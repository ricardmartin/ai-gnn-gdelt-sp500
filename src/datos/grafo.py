"""Construccion del grafo geopolitico diario (Fase 3 / inicio del GNN).

Convierte `df_grafo` (salida del pipeline de filtrado, notebook 4.6) en un grafo
dinamico discreto: un snapshot por dia. Cada snapshot es un objeto PyG `Data`.

Decisiones de diseno (acordadas con el usuario):
  - Nodos: roster fijo de ~20 paises (`NODOS_ACTA`). El indice de cada pais es
    estable entre snapshots, lo que facilita el GNN dinamico discreto.
  - Aristas: DIRIGIDAS Actor1 -> Actor2, agregando los eventos del dia por par de
    paises. Solo pares en los que AMBOS actores estan en el roster.
  - Features de nodo: actividad geopolitica del pais ese dia (como actor1 o actor2).
  - Target (y): direccion del S&P 500 para la sesion siguiente. Aun no disponible
    (Fase 2 pendiente); se deja `data.y = None`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from .preprocesar import NODOS_ACTA

# Orden canonico y estable de los nodos. No cambia entre dias.
NODE_CODES = sorted(NODOS_ACTA)
NODE_INDEX = {code: i for i, code in enumerate(NODE_CODES)}
N_NODOS = len(NODE_CODES)

_QUADS = ["1", "2", "3", "4"]  # QuadClass: verbal/material x coop/conflict

NODE_FEATURE_NAMES = [
    "log_n_eventos", "frac_como_actor1", "mean_goldstein", "mean_avgtone",
    "log_sum_mentions", "frac_q1", "frac_q2", "frac_q3", "frac_q4",
]
EDGE_FEATURE_NAMES = [
    "log_n_eventos", "mean_goldstein", "mean_avgtone", "log_sum_mentions",
    "frac_q1", "frac_q2", "frac_q3", "frac_q4",
]


def _frac_quads(quad_series: pd.Series) -> np.ndarray:
    """Fraccion de eventos en cada QuadClass (1..4). Vector de 4."""
    n = len(quad_series)
    if n == 0:
        return np.zeros(4, dtype="float32")
    vc = quad_series.astype(str).value_counts()
    return np.array([vc.get(q, 0) / n for q in _QUADS], dtype="float32")


def _node_features(sub: pd.DataFrame) -> np.ndarray:
    """Matriz [N_NODOS, 9] de features de nodo para un dia.

    Cada pais agrega los eventos en los que participa como actor1 o actor2.
    """
    X = np.zeros((N_NODOS, len(NODE_FEATURE_NAMES)), dtype="float32")

    # Forma larga: una fila por (evento, rol) cuando el actor esta en el roster.
    largos = []
    for col, rol in (("Actor1CountryCode", 1), ("Actor2CountryCode", 2)):
        m = sub[col].isin(NODE_INDEX)
        if m.any():
            tmp = sub.loc[m, [col, "GoldsteinScale", "AvgTone", "NumMentions", "QuadClass"]].copy()
            tmp = tmp.rename(columns={col: "pais"})
            tmp["rol"] = rol
            largos.append(tmp)
    if not largos:
        return X
    largo = pd.concat(largos, ignore_index=True)

    for code, g in largo.groupby("pais"):
        i = NODE_INDEX[code]
        n = len(g)
        X[i, 0] = np.log1p(n)
        X[i, 1] = (g["rol"] == 1).mean()
        X[i, 2] = g["GoldsteinScale"].mean(skipna=True)
        X[i, 3] = g["AvgTone"].mean(skipna=True)
        X[i, 4] = np.log1p(g["NumMentions"].sum(skipna=True))
        X[i, 5:9] = _frac_quads(g["QuadClass"])
    return np.nan_to_num(X, nan=0.0)


def _edges(sub: pd.DataFrame):
    """edge_index [2, E] y edge_attr [E, 8] para un dia (aristas dirigidas roster->roster)."""
    m = sub["Actor1CountryCode"].isin(NODE_INDEX) & sub["Actor2CountryCode"].isin(NODE_INDEX)
    par = sub.loc[m]
    if par.empty:
        return (torch.empty((2, 0), dtype=torch.long),
                torch.empty((0, len(EDGE_FEATURE_NAMES)), dtype=torch.float))

    src_list, dst_list, feats = [], [], []
    for (a1, a2), g in par.groupby(["Actor1CountryCode", "Actor2CountryCode"]):
        src_list.append(NODE_INDEX[a1])
        dst_list.append(NODE_INDEX[a2])
        n = len(g)
        feats.append([
            np.log1p(n),
            np.nan_to_num(g["GoldsteinScale"].mean(skipna=True)),
            np.nan_to_num(g["AvgTone"].mean(skipna=True)),
            np.log1p(np.nan_to_num(g["NumMentions"].sum(skipna=True))),
            *_frac_quads(g["QuadClass"]),
        ])

    edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
    edge_attr = torch.tensor(np.array(feats, dtype="float32"), dtype=torch.float)
    return edge_index, edge_attr


def construir_snapshot(sub: pd.DataFrame, sesion: str, y=None) -> Data:
    """Crea el `Data` PyG de una sesion a partir de su sub-DataFrame de df_grafo.

    `sub` puede agregar varios dias GDELT (alineamiento B). `sesion` es el id de la
    sesion (p. ej. la fecha de mercado predicha). `y` es la etiqueta triclase (0/1/2).
    """
    x = torch.tensor(_node_features(sub), dtype=torch.float)
    edge_index, edge_attr = _edges(sub)
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    data.num_nodes = N_NODOS  # el orden de nodos es siempre NODE_CODES (constante de modulo)
    data.sesion = sesion
    data.dias_gdelt = sorted(sub["fecha"].unique().tolist())
    data.y = None if y is None else torch.tensor([int(y)], dtype=torch.long)
    return data


def construir_snapshots(df_grafo: pd.DataFrame, sesiones: dict | None = None,
                        etiquetas: dict | None = None) -> dict[str, Data]:
    """Construye los snapshots PyG. Devuelve {sesion: Data} ordenado por sesion.

    - `sesiones=None`  -> alineamiento A: un snapshot por dia GDELT (sesion = fecha).
    - `sesiones={gdelt_date: sesion}` -> alineamiento B: agrega todos los dias GDELT
      que mapean a la misma sesion de mercado en un unico snapshot.
    - `etiquetas={sesion: y}` -> asigna la etiqueta triclase a cada snapshot.
    """
    df = df_grafo.copy()
    if sesiones is None:
        df["sesion"] = df["fecha"]
    else:
        df = df[df["fecha"].isin(sesiones)].copy()
        df["sesion"] = df["fecha"].map(sesiones)

    etiquetas = etiquetas or {}
    snapshots = {}
    for sesion in sorted(df["sesion"].unique()):
        sub = df[df["sesion"] == sesion]
        snapshots[sesion] = construir_snapshot(sub, sesion, y=etiquetas.get(sesion))
    return snapshots
