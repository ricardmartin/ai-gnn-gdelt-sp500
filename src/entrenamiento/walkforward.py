"""
Particiones temporales tipo walk-forward.

A diferencia de un k-fold estándar, el walk-forward respeta el orden temporal
de las muestras: entrena con un periodo inicial, valida con el periodo
inmediatamente posterior, y desliza la ventana hacia adelante.

Dos modos:
    "expansiva"  -> el conjunto de train crece en cada fold
    "deslizante" -> ventana de train de tamaño fijo
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.logging import obtener_logger
from config import WALK_FORWARD

log = obtener_logger(__name__)


@dataclass
class FoldTemporal:
    """Una partición temporal: índices de train y de validación."""
    fold_id: int
    idx_train: np.ndarray
    idx_val: np.ndarray
    fecha_train_inicio: pd.Timestamp
    fecha_train_fin: pd.Timestamp
    fecha_val_inicio: pd.Timestamp
    fecha_val_fin: pd.Timestamp


def construir_folds(
    fechas: pd.Series,
    num_folds: int = WALK_FORWARD.num_folds,
    modo: str = WALK_FORWARD.modo,
    tam_val_muestras: int | None = WALK_FORWARD.tam_val_muestras,
    train_inicial_muestras: int | None = WALK_FORWARD.train_inicial_muestras,
    embargo: int = WALK_FORWARD.embargo,
) -> list[FoldTemporal]:
    """
    Construye los folds del walk-forward, midiendo las ventanas en MUESTRAS
    (sesiones bursátiles), no en días de calendario.

    Cada muestra del dataset es un día de mercado alineado con GDELT, por lo que
    medir en muestras da folds parejos y, sobre todo, permite cubrir todo el
    rango disponible en lugar de confinar el experimento a una franja inicial.

    Si `tam_val_muestras` (y/o `train_inicial_muestras`) es None, el rango se
    parte en (num_folds + 1) bloques iguales: el primero es el train inicial y
    los `num_folds` restantes son las validaciones, que así cubren toda la cola
    del periodo (esquema equivalente a TimeSeriesSplit expansivo).

    Args:
        fechas: serie de fechas ORDENADA ascendente (una por muestra del dataset).
        num_folds: número de folds (bloques de validación).
        modo: "expansiva" (el train crece) o "deslizante" (train de tamaño fijo).
        tam_val_muestras: muestras por bloque de validación. None -> se deriva.
        train_inicial_muestras: muestras del primer train. None -> se deriva.
        embargo: hueco en muestras entre el fin del train y el inicio del val,
            para evitar leakage temporal en el borde. 0 = sin hueco.

    Returns:
        Lista de FoldTemporal.
    """
    fechas = pd.to_datetime(fechas).reset_index(drop=True)
    n = len(fechas)

    # Derivar tamaños si no se han fijado: (num_folds + 1) bloques iguales.
    if tam_val_muestras is None:
        bloque = n // (num_folds + 1)
        tam_val_muestras = bloque
        if train_inicial_muestras is None:
            train_inicial_muestras = bloque
    if train_inicial_muestras is None:
        train_inicial_muestras = n - num_folds * tam_val_muestras

    if tam_val_muestras <= 0 or train_inicial_muestras <= 0:
        raise ValueError(
            f"Tamaños inválidos: N={n}, train_inicial={train_inicial_muestras}, "
            f"val={tam_val_muestras}. ¿Demasiados folds para tan pocas muestras?"
        )

    log.info(
        "Walk-forward: %d folds, modo=%s, train inicial=%d muestras, "
        "val=%d muestras, embargo=%d, N=%d, rango=%s a %s",
        num_folds, modo, train_inicial_muestras, tam_val_muestras, embargo, n,
        fechas.iloc[0].date(), fechas.iloc[-1].date(),
    )

    folds: list[FoldTemporal] = []
    inicio_train = 0
    fin_train = train_inicial_muestras

    for k in range(num_folds):
        inicio_val = fin_train + embargo
        fin_val = inicio_val + tam_val_muestras
        if fin_val > n:
            log.warning("Fold %d cortado: validación excede las %d muestras", k, n)
            break

        idx_train = np.arange(inicio_train, fin_train)
        idx_val = np.arange(inicio_val, fin_val)

        if len(idx_train) == 0 or len(idx_val) == 0:
            log.warning("Fold %d vacío, se omite", k)
            continue

        folds.append(FoldTemporal(
            fold_id=k,
            idx_train=idx_train,
            idx_val=idx_val,
            fecha_train_inicio=fechas.iloc[inicio_train],
            fecha_train_fin=fechas.iloc[fin_train - 1],
            fecha_val_inicio=fechas.iloc[inicio_val],
            fecha_val_fin=fechas.iloc[fin_val - 1],
        ))

        log.info(
            "  Fold %d: train [%s, %s] n=%d | val [%s, %s] n=%d",
            k, fechas.iloc[inicio_train].date(), fechas.iloc[fin_train - 1].date(),
            len(idx_train),
            fechas.iloc[inicio_val].date(), fechas.iloc[fin_val - 1].date(),
            len(idx_val),
        )

        # Avanzar la ventana.
        if modo == "expansiva":
            fin_train = fin_val          # el train crece
        elif modo == "deslizante":
            inicio_train = inicio_train + tam_val_muestras
            fin_train = fin_val
        else:
            raise ValueError(f"Modo desconocido: {modo}")

    return folds
