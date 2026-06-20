"""
Construcción del grafo heterogéneo HeteroData por día.

Para cada día t se construye un grafo con:

- **Dos tipos de nodos:**
    'country' : los ~20 países del roster
    'market'  : un único nodo correspondiente al S&P 500

- **Dos tipos de aristas:**
    ('country', 'interactua', 'country')  : interacciones GDELT con decay
    ('country', 'expone', 'market')       : aristas estructurales

El tipado de las aristas país-país (por QuadClass) se mantiene como atributo
de arista, no como tipo separado en el grafo heterogéneo, para no multiplicar
los tipos. El modelo puede distinguirlas mediante el edge_attr.

Las features de los nodos `country` agregan los eventos GDELT en los que
participa cada país en el día t (entrante + saliente). El nodo `market`
lleva features financieras del SP500 a la fecha t.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

from src.modelo.decay import aplicar_decay
from src.utils.paises import (
    ROSTER, PAIS_A_INDICE, NUM_PAISES, peso_comercio,
)
from src.utils.logging import obtener_logger
from config import LAMBDA_DECAY, VENTANA_DECAY_DIAS

log = obtener_logger(__name__)


# Número de QuadClass distintas (4 en CAMEO: 1,2,3,4).
NUM_QUADCLASS = 4

# Dimensión del vector de features por nodo country.
# Componentes: [tono_medio, goldstein_medio, n_eventos_log,
#               num_mentions_log, peso_comercio,
#               grado_entrada_log, grado_salida_log,
#               quad1_frac, quad2_frac, quad3_frac, quad4_frac]
DIM_FEATURES_COUNTRY = 11

# Dimensión del vector de features del nodo market.
# Componentes: [retorno_1d, retorno_5d, retorno_21d,
#               volatilidad_21d, log_volumen,
#               vix, log_dxy, fed_funds, treasury_10y]
DIM_FEATURES_MARKET = 9

# Dimensión del vector de features por arista country-country.
# Componentes: [peso_decay, tono_ponderado, n_eventos_log,
#               one-hot QuadClass (4)]
DIM_FEATURES_EDGE_CC = 3 + NUM_QUADCLASS

# Dimensión del vector de features por arista country-market.
# Componente único: el peso de comercio bilateral.
DIM_FEATURES_EDGE_CM = 1


def calcular_features_countries(
    eventos_agregados: pd.DataFrame,
    fecha_corte: pd.Timestamp,
) -> np.ndarray:
    """
    Calcula la matriz de features de los nodos `country` para un día concreto.

    Args:
        eventos_agregados: salida de `agregar_eventos_por_dia_y_par`.
        fecha_corte: día t para el que se computa el grafo.

    Returns:
        Array de shape (NUM_PAISES, DIM_FEATURES_COUNTRY).
    """
    feats = np.zeros((NUM_PAISES, DIM_FEATURES_COUNTRY), dtype=np.float32)

    # Por defecto el peso de comercio (siempre conocido, no depende del día).
    for pais in ROSTER:
        feats[PAIS_A_INDICE[pais.id], 4] = peso_comercio(pais.id)

    if eventos_agregados.empty:
        return feats

    fecha_corte = pd.Timestamp(fecha_corte).normalize()
    fecha_min = fecha_corte - pd.Timedelta(days=VENTANA_DECAY_DIAS)
    df = eventos_agregados[
        (eventos_agregados["fecha"] <= fecha_corte) &
        (eventos_agregados["fecha"] >= fecha_min)
    ]
    if df.empty:
        return feats

    # Distancia temporal -> factor de decay (mismo que para aristas).
    dt = (fecha_corte - df["fecha"]).dt.days.astype(float).values
    decay_factor = np.exp(-LAMBDA_DECAY * dt)

    df = df.assign(_w=decay_factor)

    # Agregamos por país (considerando que un país participa tanto como
    # origen como destino). Sumamos las contribuciones ponderadas.
    for rol_col, signo in (("pais_origen", "salida"), ("pais_destino", "entrada")):
        sub = df.groupby(rol_col, observed=True).apply(
            lambda g: pd.Series({
                "tono_w": float((g["tono_medio"] * g["_w"]).sum()),
                "gold_w": float((g["goldstein_medio"] * g["_w"]).sum()),
                "n_w": float((g["n_eventos"] * g["_w"]).sum()),
                "mentions_w": float((g["num_mentions_total"] * g["_w"]).sum()),
                "suma_w": float(g["_w"].sum()),
            })
        )

        for pais_id, fila in sub.iterrows():
            idx = PAIS_A_INDICE.get(pais_id)
            if idx is None:
                continue
            sw = max(fila["suma_w"], 1e-9)
            # Acumulamos (suma de entrada y salida, normalizada).
            feats[idx, 0] += float(fila["tono_w"] / sw) / 2.0      # tono_medio
            feats[idx, 1] += float(fila["gold_w"] / sw) / 2.0      # goldstein_medio
            feats[idx, 2] += np.log1p(fila["n_w"]) / 2.0           # n_eventos_log
            feats[idx, 3] += np.log1p(fila["mentions_w"]) / 2.0    # mentions_log

            if signo == "entrada":
                feats[idx, 5] = np.log1p(fila["n_w"])              # grado entrada
            else:
                feats[idx, 6] = np.log1p(fila["n_w"])              # grado salida

    # Fracciones por QuadClass.
    for q in range(1, NUM_QUADCLASS + 1):
        sub_q = df[df["quadclass"] == str(q)]
        if sub_q.empty:
            continue
        for rol_col in ("pais_origen", "pais_destino"):
            agg = sub_q.groupby(rol_col, observed=True)["_w"].sum()
            for pais_id, w in agg.items():
                idx = PAIS_A_INDICE.get(pais_id)
                if idx is not None:
                    feats[idx, 6 + q] += float(w)

    # Normalizar fracciones de QuadClass por país.
    suma_q = feats[:, 7:7 + NUM_QUADCLASS].sum(axis=1, keepdims=True)
    suma_q = np.where(suma_q > 0, suma_q, 1.0)
    feats[:, 7:7 + NUM_QUADCLASS] /= suma_q

    return feats


def calcular_features_market(
    fecha_corte: pd.Timestamp,
    precios_sp500: pd.DataFrame,
    macro: Optional[pd.DataFrame] = None,
    vix: Optional[pd.Series] = None,
) -> np.ndarray:
    """
    Calcula el vector de features del nodo `market` para un día concreto.

    Args:
        fecha_corte: día t.
        precios_sp500: DataFrame de yfinance con columnas Open/High/Low/Close/Volume.
        macro: DataFrame de FRED (puede ser None).
        vix: serie del VIX (puede ser None).

    Returns:
        Array de shape (1, DIM_FEATURES_MARKET).
    """
    feats = np.zeros((1, DIM_FEATURES_MARKET), dtype=np.float32)

    # Usar solo precios hasta fecha_corte (anti-leakage).
    sp = precios_sp500.loc[:fecha_corte]
    if sp.empty:
        return feats

    close = sp["Close"].astype(float)
    vol = sp["Volume"].astype(float) if "Volume" in sp.columns else None

    if len(close) >= 2:
        feats[0, 0] = float(close.iloc[-1] / close.iloc[-2] - 1.0)
    if len(close) >= 6:
        feats[0, 1] = float(close.iloc[-1] / close.iloc[-6] - 1.0)
    if len(close) >= 22:
        feats[0, 2] = float(close.iloc[-1] / close.iloc[-22] - 1.0)
    if len(close) >= 22:
        retornos = close.pct_change().tail(21)
        feats[0, 3] = float(retornos.std()) if not retornos.empty else 0.0
    if vol is not None and not vol.empty:
        feats[0, 4] = float(np.log1p(vol.iloc[-1]))

    if vix is not None and not vix.empty:
        v = vix.loc[:fecha_corte]
        if not v.empty:
            feats[0, 5] = float(v.iloc[-1])

    if macro is not None and not macro.empty:
        m = macro.loc[:fecha_corte]
        if not m.empty:
            fila = m.iloc[-1]
            if "fed_funds" in m.columns and not pd.isna(fila.get("fed_funds")):
                feats[0, 7] = float(fila["fed_funds"])
            if "treasury_10y" in m.columns and not pd.isna(fila.get("treasury_10y")):
                feats[0, 8] = float(fila["treasury_10y"])

    return feats


def construir_aristas_cc(
    eventos_agregados: pd.DataFrame,
    fecha_corte: pd.Timestamp,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Construye las aristas country↔country (con decay aplicado).

    Returns:
        edge_index: tensor de shape (2, num_aristas).
        edge_attr:  tensor de shape (num_aristas, DIM_FEATURES_EDGE_CC).
    """
    aristas = aplicar_decay(eventos_agregados, fecha_corte)
    if aristas.empty:
        return (
            torch.zeros((2, 0), dtype=torch.long),
            torch.zeros((0, DIM_FEATURES_EDGE_CC), dtype=torch.float32),
        )

    origen_idx = aristas["pais_origen"].map(PAIS_A_INDICE).values
    destino_idx = aristas["pais_destino"].map(PAIS_A_INDICE).values

    edge_index = torch.tensor(
        np.vstack([origen_idx, destino_idx]).astype(np.int64),
        dtype=torch.long,
    )

    # Features de arista: [peso_decay, tono_ponderado, n_eventos_log, one_hot_quad]
    n = len(aristas)
    edge_attr = np.zeros((n, DIM_FEATURES_EDGE_CC), dtype=np.float32)
    edge_attr[:, 0] = aristas["peso_decay"].values
    edge_attr[:, 1] = aristas["tono_ponderado"].values
    edge_attr[:, 2] = np.log1p(aristas["n_eventos"].values)
    for i, q in enumerate(aristas["quadclass"].values):
        try:
            q_int = int(q)
            if 1 <= q_int <= NUM_QUADCLASS:
                edge_attr[i, 2 + q_int] = 1.0
        except (ValueError, TypeError):
            pass

    return edge_index, torch.tensor(edge_attr, dtype=torch.float32)


def construir_aristas_cm() -> tuple[torch.Tensor, torch.Tensor]:
    """
    Construye las aristas country → market (estáticas, una por país).

    Returns:
        edge_index: tensor de shape (2, NUM_PAISES). Fila 0 = índice de país,
                    fila 1 = 0 (siempre el único nodo market).
        edge_attr:  tensor de shape (NUM_PAISES, 1) con el peso de comercio.
    """
    indices = np.arange(NUM_PAISES, dtype=np.int64)
    edge_index = torch.tensor(
        np.vstack([indices, np.zeros(NUM_PAISES, dtype=np.int64)]),
        dtype=torch.long,
    )
    pesos = np.array(
        [peso_comercio(p.id) for p in ROSTER],
        dtype=np.float32,
    ).reshape(-1, 1)
    return edge_index, torch.tensor(pesos, dtype=torch.float32)


def construir_grafo_dia(
    eventos_agregados: pd.DataFrame,
    fecha_corte: pd.Timestamp,
    precios_sp500: pd.DataFrame,
    macro: Optional[pd.DataFrame] = None,
    vix: Optional[pd.Series] = None,
) -> HeteroData:
    """
    Construye un grafo heterogéneo HeteroData para una fecha concreta.

    Devuelve un HeteroData con:
        data['country'].x       -> (NUM_PAISES, DIM_FEATURES_COUNTRY)
        data['market'].x        -> (1, DIM_FEATURES_MARKET)
        data['country', 'interactua', 'country'].edge_index
        data['country', 'interactua', 'country'].edge_attr
        data['country', 'expone', 'market'].edge_index
        data['country', 'expone', 'market'].edge_attr
    """
    data = HeteroData()

    # Nodos country.
    x_country = calcular_features_countries(eventos_agregados, fecha_corte)
    data["country"].x = torch.tensor(x_country, dtype=torch.float32)

    # Nodo market.
    x_market = calcular_features_market(fecha_corte, precios_sp500, macro, vix)
    data["market"].x = torch.tensor(x_market, dtype=torch.float32)

    # Aristas country-country (con decay).
    ei_cc, ea_cc = construir_aristas_cc(eventos_agregados, fecha_corte)
    data["country", "interactua", "country"].edge_index = ei_cc
    data["country", "interactua", "country"].edge_attr = ea_cc

    # Aristas country -> market (estructurales).
    ei_cm, ea_cm = construir_aristas_cm()
    data["country", "expone", "market"].edge_index = ei_cm
    data["country", "expone", "market"].edge_attr = ea_cm

    return data
