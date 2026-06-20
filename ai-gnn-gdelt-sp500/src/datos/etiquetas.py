"""
Cálculo de la etiqueta triclase del S&P 500 y alineación temporal con grafos GDELT.

Etiqueta: para predecir el día de mercado `t+1`, se calcula el retorno
close-to-close del SP500 entre los días t y t+1 y se discretiza en tres clases
{baja=0, neutro=1, sube=2} según el umbral definido en `config.py`.

Alineación temporal (anti-leakage): la información geopolítica usada para
predecir el día t+1 debe limitarse a los eventos GDELT publicados ANTES del
cierre del mercado del día t. Eventos posteriores se asignan al siguiente día.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logging import obtener_logger
from config import (
    MODO_ETIQUETA, UMBRAL_NEUTRO, UMBRAL_SIGMA, HORA_CIERRE_NY_UTC,
)

log = obtener_logger(__name__)


CLASE_BAJA = 0
CLASE_NEUTRO = 1
CLASE_SUBE = 2


def calcular_retornos(precios_sp500: pd.DataFrame) -> pd.Series:
    """
    Calcula el retorno close-to-close diario del S&P 500.

    Args:
        precios_sp500: DataFrame con índice de fechas y columna 'Close'.

    Returns:
        Serie de retornos diarios (NaN para el primer día).
    """
    if "Close" not in precios_sp500.columns:
        raise ValueError("Se esperaba columna 'Close' en los precios del SP500")
    close = precios_sp500["Close"].astype(float)
    return close.pct_change().rename("retorno")


def discretizar_retornos(
    retornos: pd.Series,
    modo: str = MODO_ETIQUETA,
    umbral_fijo: float = UMBRAL_NEUTRO,
    umbral_sigma: float = UMBRAL_SIGMA,
) -> pd.Series:
    """
    Discretiza retornos continuos en {baja=0, neutro=1, sube=2}.

    Modos soportados:
        "fijo"     -> umbral simétrico ±umbral_fijo
        "sigma"    -> umbral simétrico ±umbral_sigma * std(retornos)
        "terciles" -> percentiles 33 y 66 (clases balanceadas por construcción)
    """
    r = retornos.dropna()

    if modo == "fijo":
        u = umbral_fijo
        log.info("Discretización fija: umbral ±%.4f", u)
        return _aplicar_umbral_simetrico(retornos, u)

    if modo == "sigma":
        sigma = float(r.std())
        u = umbral_sigma * sigma
        log.info("Discretización por sigma: σ=%.4f, umbral ±%.4f", sigma, u)
        return _aplicar_umbral_simetrico(retornos, u)

    if modo == "terciles":
        q33, q66 = np.quantile(r.values, [1/3, 2/3])
        log.info("Discretización por terciles: q33=%.4f, q66=%.4f", q33, q66)
        clases = pd.Series(CLASE_NEUTRO, index=retornos.index, dtype="int64")
        clases[retornos < q33] = CLASE_BAJA
        clases[retornos > q66] = CLASE_SUBE
        clases[retornos.isna()] = -1  # marca para descartar luego
        return clases

    raise ValueError(f"Modo de etiqueta desconocido: {modo}")


def _aplicar_umbral_simetrico(retornos: pd.Series, umbral: float) -> pd.Series:
    """Aplicar un umbral simétrico para clasificar en {0, 1, 2}."""
    clases = pd.Series(CLASE_NEUTRO, index=retornos.index, dtype="int64")
    clases[retornos < -umbral] = CLASE_BAJA
    clases[retornos > umbral] = CLASE_SUBE
    clases[retornos.isna()] = -1
    return clases


def construir_etiquetas_diarias(precios_sp500: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el DataFrame de etiquetas usado durante el entrenamiento.

    Cada fila representa una sesión de mercado t+1 con su etiqueta. La columna
    `fecha_grafo` indica qué día se debe usar para construir el grafo predictor
    (= sesión anterior, antes del cierre).

    Devuelve:
        DataFrame con columnas
            fecha_grafo (date)       -> qué grafo se construye
            fecha_target (date)      -> qué sesión se predice (siguiente día hábil)
            retorno (float)          -> retorno close-to-close
            clase (int)              -> 0=baja, 1=neutro, 2=sube
    """
    retornos = calcular_retornos(precios_sp500)
    clases = discretizar_retornos(retornos)

    df = pd.DataFrame({
        "fecha_target": retornos.index,
        "retorno": retornos.values,
        "clase": clases.values,
    })
    # El grafo predictor es el del día hábil ANTERIOR a la sesión predicha.
    # En la práctica, "día anterior" se calcula con shift (1 sesión bursátil).
    df["fecha_grafo"] = df["fecha_target"].shift(1)

    # Descartar filas sin grafo previo (primera) y sin retorno (NaN inicial).
    df = df.dropna(subset=["fecha_grafo", "retorno"])
    df = df[df["clase"] != -1].reset_index(drop=True)

    # Convertir a fechas (sin hora) para alinear con los días GDELT.
    df["fecha_target"] = pd.to_datetime(df["fecha_target"]).dt.normalize()
    df["fecha_grafo"] = pd.to_datetime(df["fecha_grafo"]).dt.normalize()
    df["clase"] = df["clase"].astype("int64")

    log.info("Etiquetas construidas: %d sesiones", len(df))
    log.info("Distribución de clases:\n%s", df["clase"].value_counts().sort_index())
    return df


def aplicar_corte_horario(df_eventos: pd.DataFrame) -> pd.DataFrame:
    """
    Asigna cada evento GDELT al día de mercado al que pertenece según el corte
    horario definido en `config.HORA_CIERRE_NY_UTC`.

    Eventos con DATEADDED posterior al cierre se asignan al día siguiente
    (los usará el grafo predictor de la sesión t+2, no la t+1).

    Args:
        df_eventos: DataFrame con columnas SQLDATE y DATEADDED.

    Returns:
        Mismo DataFrame con columna `fecha_grafo` que indica a qué día
        contribuye cada evento.
    """
    df = df_eventos.copy()
    # DATEADDED tiene formato YYYYMMDDHHMMSS en GDELT 1.0 desde 2013.
    # Antes de 2013 sólo hay YYYYMMDD, en cuyo caso el corte no es aplicable
    # y se usa SQLDATE directamente.
    ts_added = pd.to_datetime(df["DATEADDED"], format="%Y%m%d%H%M%S", errors="coerce")
    ts_added = ts_added.fillna(
        pd.to_datetime(df["DATEADDED"], format="%Y%m%d", errors="coerce")
    )

    fecha_dia = ts_added.dt.normalize()
    hora = ts_added.dt.hour
    # Si la hora >= corte, el evento se asigna al día siguiente.
    desplaza = (hora >= HORA_CIERRE_NY_UTC).astype("int64")
    df["fecha_grafo"] = fecha_dia + pd.to_timedelta(desplaza, unit="D")
    return df
