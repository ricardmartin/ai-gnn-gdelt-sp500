"""
Bucle de entrenamiento de la HGNN.

Para cada fold del walk-forward:
    - Entrena el modelo sobre el train del fold.
    - Lo evalúa sobre el val: clasificación + simulación financiera.
    - Reporta métricas por seed y agrega.

Implementa:
    - Cross-entropy con pesos opcionales por clase.
    - Optimizador AdamW con weight decay.
    - Early stopping por F1 macro de validación.
    - Simulación de la estrategia de inversión sobre el set de validación.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch_geometric.loader import DataLoader

from src.modelo.arquitectura import HGNNGeopolitica
from src.entrenamiento.evaluacion import (
    Metricas, MetricasFinancieras,
    calcular_metricas, simular_estrategia,
    ResultadoExperimento,
)
from src.utils.logging import obtener_logger
from config import ENTRENAMIENTO, MODELO, UMBRAL_SHORT

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
    """Pesos de clase inversos a la frecuencia (para CE ponderada)."""
    counts = np.bincount(y_train, minlength=num_clases).astype(np.float32)
    counts = np.where(counts > 0, counts, 1.0)
    pesos = counts.sum() / (num_clases * counts)
    return torch.tensor(pesos, dtype=torch.float32)


def _predecir(
    modelo: HGNNGeopolitica,
    loader,
    dispositivo: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Pasa el loader entero por el modelo y devuelve (probas, preds, reales).

    - probas: shape (n, 3) con las probabilidades softmax por clase.
    - preds:  shape (n,)  con la clase argmax.
    - reales: shape (n,)  con la etiqueta verdadera.
    """
    modelo.eval()
    probas_list, preds_list, reales_list = [], [], []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(dispositivo)
            logits = modelo(batch)
            probas = F.softmax(logits, dim=-1).cpu().numpy()
            preds = logits.argmax(dim=-1).cpu().numpy()
            reales = batch["market"].y.cpu().numpy()
            probas_list.append(probas)
            preds_list.append(preds)
            reales_list.append(reales)

    if not preds_list:
        return (
            np.empty((0, 3), dtype=np.float32),
            np.array([], dtype=np.int64),
            np.array([], dtype=np.int64),
        )
    return (
        np.concatenate(probas_list, axis=0),
        np.concatenate(preds_list, axis=0),
        np.concatenate(reales_list, axis=0),
    )


def entrenar_un_fold(
    dataset,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    seed: int = 0,
    dispositivo: str = "cpu",
    verbose: bool = True,
    retornos_val: Optional[np.ndarray] = None,
    umbral_short: float = UMBRAL_SHORT,
) -> tuple[Metricas, dict, Optional[MetricasFinancieras]]:
    """
    Entrena el modelo sobre un fold y evalúa en validación.

    Args:
        dataset: DatasetGrafoDiario.
        idx_train: índices de train.
        idx_val: índices de validación.
        seed: semilla.
        dispositivo: 'cpu' o 'cuda'.
        verbose: imprime progreso por epoch.
        retornos_val: array de retornos reales (close-to-close) del set de
            validación, alineado con idx_val. Si se proporciona, se ejecuta
            la simulación financiera.
        umbral_short: umbral de P(baja) para activar short.

    Returns:
        (metricas_clasificacion, historial, metricas_financieras_o_None).
    """
    fijar_semilla(seed)

    # --- Construir subdatasets ----------------------------------------------
    grafos_train, y_train = [], []
    for i in idx_train:
        g, c = dataset[int(i)]
        grafos_train.append(g)
        y_train.append(c)
    y_train_arr = np.asarray(y_train, dtype=np.int64)

    grafos_val = []
    for i in idx_val:
        g, _ = dataset[int(i)]
        grafos_val.append(g)

    loader_train = DataLoader(
        grafos_train, batch_size=ENTRENAMIENTO.batch_size, shuffle=True,
    )
    loader_val = DataLoader(
        grafos_val, batch_size=ENTRENAMIENTO.batch_size, shuffle=False,
    )

    # --- Modelo --------------------------------------------------------------
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

    # --- Bucle con early stopping -------------------------------------------
    historial = {"train_loss": [], "val_f1": [], "val_acc": []}
    mejor_f1 = -np.inf
    epochs_sin_mejora = 0
    mejor_estado: Optional[dict] = None

    for epoch in range(ENTRENAMIENTO.epochs_max):
        # Train
        modelo.train()
        loss_acc, n_batches = 0.0, 0
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

        # Val
        _, preds, reales = _predecir(modelo, loader_val, dispositivo)
        m = calcular_metricas(reales, preds)

        historial["train_loss"].append(train_loss)
        historial["val_f1"].append(m.f1_macro)
        historial["val_acc"].append(m.accuracy)

        if verbose:
            log.info(
                "  epoch %3d | train_loss=%.4f | val_acc=%.4f | val_f1=%.4f",
                epoch, train_loss, m.accuracy, m.f1_macro,
            )

        # Early stopping
        if m.f1_macro > mejor_f1:
            mejor_f1 = m.f1_macro
            mejor_estado = {k: v.detach().cpu().clone()
                            for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= ENTRENAMIENTO.paciencia_early_stopping:
                log.info("  Early stopping en epoch %d", epoch)
                break

    # Restaurar el mejor estado y evaluación final.
    if mejor_estado is not None:
        modelo.load_state_dict(mejor_estado)

    probas, preds, reales = _predecir(modelo, loader_val, dispositivo)
    m_final = calcular_metricas(reales, preds)

    # Simulación financiera si tenemos retornos reales.
    metricas_fin: Optional[MetricasFinancieras] = None
    if retornos_val is not None and len(retornos_val) == len(reales):
        metricas_fin = simular_estrategia(probas, retornos_val, umbral_short)

    return m_final, historial, metricas_fin, probas, reales


def entrenar_walkforward(
    dataset,
    folds,
    semillas=ENTRENAMIENTO.semillas,
    dispositivo: str = "cpu",
    retornos_por_indice: Optional[np.ndarray] = None,
    umbral_short: float = UMBRAL_SHORT,
) -> ResultadoExperimento:
    """
    Walk-forward completo con multi-seed y simulación financiera.

    Args:
        dataset: DatasetGrafoDiario.
        folds: lista de FoldTemporal.
        semillas: semillas a usar.
        dispositivo: 'cpu' o 'cuda'.
        retornos_por_indice: array de longitud len(dataset) con el retorno
            real (close-to-close) asociado a cada muestra del dataset, en el
            mismo orden de índices que usa el dataset. Si se pasa, se ejecuta
            la simulación financiera por fold.
        umbral_short: umbral de P(baja) para activar short.

    Returns:
        ResultadoExperimento con métricas de clasificación + financieras.
    """
    resultado = ResultadoExperimento()

    for fold in folds:
        log.info("=" * 70)
        log.info("FOLD %d  (train n=%d, val n=%d)",
                 fold.fold_id, len(fold.idx_train), len(fold.idx_val))
        log.info("=" * 70)

        retornos_val_fold = None
        if retornos_por_indice is not None:
            retornos_val_fold = retornos_por_indice[fold.idx_val]

        for seed in semillas:
            log.info("--- Semilla %d ---", seed)
            m, _hist, mf, probas_sf, reales_sf = entrenar_un_fold(
                dataset, fold.idx_train, fold.idx_val,
                seed=seed, dispositivo=dispositivo, verbose=False,
                retornos_val=retornos_val_fold,
                umbral_short=umbral_short,
            )
            log.info("  Clasificación: %s", m.resumen())
            if mf is not None:
                log.info("  Financiero:    %s", mf.resumen())
            resultado.agregar(m, mf)
            # Crudos para análisis posterior (por fold y semilla)
            if not hasattr(resultado, "probas_crudas"):
                resultado.probas_crudas = []
                resultado.reales_crudas = []
                resultado.retornos_crudos = []
            resultado.probas_crudas.append(probas_sf)
            resultado.reales_crudas.append(reales_sf)
            resultado.retornos_crudos.append(
                retornos_val_fold if retornos_val_fold is not None else None
            )

    log.info("=" * 70)
    log.info("RESUMEN GLOBAL: %s", resultado.resumen_final())
    log.info("=" * 70)
    return resultado
