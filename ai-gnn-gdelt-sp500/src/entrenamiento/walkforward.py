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
    train_inicial_dias: int = WALK_FORWARD.train_inicial_dias,
    validacion_dias: int = WALK_FORWARD.validacion_dias,
) -> list[FoldTemporal]:
    """
    Construye los folds del walk-forward.

    Args:
        fechas: serie de fechas ordenadas (una por muestra del dataset).
        num_folds: número de folds.
        modo: "expansiva" o "deslizante".
        train_inicial_dias: tamaño mínimo (días) del primer set de train.
        validacion_dias: tamaño (días) del set de validación de cada fold.

    Returns:
        Lista de FoldTemporal.
    """
    fechas = pd.to_datetime(fechas).reset_index(drop=True)
    fecha_min = fechas.iloc[0]
    fecha_max = fechas.iloc[-1]

    log.info(
        "Walk-forward: %d folds, modo=%s, train inicial=%dd, val=%dd, rango=%s a %s",
        num_folds, modo, train_inicial_dias, validacion_dias,
        fecha_min.date(), fecha_max.date(),
    )

    folds: list[FoldTemporal] = []
    inicio_train = fecha_min
    fin_train = fecha_min + pd.Timedelta(days=train_inicial_dias)

    for k in range(num_folds):
        inicio_val = fin_train
        fin_val = inicio_val + pd.Timedelta(days=validacion_dias)
        if fin_val > fecha_max:
            log.warning("Fold %d cortado: validación excede rango disponible", k)
            break

        idx_train = fechas[(fechas >= inicio_train) & (fechas < fin_train)].index.values
        idx_val = fechas[(fechas >= inicio_val) & (fechas < fin_val)].index.values

        if len(idx_train) == 0 or len(idx_val) == 0:
            log.warning("Fold %d vacío, se omite", k)
            continue

        folds.append(FoldTemporal(
            fold_id=k,
            idx_train=idx_train,
            idx_val=idx_val,
            fecha_train_inicio=inicio_train,
            fecha_train_fin=fin_train,
            fecha_val_inicio=inicio_val,
            fecha_val_fin=fin_val,
        ))

        log.info(
            "  Fold %d: train [%s, %s) n=%d | val [%s, %s) n=%d",
            k, inicio_train.date(), fin_train.date(), len(idx_train),
            inicio_val.date(), fin_val.date(), len(idx_val),
        )

        # Avanzar la ventana.
        if modo == "expansiva":
            fin_train = fin_val      # el train crece
        elif modo == "deslizante":
            inicio_train = inicio_train + pd.Timedelta(days=validacion_dias)
            fin_train = fin_val
        else:
            raise ValueError(f"Modo desconocido: {modo}")

    return folds
