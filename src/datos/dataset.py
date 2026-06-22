"""
Dataset que ensambla snapshots de grafo + etiquetas para entrenar.

A diferencia de los datasets canónicos de PyG, aquí cada muestra es un grafo
heterogéneo entero (HeteroData) que representa un día concreto, junto con su
etiqueta triclase. El dataset:

1. Toma el DataFrame de etiquetas (fecha_grafo -> clase).
2. Para cada fila, construye el grafo del día correspondiente bajo demanda
   (o pre-construye todo y cachea).
3. Devuelve pares (HeteroData, etiqueta).

Para el entrenamiento se usa un DataLoader de PyG (`torch_geometric.loader`)
que sabe juntar HeteroData en batches.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import torch
from torch_geometric.data import HeteroData

from src.datos.grafo import construir_grafo_dia
from src.utils.logging import obtener_logger

log = obtener_logger(__name__)


class DatasetGrafoDiario:
    """
    Dataset de grafos diarios + etiquetas.

    No hereda de torch.utils.data.Dataset porque PyG funciona mejor con una
    interfaz simple iterable/indexable; el DataLoader de PyG lo aceptará igual.

    Args:
        eventos_agregados: DataFrame de eventos agregados (todos los días).
        etiquetas: DataFrame con columnas fecha_grafo, fecha_target, clase, retorno.
        precios_sp500: DataFrame de precios diarios del SP500.
        macro: DataFrame de variables macro (opcional).
        vix: serie del VIX (opcional).
        precomputar: si True, construye todos los grafos en memoria al inicio.
            Útil para datasets pequeños; con muchos días puede ser pesado.
        participacion: agregación de participación a nivel de nodo (salida de
            `agregar_participacion_por_dia_y_pais`), que incluye los eventos de
            un solo actor del filtro OR. Si se omite, las features de nodo se
            derivan de `eventos_agregados` y NO incluyen esos eventos.
    """

    def __init__(
        self,
        eventos_agregados: pd.DataFrame,
        etiquetas: pd.DataFrame,
        precios_sp500: pd.DataFrame,
        macro: Optional[pd.DataFrame] = None,
        vix: Optional[pd.Series] = None,
        precomputar: bool = False,
        participacion: Optional[pd.DataFrame] = None,
    ) -> None:
        self.eventos_agregados = eventos_agregados
        self.etiquetas = etiquetas.reset_index(drop=True)
        self.precios_sp500 = precios_sp500
        self.macro = macro
        self.vix = vix
        self.participacion = participacion

        # Caché en memoria, vacía o pre-llenada.
        self._cache: dict[int, HeteroData] = {}
        if precomputar:
            log.info("Precomputando %d grafos...", len(self.etiquetas))
            for i in range(len(self.etiquetas)):
                self._cache[i] = self._construir(i)
            log.info("Precomputación completada")

    def _construir(self, idx: int) -> HeteroData:
        fila = self.etiquetas.iloc[idx]
        fecha = pd.Timestamp(fila["fecha_grafo"])
        return construir_grafo_dia(
            self.eventos_agregados,
            fecha,
            self.precios_sp500,
            self.macro,
            self.vix,
            participacion=self.participacion,
        )

    def __len__(self) -> int:
        return len(self.etiquetas)

    def __getitem__(self, idx: int) -> tuple[HeteroData, int]:
        if idx in self._cache:
            data = self._cache[idx]
        else:
            data = self._construir(idx)
            # Caché lazy: guardamos solo si no agotamos memoria.
            self._cache[idx] = data

        # Incrustamos la etiqueta dentro del HeteroData para que viaje en el batch.
        clase = int(self.etiquetas.iloc[idx]["clase"])
        data["market"].y = torch.tensor([clase], dtype=torch.long)
        return data, clase

    def obtener_solo_grafos(self) -> list[HeteroData]:
        """Devuelve una lista con todos los HeteroData (sin la etiqueta como tupla)."""
        return [self[i][0] for i in range(len(self))]
