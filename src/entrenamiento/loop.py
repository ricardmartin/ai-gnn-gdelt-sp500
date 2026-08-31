"""
Bucle de entrenamiento de la HGNN.

Para cada fold del walk-forward:
    - Recalcula las etiquetas del fold con umbrales derivados SOLO del train
      (anti-leakage de etiquetas, ver `src/datos/etiquetas.py`).
    - Separa el tramo final del train como VALIDACIÓN INTERNA y decide el
      early stopping únicamente con ella (anti-leakage de selección de modelo).
    - Ajusta la normalización de features SOLO con el train interno y la
      aplica congelada a train, val interna y test.
    - Evalúa el bloque de test del fold UNA única vez, con el mejor modelo
      según la val interna: clasificación + simulación financiera.
    - Reporta métricas por seed y agrega.

Implementa:
    - Cross-entropy con pesos opcionales por clase (calculados en el train interno).
    - Optimizador AdamW con weight decay.
    - Early stopping por F1 macro de la validación INTERNA.
    - Simulación de la estrategia de inversión sobre el set de test.
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
from src.datos.etiquetas import clases_para_fold
from src.datos.normalizacion import NormalizadorGrafos
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


def dividir_train_interno(
    idx_train: np.ndarray,
    fraccion_val_interna: float,
    min_val_interna: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Divide temporalmente el train de un fold en (train interno, val interna).

    La val interna es el TRAMO FINAL del train (respeta el orden temporal:
    nunca se valida con datos anteriores a los de entrenamiento). El early
    stopping se decide con ella, y el test del fold queda intacto hasta la
    evaluación final.

    Reglas de tamaño:
        - objetivo: fraccion_val_interna del train, con mínimo min_val_interna.
        - tope: nunca más de 1/3 del train (para no dejar el train esquelético).
        - degenerado (train <= 3 muestras): sin split; se avisa y la "val
          interna" es el propio train (early stopping poco fiable, pero jamás
          se toca el test).

    Returns:
        (idx_train_interno, idx_val_interna), ambos ordenados ascendentemente.
    """
    idx = np.sort(np.asarray(idx_train, dtype=int))
    n = len(idx)

    if n <= 3:
        log.warning(
            "Train con solo %d muestras: sin split interno; el early stopping "
            "usará el propio train (poco fiable).", n,
        )
        return idx, idx

    n_val = max(int(round(fraccion_val_interna * n)), int(min_val_interna))
    n_val = min(n_val, n // 3)   # tope: 1/3 del train
    n_val = max(n_val, 1)

    return idx[:-n_val], idx[-n_val:]


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


def _cargar_grafos(
    dataset,
    indices: np.ndarray,
    clases_por_indice: Optional[np.ndarray],
) -> tuple[list, np.ndarray]:
    """
    Recupera los grafos de `indices` del dataset y les fija la etiqueta.

    Si `clases_por_indice` no es None (etiquetas del fold, calculadas con
    umbrales del train), sobreescribe la etiqueta provisional que incrusta el
    dataset. Devuelve (lista_de_grafos, array_de_clases).
    """
    grafos, clases = [], []
    for i in indices:
        i = int(i)
        g, c = dataset[i]
        if clases_por_indice is not None:
            c = int(clases_por_indice[i])
            if c < 0:
                raise ValueError(
                    f"Etiqueta inválida (-1) en el índice {i}: hay un retorno "
                    f"NaN en `retornos_por_indice`. Revisa la alineación."
                )
            g["market"].y = torch.tensor([c], dtype=torch.long)
        grafos.append(g)
        clases.append(c)
    return grafos, np.asarray(clases, dtype=np.int64)


def entrenar_un_fold(
    dataset,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    seed: int = 0,
    dispositivo: str = "cpu",
    verbose: bool = True,
    retornos_val: Optional[np.ndarray] = None,
    umbral_short: float = UMBRAL_SHORT,
    retornos_por_indice: Optional[np.ndarray] = None,
    fraccion_val_interna: Optional[float] = None,
    min_val_interna: Optional[int] = None,
    normalizar: Optional[bool] = None,
) -> tuple[Metricas, dict, Optional[MetricasFinancieras], np.ndarray, np.ndarray]:
    """
    Entrena el modelo sobre un fold y lo evalúa UNA sola vez en el test.

    Protocolo (anti-leakage):
        1. Etiquetas del fold: si se pasa `retornos_por_indice`, los umbrales
           de clase se calculan SOLO con los retornos de `idx_train` y se
           aplican congelados a train y test. Si no se pasa, se usan las
           etiquetas provisionales del dataset (se emite un warning: su umbral
           se calculó con la serie completa).
        2. Split interno: el tramo final de `idx_train` se reserva como
           validación interna; el early stopping se decide solo con ella.
        3. Normalización: medias/desviaciones calculadas SOLO en el train
           interno, aplicadas congeladas a los tres conjuntos.
        4. `idx_val` (el test del fold) se evalúa una única vez, al final,
           con el mejor modelo según la val interna.

    Args:
        dataset: DatasetGrafoDiario.
        idx_train: índices de train del fold.
        idx_val: índices de test del fold (NUNCA usados para decidir nada).
        seed: semilla.
        dispositivo: 'cpu' o 'cuda'.
        verbose: imprime progreso por epoch.
        retornos_val: retornos reales del test, alineados con idx_val (solo
            para la simulación financiera). Si se pasa `retornos_por_indice`,
            este argumento se ignora y se deriva de ahí.
        umbral_short: umbral de P(baja) para activar short.
        retornos_por_indice: retornos reales de TODO el dataset (longitud
            len(dataset), mismo orden de índices). Activa las etiquetas por
            fold y la simulación. RECOMENDADO pasarlo siempre.
        fraccion_val_interna / min_val_interna: tamaño de la val interna
            (por defecto, los de config.ENTRENAMIENTO).
        normalizar: activa/desactiva la normalización (por defecto,
            config.ENTRENAMIENTO.normalizar_features).

    Returns:
        (metricas_test, historial, metricas_financieras_o_None,
         probas_test, reales_test)
    """
    if fraccion_val_interna is None:
        fraccion_val_interna = ENTRENAMIENTO.fraccion_val_interna
    if min_val_interna is None:
        min_val_interna = ENTRENAMIENTO.min_val_interna
    if normalizar is None:
        normalizar = ENTRENAMIENTO.normalizar_features

    fijar_semilla(seed)

    idx_train = np.sort(np.asarray(idx_train, dtype=int))
    idx_val = np.sort(np.asarray(idx_val, dtype=int))

    # --- 1) Etiquetas del fold (umbrales SOLO del train) ---------------------
    clases_fold: Optional[np.ndarray] = None
    if retornos_por_indice is not None:
        retornos_por_indice = np.asarray(retornos_por_indice, dtype=float)
        if len(retornos_por_indice) != len(dataset):
            raise ValueError(
                f"`retornos_por_indice` tiene longitud {len(retornos_por_indice)} "
                f"pero el dataset tiene {len(dataset)} muestras."
            )
        clases_fold, _umbrales = clases_para_fold(retornos_por_indice, idx_train)
    else:
        log.warning(
            "entrenar_un_fold sin `retornos_por_indice`: se usan las etiquetas "
            "PROVISIONALES del dataset (umbral calculado con la serie completa, "
            "leakage suave). Pasa `retornos_por_indice` para el protocolo correcto."
        )

    # --- 2) Split interno del train ------------------------------------------
    idx_tr_int, idx_val_int = dividir_train_interno(
        idx_train, fraccion_val_interna, min_val_interna,
    )
    if verbose:
        log.info(
            "  Split interno: train=%d | val_interna=%d | test=%d",
            len(idx_tr_int), len(idx_val_int), len(idx_val),
        )

    # --- Cargar grafos con la etiqueta del fold ------------------------------
    grafos_tr, y_tr = _cargar_grafos(dataset, idx_tr_int, clases_fold)
    grafos_vi, _y_vi = _cargar_grafos(dataset, idx_val_int, clases_fold)
    grafos_te, _y_te = _cargar_grafos(dataset, idx_val, clases_fold)

    # --- 3) Normalización con estadísticas SOLO del train interno ------------
    if normalizar:
        normalizador = NormalizadorGrafos().fit(grafos_tr)
        grafos_tr = normalizador.transform_lista(grafos_tr)
        grafos_vi = normalizador.transform_lista(grafos_vi)
        grafos_te = normalizador.transform_lista(grafos_te)

    loader_train = DataLoader(
        grafos_tr, batch_size=ENTRENAMIENTO.batch_size, shuffle=True,
    )
    loader_val_int = DataLoader(
        grafos_vi, batch_size=ENTRENAMIENTO.batch_size, shuffle=False,
    )
    loader_test = DataLoader(
        grafos_te, batch_size=ENTRENAMIENTO.batch_size, shuffle=False,
    )

    # --- Modelo ---------------------------------------------------------------
    modelo = HGNNGeopolitica().to(dispositivo)
    optimizador = AdamW(
        modelo.parameters(),
        lr=ENTRENAMIENTO.learning_rate,
        weight_decay=ENTRENAMIENTO.weight_decay,
    )

    if ENTRENAMIENTO.usar_pesos_clase:
        # Pesos calculados sobre lo que realmente ve la loss: el train interno.
        pesos = pesos_de_clase(y_tr).to(dispositivo)
        criterio = nn.CrossEntropyLoss(weight=pesos)
    else:
        criterio = nn.CrossEntropyLoss()

    # --- Bucle con early stopping por VAL INTERNA -----------------------------
    # El test del fold NO se mira en ningún momento de este bucle.
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

        # Validación INTERNA (nunca el test)
        _, preds_vi, reales_vi = _predecir(modelo, loader_val_int, dispositivo)
        m_vi = calcular_metricas(reales_vi, preds_vi)

        historial["train_loss"].append(train_loss)
        historial["val_f1"].append(m_vi.f1_macro)
        historial["val_acc"].append(m_vi.accuracy)

        if verbose:
            log.info(
                "  epoch %3d | train_loss=%.4f | val_int_acc=%.4f | val_int_f1=%.4f",
                epoch, train_loss, m_vi.accuracy, m_vi.f1_macro,
            )

        # Early stopping (decidido con la val interna)
        if m_vi.f1_macro > mejor_f1:
            mejor_f1 = m_vi.f1_macro
            mejor_estado = {k: v.detach().cpu().clone()
                            for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= ENTRENAMIENTO.paciencia_early_stopping:
                if verbose:
                    log.info("  Early stopping en epoch %d (val interna)", epoch)
                break

    # Restaurar el mejor estado según la val interna.
    if mejor_estado is not None:
        modelo.load_state_dict(mejor_estado)

    # --- 4) Evaluación ÚNICA sobre el test del fold ----------------------------
    probas, preds, reales = _predecir(modelo, loader_test, dispositivo)
    m_final = calcular_metricas(reales, preds)

    # Retornos del test para la simulación financiera.
    if retornos_por_indice is not None:
        retornos_test = retornos_por_indice[idx_val]
    else:
        retornos_test = retornos_val

    metricas_fin: Optional[MetricasFinancieras] = None
    if retornos_test is not None and len(retornos_test) == len(reales):
        metricas_fin = simular_estrategia(probas, retornos_test, umbral_short)

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
            mismo orden de índices que usa el dataset. RECOMENDADO pasarlo
            siempre: activa (a) las etiquetas por fold con umbral solo del
            train y (b) la simulación financiera por fold.
        umbral_short: umbral de P(baja) para activar short.

    Returns:
        ResultadoExperimento con métricas de clasificación + financieras.
    """
    if retornos_por_indice is None:
        log.warning(
            "entrenar_walkforward sin `retornos_por_indice`: sin simulación "
            "financiera y con etiquetas provisionales (leakage suave de sigma)."
        )

    resultado = ResultadoExperimento()

    for fold in folds:
        log.info("=" * 70)
        log.info("FOLD %d  (train n=%d, test n=%d)",
                 fold.fold_id, len(fold.idx_train), len(fold.idx_val))
        log.info("=" * 70)

        retornos_val_fold = None
        if retornos_por_indice is not None:
            retornos_val_fold = np.asarray(retornos_por_indice, dtype=float)[fold.idx_val]
        if hasattr(dataset, "etiquetas") and "fecha_target" in dataset.etiquetas:
            fechas_val_fold = dataset.etiquetas.iloc[fold.idx_val]["fecha_target"].values
        else:
            # Fallback auditable para datasets sintéticos sin tabla de fechas.
            fechas_val_fold = np.asarray(fold.idx_val)

        for seed in semillas:
            log.info("--- Semilla %d ---", seed)
            m, _hist, mf, probas_sf, reales_sf = entrenar_un_fold(
                dataset, fold.idx_train, fold.idx_val,
                seed=seed, dispositivo=dispositivo, verbose=False,
                umbral_short=umbral_short,
                retornos_por_indice=retornos_por_indice,
            )
            log.info("  Clasificación: %s", m.resumen())
            if mf is not None:
                log.info("  Financiero:    %s", mf.resumen())
            resultado.agregar(m, mf, fold_id=fold.fold_id, seed=seed)
            resultado.agregar_oos(
                fold_id=fold.fold_id,
                seed=seed,
                indices=fold.idx_val,
                fechas=fechas_val_fold,
                probabilidades=probas_sf,
                reales=reales_sf,
                retornos=retornos_val_fold,
            )

    log.info("=" * 70)
    log.info("RESUMEN GLOBAL: %s", resultado.resumen_final())
    log.info("=" * 70)
    return resultado
