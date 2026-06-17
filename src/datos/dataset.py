"""Ensamblado del dataset: une los snapshots del grafo con las etiquetas del S&P 500.

Orquesta `preprocesar` (GDELT -> df_grafo), `financiero` (etiquetas triclase) y
`grafo` (snapshots PyG) para producir la lista de snapshots etiquetados lista para
entrenar, usando el ALINEAMIENTO B: un snapshot por sesion de mercado, agregando
todos los dias GDELT (incluidos finde/festivo) desde el cierre anterior.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .preprocesar import reproducir_df_grafo
from .financiero import construir_targets
from .grafo import construir_snapshots


def cargar_df_grafo(raw_dir="data/raw", patron="2022*.export.CSV", k_min=5,
                    data_dir="data", cache="data/df_grafo_2022.pkl", refrescar=False):
    """Devuelve `df_grafo` cacheado en disco; lo reconstruye solo si falta el cache.

    Reconstruirlo (clustering de todos los dias) es costoso, asi que se persiste.
    """
    cache = Path(cache)
    if cache.exists() and not refrescar:
        return pd.read_pickle(cache)
    df_grafo, _ = reproducir_df_grafo(raw_dir, data_dir, k_min=k_min, patron=patron)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df_grafo.to_pickle(cache)
    return df_grafo


def construir_dataset(raw_dir="data/raw", patron="2022*.export.CSV",
                      inicio_sp="2022-02-09", fin_sp="2022-02-26",
                      k_min=5, tau=0.001, data_dir="data",
                      cache="data/df_grafo_2022.pkl", refrescar=False):
    """Construye los snapshots B etiquetados para un periodo.

    Devuelve (snapshots, targets):
      - snapshots: {market_date: Data}  con `data.y` (0/1/2) y `data.dias_gdelt`.
      - targets:   DataFrame de la alineacion gdelt_date -> sesion + etiqueta.
    """
    # 1. df_grafo sobre los dias GDELT del periodo (cacheado)
    df_grafo = cargar_df_grafo(raw_dir, patron, k_min, data_dir, cache, refrescar)

    # 2. etiquetas alineadas: cada dia GDELT -> su siguiente sesion de mercado
    gdelt_dates = sorted(df_grafo["fecha"].unique())
    targets = construir_targets(gdelt_dates, inicio_sp, fin_sp, tau=tau)

    # 3. mapeos para el alineamiento B
    sesiones = dict(zip(targets["gdelt_date"], targets["market_date"]))
    etiquetas = (targets.drop_duplicates("market_date")
                 .set_index("market_date")["y"].astype(int).to_dict())

    # 4. snapshots B etiquetados
    snapshots = construir_snapshots(df_grafo, sesiones=sesiones, etiquetas=etiquetas)
    return snapshots, targets


if __name__ == "__main__":
    snaps, targets = construir_dataset()
    print(f"Snapshots B (1 por sesion de mercado): {len(snaps)}\n")
    print(f"{'sesion':>12}  {'y':>2}  {'clase':>7}  dias_gdelt_agregados")
    clase_inv = {0: "baja", 1: "neutro", 2: "sube"}
    for sesion, d in snaps.items():
        y = int(d.y.item())
        print(f"{sesion:>12}  {y:>2}  {clase_inv[y]:>7}  {d.dias_gdelt}")
    print("\nFormas (sesion: x, edges):")
    for sesion, d in snaps.items():
        print(f"  {sesion}: x={tuple(d.x.shape)} edge_index={tuple(d.edge_index.shape)}")
