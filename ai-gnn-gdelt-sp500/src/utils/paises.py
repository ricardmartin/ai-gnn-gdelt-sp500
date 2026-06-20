"""
Roster de nodos país y pesos iniciales de exposición al S&P 500.

Este módulo centraliza dos piezas críticas del diseño del grafo:

1. La lista de países que constituyen los nodos de tipo `country`. Se ha optado
   por un conjunto reducido (~20 nodos) seleccionados por su relevancia económica
   y geopolítica para el mercado estadounidense, en lugar de incluir todos los
   países que aparecen en GDELT. La justificación está en la sección 4.2.4
   del documento del TFM.

2. La matriz de pesos iniciales de las aristas país → market. Estos pesos
   informan al modelo de la exposición estructural de cada país al SP500 antes
   del entrenamiento. Como aproximación de exposición se utiliza el porcentaje
   del comercio bilateral con Estados Unidos (importaciones + exportaciones)
   sobre el total del comercio exterior de USA.

   AJUSTAR: los valores numéricos aquí son ESTIMACIONES de orden de magnitud
   para que el sistema arranque. Deben sustituirse por datos reales de
   UN Comtrade o equivalente antes de los experimentos finales.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Pais:
    """Representación interna de un país (o entidad supranacional) del roster."""
    # Identificador único en el código (sin ambigüedades, en mayúsculas).
    id: str
    # Nombre legible.
    nombre: str
    # Códigos por los que GDELT puede referirse a este actor en Actor1CountryCode
    # y Actor2CountryCode. Se incluyen variantes habituales (CAMEO/FIPS).
    codigos_gdelt: tuple[str, ...]


# ---------------------------------------------------------------------------
# Roster propuesto (~20 nodos)
# ---------------------------------------------------------------------------
# AJUSTAR: lista provisional. La composición exacta debe validarse tras el EDA
# en función de volumen de eventos y relevancia para el target.

ROSTER: tuple[Pais, ...] = (
    Pais("USA",  "Estados Unidos",          ("USA",)),
    Pais("CHN",  "China",                   ("CHN",)),
    Pais("RUS",  "Rusia",                   ("RUS",)),
    Pais("EUR",  "Unión Europea",           ("EUR", "EEC")),
    Pais("DEU",  "Alemania",                ("DEU",)),
    Pais("FRA",  "Francia",                 ("FRA",)),
    Pais("GBR",  "Reino Unido",             ("GBR",)),
    Pais("JPN",  "Japón",                   ("JPN",)),
    Pais("KOR",  "Corea del Sur",           ("KOR",)),
    Pais("IND",  "India",                   ("IND",)),
    Pais("TWN",  "Taiwán",                  ("TWN",)),
    Pais("CAN",  "Canadá",                  ("CAN",)),
    Pais("MEX",  "México",                  ("MEX",)),
    Pais("BRA",  "Brasil",                  ("BRA",)),
    Pais("SAU",  "Arabia Saudí",            ("SAU",)),
    Pais("IRN",  "Irán",                    ("IRN",)),
    Pais("ISR",  "Israel",                  ("ISR",)),
    Pais("TUR",  "Turquía",                 ("TUR",)),
    Pais("PRK",  "Corea del Norte",         ("PRK",)),
    Pais("AUS",  "Australia",               ("AUS",)),
)


# Diccionarios auxiliares útiles en el resto del código.
# Mapean código GDELT -> id de nodo, e id de nodo -> índice entero estable.
COD_A_PAIS: dict[str, str] = {
    cod: p.id for p in ROSTER for cod in p.codigos_gdelt
}

PAIS_A_INDICE: dict[str, int] = {p.id: i for i, p in enumerate(ROSTER)}
INDICE_A_PAIS: dict[int, str] = {i: p.id for i, p in enumerate(ROSTER)}

NUM_PAISES: int = len(ROSTER)


def resolver_codigo(codigo: str | None) -> str | None:
    """
    Dada una etiqueta de país tal y como aparece en GDELT (Actor1CountryCode o
    Actor2CountryCode), devuelve el id del nodo del roster correspondiente,
    o None si el país no forma parte del roster.
    """
    if not codigo:
        return None
    return COD_A_PAIS.get(codigo)


# ---------------------------------------------------------------------------
# Comercio bilateral con USA (pesos iniciales de aristas país → market)
# ---------------------------------------------------------------------------
# AJUSTAR: estos valores son aproximaciones de orden de magnitud, expresadas
# como fracción del comercio exterior total de USA. Deben sustituirse por datos
# reales antes de los experimentos definitivos. La fuente recomendada es
# UN Comtrade (gratis) o el U.S. Census Bureau Trade Data.
#
# Para USA -> mercado USA se asigna 1.0 (autoexposición máxima).
# Para el resto, el peso es relativo a USA.

PESOS_COMERCIO_BILATERAL: dict[str, float] = {
    "USA": 1.00,
    "CHN": 0.16,
    "MEX": 0.15,
    "CAN": 0.14,
    "JPN": 0.05,
    "DEU": 0.04,
    "KOR": 0.03,
    "EUR": 0.10,   # bloque agregado, sin Alemania/Francia/UK individuales
    "FRA": 0.02,
    "GBR": 0.03,
    "IND": 0.02,
    "TWN": 0.03,
    "BRA": 0.02,
    "SAU": 0.01,
    "ISR": 0.01,
    "TUR": 0.01,
    "RUS": 0.005,  # tras sanciones
    "IRN": 0.001,
    "PRK": 0.0001,
    "AUS": 0.01,
}


def peso_comercio(pais_id: str) -> float:
    """Devuelve el peso de exposición comercial de `pais_id` al mercado USA."""
    return PESOS_COMERCIO_BILATERAL.get(pais_id, 0.0)
