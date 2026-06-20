"""
Bucle de entrenamiento de la HGNN.

Para cada fold del walk-forward, entrena el modelo sobre el train del fold y
lo evalúa sobre el val. Soporta multi-seed para reportar varianza.

Implementa:
    - Cross-entropy con pesos opcionales por clase.
    - Optimizador AdamW con weight decay.
    - Early stopping por F1 macro de validación.
    - Checkpointing del mejor modelo de cada fold.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch_geometric.loader import DataLoader

from src.modelo.arquitectura import HGNNGeopolitica
from src.entrenamiento.evaluacion import (
    Metricas, calcular_metricas, ResultadoExperimento,
)
from src.utils.logging import obtener_logger
from config import ENTRENAMIENTO, MODELO, DIR_CHECKPOINTS

log = obtener_logger(__name__)


def fijar_semilla(seed: int) -> None:
    """Fija las semillas de Python, NumPy y PyTorch para reproducibilidad."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def pesos_de_clase(y_train: np.ndarray, num_clases: int = 3) -> torch.Tensor:
    """
    Calcula pesos de clase inversamente proporcionales a la frecuencia.

    Útil para evitar que el modelo se sesgue hacia la clase mayoritaria.
    """
    counts = np.bincount(y_train, minlength=num_clases).astype(np.float32)
    counts = np.where(counts > 0, counts, 1.0)
    pesos = counts.sum() / (num_clases * counts)
    return torch.tensor(pesos, dtype=torch.float32)


def entrenar_un_fold(
    dataset,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    seed: int = 0,
    dispositivo: str = "cpu",
    verbose: bool = True,
) -> tuple[Metricas, dict]:
    """
    Entrena el modelo sobre un fold y devuelve las métricas finales en val.

    Args:
        dataset: instancia de DatasetGrafoDiario.
        idx_train: índices de muestras de train dentro del dataset.
        idx_val: índices de muestras de validación.
        seed: semilla aleatoria.
        dispositivo: 'cpu' o 'cuda'.
        verbose: si True, imprime progreso por epoch.

    Returns:
        Tupla (metricas_val, historial) donde historial es un dict con
        las curvas de pérdida y métrica por epoch.
    """
    fijar_semilla(seed)

    # --- Construir subdatasets de train y val ----------------------------------
    grafos_train = []
    y_train = []
    for i in idx_train:
        g, c = dataset[int(i)]
        grafos_train.append(g)
        y_train.append(c)
    y_train_arr = np.asarray(y_train, dtype=np.int64)

    grafos_val = []
    y_val = []
    for i in idx_val:
        g, c = dataset[int(i)]
        grafos_val.append(g)
        y_val.append(c)
    y_val_arr = np.asarray(y_val, dtype=np.int64)

    # --- DataLoaders ----------------------------------------------------------
    loader_train = DataLoader(
        grafos_train, batch_size=ENTRENAMIENTO.batch_size, shuffle=True,
    )
    loader_val = DataLoader(
        grafos_val, batch_size=ENTRENAMIENTO.batch_size, shuffle=False,
    )

    # --- Modelo ----------------------------------------------------------------
    modelo = HGNNGeopolitica().to(dispositivo)
    optimizador = AdamW(
        modelo.parameters(),
        lr=ENTRENAMIENTO.learning_rate,
        weight_decay=ENTRENAMIENTO.weight_decay,
    )

    if ENTRENAMIENTO.usar_pesos_clase:
        pesos = pesos_de_clase(y_train_arr).to(dispositivo)
        criterio = nn.CrossEntropyLoss(weight=pesos)
    else:
        criterio = nn.CrossEntropyLoss()

    # --- Bucle con early stopping ---------------------------------------------
    historial = {"train_loss": [], "val_f1": [], "val_acc": []}
    mejor_f1 = -np.inf
    epochs_sin_mejora = 0
    mejor_estado: Optional[dict] = None

    for epoch in range(ENTRENAMIENTO.epochs_max):
        # ---- Train ----
        modelo.train()
        loss_acc = 0.0
        n_batches = 0
        for batch in loader_train:
            batch = batch.to(dispositivo)
            optimizador.zero_grad()
            logits = modelo(batch)
            y = batch["market"].y
            perdida = criterio(logits, y)
            perdida.backward()
            optimizador.step()
            loss_acc += float(perdida.item())
            n_batches += 1
        train_loss = loss_acc / max(1, n_batches)

        # ---- Val ----
        modelo.eval()
        preds, reales = [], []
        with torch.no_grad():
            for batch in loader_val:
                batch = batch.to(dispositivo)
                logits = modelo(batch)
                p = logits.argmax(dim=-1).cpu().numpy()
                preds.append(p)
                reales.append(batch["market"].y.cpu().numpy())
        preds = np.concatenate(preds) if preds else np.array([], dtype=np.int64)
        reales = np.concatenate(reales) if reales else np.array([], dtype=np.int64)
        m = calcular_metricas(reales, preds)

        historial["train_loss"].append(train_loss)
        historial["val_f1"].append(m.f1_macro)
        historial["val_acc"].append(m.accuracy)

        if verbose:
            log.info(
                "  epoch %3d | train_loss=%.4f | val_acc=%.4f | val_f1=%.4f",
                epoch, train_loss, m.accuracy, m.f1_macro,
            )

        # ---- Early stopping ----
        if m.f1_macro > mejor_f1:
            mejor_f1 = m.f1_macro
            mejor_estado = {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= ENTRENAMIENTO.paciencia_early_stopping:
                log.info("  Early stopping en epoch %d (sin mejora desde %d epochs)",
                         epoch, ENTRENAMIENTO.paciencia_early_stopping)
                break

    # Restaurar el mejor estado y evaluar una vez más.
    if mejor_estado is not None:
        modelo.load_state_dict(mejor_estado)
    modelo.eval()
    preds, reales = [], []
    with torch.no_grad():
        for batch in loader_val:
            batch = batch.to(dispositivo)
            logits = modelo(batch)
            preds.append(logits.argmax(dim=-1).cpu().numpy())
            reales.append(batch["market"].y.cpu().numpy())
    preds = np.concatenate(preds) if preds else np.array([], dtype=np.int64)
    reales = np.concatenate(reales) if reales else np.array([], dtype=np.int64)
    m_final = calcular_metricas(reales, preds)

    return m_final, historial


def entrenar_walkforward(
    dataset,
    folds,
    semillas=ENTRENAMIENTO.semillas,
    dispositivo: str = "cpu",
) -> ResultadoExperimento:
    """
    Ejecuta el entrenamiento walk-forward completo, con multi-seed.

    Args:
        dataset: DatasetGrafoDiario.
        folds: lista de FoldTemporal devuelta por construir_folds().
        semillas: iterable de semillas a usar.
        dispositivo: 'cpu' o 'cuda'.

    Returns:
        ResultadoExperimento con las métricas de cada (fold, semilla).
    """
    resultado = ResultadoExperimento()

    for fold in folds:
        log.info("=" * 70)
        log.info("FOLD %d  (train n=%d, val n=%d)",
                 fold.fold_id, len(fold.idx_train), len(fold.idx_val))
        log.info("=" * 70)

        for seed in semillas:
            log.info("--- Semilla %d ---", seed)
            m, _hist = entrenar_un_fold(
                dataset, fold.idx_train, fold.idx_val,
                seed=seed, dispositivo=dispositivo, verbose=False,
            )
            log.info("  Resultado: %s", m.resumen())
            resultado.agregar(m)

    log.info("=" * 70)
    log.info("RESUMEN GLOBAL: %s", resultado.resumen_final())
    log.info("=" * 70)
    return resultado
