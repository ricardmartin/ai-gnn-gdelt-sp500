"""Scaffold del modelo GNN (Fase 4, inicio).

Encoder geopolitico: consume un snapshot diario (`Data` de `graph_build`) y produce
un embedding a nivel de grafo que resume el estado geopolitico del mundo ese dia.
Ese embedding es el que mas adelante se fusionara con los indicadores del S&P 500
y pasara por una cabeza de clasificacion triclase (sube / baja / neutro).

Estado: scaffold verificable con forward pass. El entrenamiento queda a la espera
de la variable objetivo (Fase 2, datos financieros). Por eso la cabeza de
clasificacion se incluye pero aun no se entrena.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv, global_mean_pool

from ..datos.grafo import NODE_FEATURE_NAMES, EDGE_FEATURE_NAMES


class GeoEncoder(nn.Module):
    """GATv2 de 2 capas con atencion sobre aristas -> embedding de grafo.

    Usa `edge_attr` (edge_dim) para que la atencion pondere el tipo/intensidad de
    la interaccion geopolitica, no solo la topologia.
    """

    def __init__(self, node_dim=len(NODE_FEATURE_NAMES), edge_dim=len(EDGE_FEATURE_NAMES),
                 hidden=64, out_dim=64, heads=4, dropout=0.2):
        super().__init__()
        self.dropout = dropout
        self.conv1 = GATv2Conv(node_dim, hidden, heads=heads, edge_dim=edge_dim,
                               dropout=dropout, add_self_loops=True)
        self.conv2 = GATv2Conv(hidden * heads, out_dim, heads=1, edge_dim=edge_dim,
                               dropout=dropout, add_self_loops=True)

    def forward(self, x, edge_index, edge_attr, batch=None):
        h = self.conv1(x, edge_index, edge_attr)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.conv2(h, edge_index, edge_attr)
        h = F.elu(h)
        if batch is None:  # un solo grafo
            batch = x.new_zeros(x.size(0), dtype=torch.long)
        return global_mean_pool(h, batch)  # [n_grafos, out_dim]


class GeoGNN(nn.Module):
    """Encoder geopolitico + cabeza triclase.

    `fin_dim` reserva el espacio para concatenar features del S&P 500 (Fase 2).
    Con `fin_dim=0` el modelo opera solo con el grafo (baseline geopolitico puro).
    """

    def __init__(self, emb_dim=64, fin_dim=0, hidden=64, n_clases=3, **enc_kw):
        super().__init__()
        self.encoder = GeoEncoder(out_dim=emb_dim, **enc_kw)
        self.head = nn.Sequential(
            nn.Linear(emb_dim + fin_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_clases),
        )

    def forward(self, data, fin=None):
        g = self.encoder(data.x, data.edge_index, data.edge_attr,
                         getattr(data, "batch", None))
        if fin is not None:
            g = torch.cat([g, fin], dim=-1)
        return self.head(g)  # logits [n_grafos, n_clases]


if __name__ == "__main__":
    # Verificacion del forward pass sobre los snapshots reales.
    from ..datos.preprocesar import reproducir_df_grafo
    from ..datos.grafo import construir_snapshots

    df_grafo, _ = reproducir_df_grafo()
    snaps = construir_snapshots(df_grafo)
    model = GeoGNN(emb_dim=64, fin_dim=0)
    model.eval()
    with torch.no_grad():
        for fecha, data in snaps.items():
            logits = model(data)
            probs = F.softmax(logits, dim=-1).squeeze(0)
            print(f"{fecha}: logits={logits.squeeze(0).tolist()} -> probs={[round(p, 3) for p in probs.tolist()]}")
    n_params = sum(p.numel() for p in model.parameters())
    print(f"\nParametros del modelo: {n_params:,}")
