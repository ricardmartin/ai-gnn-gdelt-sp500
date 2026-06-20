"""
Arquitectura HGNN heterogénea con atención.

Implementa el modelo descrito en el TFM:

1. Capa de proyección inicial: lleva las features de cada tipo de nodo
   (country y market) a un espacio de representación común.

2. Capas heterogéneas de message passing con atención (GATv2 vía HeteroConv).
   En cada capa, cada nodo agrega información de sus vecinos ponderando con
   atención específica por tipo de arista.

3. Cabeza de predicción: extrae el embedding final del nodo `market`, le aplica
   una capa lineal y devuelve los logits de las tres clases (baja/neutro/sube).

Se usa GATv2 envuelto en HeteroConv en lugar de HGT por simplicidad: ambas son
opciones válidas (sección 4.2.3 del TFM) y HeteroGAT facilita el desarrollo
inicial. Migrar a HGT más adelante es directo (cambiar la clase de capa).
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.nn import GATv2Conv, HeteroConv, Linear

from src.datos.grafo import (
    DIM_FEATURES_COUNTRY, DIM_FEATURES_MARKET,
    DIM_FEATURES_EDGE_CC, DIM_FEATURES_EDGE_CM,
)
from config import MODELO


class HGNNGeopolitica(nn.Module):
    """
    HGNN heterogénea para predicción de la dirección del S&P 500.

    Args:
        dim_oculta: dimensión del espacio común tras la proyección inicial.
        num_capas: número de capas de message passing.
        num_cabezas: número de cabezas de atención.
        dropout: dropout entre capas.
        num_clases: número de clases de salida (3 por defecto).
    """

    def __init__(
        self,
        dim_oculta: int = MODELO.dim_oculta,
        num_capas: int = MODELO.num_capas,
        num_cabezas: int = MODELO.num_cabezas,
        dropout: float = MODELO.dropout,
        num_clases: int = MODELO.num_clases,
    ) -> None:
        super().__init__()

        self.dim_oculta = dim_oculta
        self.num_capas = num_capas
        self.dropout = dropout

        # --- Proyección inicial por tipo de nodo ---------------------------------
        # Cada tipo de nodo tiene dimensión distinta; los llevamos a `dim_oculta`.
        self.proj_country = Linear(DIM_FEATURES_COUNTRY, dim_oculta)
        self.proj_market = Linear(DIM_FEATURES_MARKET, dim_oculta)

        # --- Capas heterogéneas de message passing -------------------------------
        # Para cada tipo de arista se define una operación GATv2 distinta.
        # HeteroConv aplica cada una al subgrafo del tipo correspondiente y suma
        # los mensajes por nodo.
        self.capas = nn.ModuleList()
        for _ in range(num_capas):
            conv = HeteroConv(
                {
                    ("country", "interactua", "country"): GATv2Conv(
                        in_channels=dim_oculta,
                        out_channels=dim_oculta // num_cabezas,
                        heads=num_cabezas,
                        dropout=dropout,
                        edge_dim=DIM_FEATURES_EDGE_CC,
                        add_self_loops=False,
                    ),
                    ("country", "expone", "market"): GATv2Conv(
                        in_channels=(dim_oculta, dim_oculta),  # (origen, destino)
                        out_channels=dim_oculta // num_cabezas,
                        heads=num_cabezas,
                        dropout=dropout,
                        edge_dim=DIM_FEATURES_EDGE_CM,
                        add_self_loops=False,
                    ),
                },
                aggr="sum",
            )
            self.capas.append(conv)

        # --- Cabeza de clasificación --------------------------------------------
        # Toma el embedding del nodo market y produce los logits.
        self.cabeza = nn.Sequential(
            nn.Linear(dim_oculta, dim_oculta),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim_oculta, num_clases),
        )

    def forward(self, data: HeteroData) -> torch.Tensor:
        """
        Propagación hacia adelante.

        Args:
            data: HeteroData con la estructura producida por `construir_grafo_dia`.

        Returns:
            Tensor de logits de shape (1, num_clases) para un único grafo, o
            (B, num_clases) si el HeteroData ha sido batched con `Batch`.
        """
        # --- Proyección inicial -------------------------------------------------
        x_dict = {
            "country": self.proj_country(data["country"].x),
            "market": self.proj_market(data["market"].x),
        }

        edge_index_dict = {
            ("country", "interactua", "country"):
                data["country", "interactua", "country"].edge_index,
            ("country", "expone", "market"):
                data["country", "expone", "market"].edge_index,
        }

        edge_attr_dict = {
            ("country", "interactua", "country"):
                data["country", "interactua", "country"].edge_attr,
            ("country", "expone", "market"):
                data["country", "expone", "market"].edge_attr,
        }

        # --- Message passing ----------------------------------------------------
        for capa in self.capas:
            x_dict = capa(x_dict, edge_index_dict, edge_attr_dict=edge_attr_dict)
            x_dict = {tipo: F.relu(x) for tipo, x in x_dict.items()}
            x_dict = {tipo: F.dropout(x, p=self.dropout, training=self.training)
                      for tipo, x in x_dict.items()}

        # --- Cabeza de predicción desde el nodo market --------------------------
        x_market = x_dict["market"]
        logits = self.cabeza(x_market)
        return logits

    def num_parametros(self) -> int:
        """Devuelve el número total de parámetros entrenables del modelo."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
