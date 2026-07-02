"""
Normalización de features de los grafos con estadísticas SOLO del train.

Problema que resuelve: las features llegan al modelo en escalas salvajemente
distintas (retorno diario ~0.01, VIX ~20, log-volumen ~22, Goldstein ±10...).
Sin estandarizar, las features de mayor escala dominan las sumas ponderadas y
el mecanismo de atención, y las más informativas (p. ej. los retornos) quedan
prácticamente ignoradas al inicio del entrenamiento.

Reglas anti-leakage:
    1. Las medias y desviaciones se calculan EXCLUSIVAMENTE sobre los grafos
       del train (interno) de cada fold.
    2. Esas estadísticas "congeladas" se aplican después a train, validación
       interna y test por igual.

Qué se estandariza:
    - `country.x` : todas las columnas. (Las fracciones QuadClass ya están en
      [0,1]; estandarizarlas es inocuo y simplifica el código.)
    - `market.x`  : todas las columnas. Las columnas constantes (p. ej. una
      feature no poblada) quedan en 0 gracias al guard de std.
    - edge_attr de ('country','interactua','country') : SOLO las 3 primeras
      columnas continuas [peso_decay, tono_ponderado, n_eventos_log]. El
      one-hot de QuadClass (columnas 3..6) se deja intacto: es categórico.
    - edge_attr de país-mercado: NO se toca (peso de comercio, ya en [0,1] y
      constante entre días; estandarizarlo lo anularía).

Seguridad de memoria: `transform` devuelve un CLON del grafo. Nunca muta el
grafo de entrada, porque `DatasetGrafoDiario` puede estar cacheando objetos
compartidos entre folds y mutarlos in-place corrompería experimentos vecinos.
"""

from __future__ import annotations

import numpy as np
import torch
from torch_geometric.data import HeteroData

from src.utils.logging import obtener_logger

log = obtener_logger(__name__)

# Número de columnas continuas al inicio del edge_attr país-país
# (peso_decay, tono_ponderado, n_eventos_log). El resto es one-hot QuadClass.
_N_COLS_CONTINUAS_EDGE_CC = 3

_REL_CC = ("country", "interactua", "country")

_EPS_STD = 1e-8


class NormalizadorGrafos:
    """
    Estandarizador (media 0, desviación 1) de las features de los HeteroData.

    Uso:
        norm = NormalizadorGrafos().fit(grafos_train)
        grafos_train_n = [norm.transform(g) for g in grafos_train]
        grafos_test_n  = [norm.transform(g) for g in grafos_test]
    """

    def __init__(self) -> None:
        self.ajustado: bool = False
        self.media_country: torch.Tensor | None = None
        self.std_country: torch.Tensor | None = None
        self.media_market: torch.Tensor | None = None
        self.std_market: torch.Tensor | None = None
        self.media_edge_cc: torch.Tensor | None = None
        self.std_edge_cc: torch.Tensor | None = None

    # ------------------------------------------------------------------ fit

    def fit(self, grafos: list[HeteroData]) -> "NormalizadorGrafos":
        """
        Calcula medias y desviaciones sobre una lista de grafos (el TRAIN).

        Args:
            grafos: lista de HeteroData del conjunto de entrenamiento.

        Returns:
            self (patrón sklearn), ya ajustado.
        """
        if not grafos:
            raise ValueError("NormalizadorGrafos.fit: lista de grafos vacía")

        # --- country.x: apilar todos los nodos país de todos los días -------
        x_country = torch.cat([g["country"].x for g in grafos], dim=0).float()
        self.media_country, self.std_country = self._media_std(x_country)

        # --- market.x: un vector por día -------------------------------------
        x_market = torch.cat([g["market"].x for g in grafos], dim=0).float()
        self.media_market, self.std_market = self._media_std(x_market)

        # --- edge_attr país-país: puede haber días sin aristas ---------------
        bloques = [
            g[_REL_CC].edge_attr
            for g in grafos
            if g[_REL_CC].edge_attr is not None and g[_REL_CC].edge_attr.numel() > 0
        ]
        if bloques:
            ea = torch.cat(bloques, dim=0).float()
            n_cont = min(_N_COLS_CONTINUAS_EDGE_CC, ea.shape[1])
            media, std = self._media_std(ea[:, :n_cont])
            self.media_edge_cc, self.std_edge_cc = media, std
        else:
            # Ningún grafo de train tiene aristas país-país: no hay nada que
            # normalizar en las aristas (transform lo respetará).
            self.media_edge_cc, self.std_edge_cc = None, None
            log.warning(
                "NormalizadorGrafos: ningún grafo de train tiene aristas "
                "país-país; el edge_attr no se normalizará."
            )

        self.ajustado = True
        log.info(
            "Normalizador ajustado sobre %d grafos de train "
            "(country %s cols, market %s cols, edge_cc %s cols continuas)",
            len(grafos),
            int(self.media_country.numel()),
            int(self.media_market.numel()),
            0 if self.media_edge_cc is None else int(self.media_edge_cc.numel()),
        )
        return self

    @staticmethod
    def _media_std(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Media y desviación por columna, con guard para columnas constantes:
        si std < eps, se sustituye por 1.0, de modo que la columna normalizada
        queda en (x - media) ≈ 0 en lugar de explotar por división entre ~0.
        """
        media = x.mean(dim=0)
        std = x.std(dim=0, unbiased=False)
        std = torch.where(std < _EPS_STD, torch.ones_like(std), std)
        return media, std

    # ------------------------------------------------------------- transform

    def transform(self, grafo: HeteroData) -> HeteroData:
        """
        Devuelve un CLON del grafo con las features estandarizadas.

        El grafo original NO se modifica (imprescindible si el dataset cachea
        objetos compartidos entre folds/semillas).
        """
        if not self.ajustado:
            raise RuntimeError("NormalizadorGrafos: llama a fit() antes de transform()")

        g = grafo.clone()

        g["country"].x = (g["country"].x.float() - self.media_country) / self.std_country
        g["market"].x = (g["market"].x.float() - self.media_market) / self.std_market

        ea = g[_REL_CC].edge_attr
        if (
            self.media_edge_cc is not None
            and ea is not None
            and ea.numel() > 0
        ):
            ea = ea.float().clone()
            n_cont = int(self.media_edge_cc.numel())
            ea[:, :n_cont] = (ea[:, :n_cont] - self.media_edge_cc) / self.std_edge_cc
            g[_REL_CC].edge_attr = ea

        return g

    def transform_lista(self, grafos: list[HeteroData]) -> list[HeteroData]:
        """Aplica `transform` a una lista completa."""
        return [self.transform(g) for g in grafos]
