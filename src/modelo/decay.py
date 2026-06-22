"""
Decay temporal tipo Hawkes para las aristas país-país.

Para cada par ordenado (origen, destino), el peso de la arista en el día t se
calcula como suma de las contribuciones de todos los eventos pasados entre ese
par, decayendo exponencialmente con la distancia temporal:

    w(t) = Σ_i α_i · exp(-λ · (t - t_i))

donde:
    α_i  = intensidad del evento i (función de Goldstein y NumMentions)
    λ    = tasa de decaimiento (hiperparámetro)
    t_i  = día del evento i
    t    = día actual

Conceptualmente, el grafo es ÚNICO y persistente; el resultado por día es solo
una "fotografía" del estado de sus aristas. Operativamente, para cada día se
recalculan los pesos a partir del histórico de eventos en una ventana finita.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import numpy as np
import pandas as pd

from src.utils.logging import obtener_logger
from config import LAMBDA_DECAY, VENTANA_DECAY_DIAS, LAMBDA_MULTIPLICADORES_QUADCLASS

log = obtener_logger(__name__)


def lambda_para_quadclass(quadclass: str, lambda_base: float = LAMBDA_DECAY) -> float:
    """
    Devuelve la tasa de decaimiento λ ajustada para un tipo de evento concreto.

    Los eventos de conflicto material (guerras, ataques) tienen memoria mas
    larga (λ menor) que los de cooperacion verbal (declaraciones), que el
    mercado descuenta rapidamente.

    Args:
        quadclass: codigo QuadClass CAMEO como string ("1", "2", "3" o "4").
        lambda_base: tasa base desde config.py.

    Returns:
        λ efectivo para ese tipo de evento.
    """
    multiplicador = LAMBDA_MULTIPLICADORES_QUADCLASS.get(str(quadclass), 1.0)
    return lambda_base * multiplicador


def calcular_alpha(goldstein_abs: np.ndarray, num_mentions: np.ndarray) -> np.ndarray:
    """
    Calcula la intensidad α_i de un evento a partir de sus atributos brutos.

    Heurística:
        α = |Goldstein| · log(1 + NumMentions)

    Esto da más peso a eventos extremos (positivos o negativos en Goldstein)
    con buena cobertura mediática. La forma exacta es un hiperparámetro y
    puede ajustarse.

    Args:
        goldstein_abs: valores absolutos de GoldsteinScale, shape (N,).
        num_mentions: número de menciones, shape (N,).

    Returns:
        Array de intensidades, shape (N,).
    """
    return goldstein_abs * np.log1p(num_mentions)


def aplicar_decay(
    eventos_agregados: pd.DataFrame,
    fecha_corte: pd.Timestamp,
    lambda_decay: float = LAMBDA_DECAY,
    ventana_dias: int = VENTANA_DECAY_DIAS,
) -> pd.DataFrame:
    """
    Calcula los pesos efectivos de cada arista país-país en `fecha_corte`,
    aplicando decay exponencial sobre todos los eventos pasados dentro de la
    ventana temporal.

    Args:
        eventos_agregados: DataFrame con columnas
            [fecha, pais_origen, pais_destino, quadclass,
             n_eventos, goldstein_medio, tono_medio, num_mentions_total]
            tal y como devuelve `agregar_eventos_por_dia_y_par`.
        fecha_corte: día t para el que se computa el grafo. Solo se usan
            eventos con fecha <= fecha_corte.
        lambda_decay: tasa de decaimiento λ.
        ventana_dias: ventana máxima de eventos pasados a considerar.

    Returns:
        DataFrame con una fila por arista activa, columnas:
            pais_origen, pais_destino, quadclass,
            peso_decay, intensidad_acumulada, tono_ponderado, n_eventos
    """
    if eventos_agregados.empty:
        return pd.DataFrame(
            columns=[
                "pais_origen", "pais_destino", "quadclass",
                "peso_decay", "intensidad_acumulada",
                "tono_ponderado", "n_eventos",
            ]
        )

    fecha_corte = pd.Timestamp(fecha_corte).normalize()
    fecha_min = fecha_corte - pd.Timedelta(days=ventana_dias)

    # Filtrar a la ventana relevante.
    df = eventos_agregados[
        (eventos_agregados["fecha"] <= fecha_corte) &
        (eventos_agregados["fecha"] >= fecha_min)
    ].copy()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "pais_origen", "pais_destino", "quadclass",
                "peso_decay", "intensidad_acumulada",
                "tono_ponderado", "n_eventos",
            ]
        )

    # Distancia en días desde cada evento al día actual.
    dt = (fecha_corte - df["fecha"]).dt.days.astype(float).values

    # Lambda diferenciado por QuadClass: conflicto material decae mas lento
    # (memoria mas larga) que cooperacion verbal (memoria mas corta).
    lambdas = np.array([
        lambda_para_quadclass(str(q), lambda_decay)
        for q in df["quadclass"].values
    ])
    decay_factor = np.exp(-lambdas * dt)

    # Intensidad de cada evento agregado.
    alpha = calcular_alpha(
        np.abs(df["goldstein_medio"].values),
        df["num_mentions_total"].values,
    )

    df["contribucion_peso"] = alpha * decay_factor
    df["contribucion_tono"] = df["tono_medio"].values * decay_factor
    df["decay_factor"] = decay_factor

    # Agregar por arista (origen, destino, tipo).
    agregado = df.groupby(
        ["pais_origen", "pais_destino", "quadclass"],
        observed=True,
    ).agg(
        peso_decay=("contribucion_peso", "sum"),
        intensidad_acumulada=("contribucion_peso", "sum"),
        tono_ponderado=("contribucion_tono", "sum"),
        suma_decay_factors=("decay_factor", "sum"),
        n_eventos=("n_eventos", "sum"),
    ).reset_index()

    # Normalizar tono ponderado dividiendo por la suma de factores de decay.
    agregado["tono_ponderado"] = (
        agregado["tono_ponderado"] / agregado["suma_decay_factors"].clip(lower=1e-9)
    )
    agregado = agregado.drop(columns=["suma_decay_factors"])

    return agregado


def vida_media_a_lambda(vida_media_dias: float) -> float:
    """Conversión auxiliar: vida media (días) -> λ."""
    return float(np.log(2.0) / vida_media_dias)


def lambda_a_vida_media(lambda_decay: float) -> float:
    """Conversión auxiliar: λ -> vida media (días)."""
    return float(np.log(2.0) / lambda_decay)
