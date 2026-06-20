"""
Preprocesado de eventos GDELT.

Toma los CSVs crudos en `data/raw/`, los carga, filtra y agrega para producir
un DataFrame de eventos relevantes listo para construir el grafo.

Filtros aplicados:

1. Se descartan filas que no involucran a dos países del ROSTER.
2. Se descartan eventos con cobertura mediática insuficiente (NumMentions bajo).
3. Se descartan filas con valores faltantes en los campos críticos.

Salida: un DataFrame con una fila por evento, columnas tipadas, lista para
ser consumida por `grafo.py` o por las funciones de agregación temporal.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.datos.descarga_gdelt import (
    COLUMNAS_GDELT_1_0,
    COLUMNAS_NUMERICAS,
    COLUMNAS_RELEVANTES,
)
from src.utils.logging import obtener_logger
from src.utils.paises import COD_A_PAIS
from config import MIN_NUM_MENTIONS

log = obtener_logger(__name__)


def cargar_csv_gdelt(ruta: Path) -> pd.DataFrame:
    """
    Carga un fichero diario de GDELT 1.0 con el esquema correcto.

    El fichero no tiene cabecera y está separado por tabuladores. La mayoría
    de columnas se mantienen como string para preservar códigos CAMEO y FIPS
    (que son numéricos en apariencia pero deben tratarse como categóricos).
    """
    df = pd.read_csv(
        ruta,
        sep="\t",
        header=None,
        names=list(COLUMNAS_GDELT_1_0),
        dtype=str,
        na_values=[""],
        keep_default_na=False,
        quoting=3,   # csv.QUOTE_NONE: GDELT no usa comillas
        on_bad_lines="skip",
    )

    for c in COLUMNAS_NUMERICAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Convertir SQLDATE a fecha real (formato YYYYMMDD).
    df["fecha"] = pd.to_datetime(df["SQLDATE"], format="%Y%m%d", errors="coerce")

    return df[list(COLUMNAS_RELEVANTES) + ["fecha"]]


def filtrar_roster(df: pd.DataFrame) -> pd.DataFrame:
    """
    Conserva solo eventos en los que tanto Actor1 como Actor2 pertenecen al
    ROSTER de países definido en `src/utils/paises.py`.

    Añade dos columnas auxiliares:
        pais_origen  -> id del nodo de Actor1
        pais_destino -> id del nodo de Actor2
    """
    df = df.copy()
    df["pais_origen"] = df["Actor1CountryCode"].map(COD_A_PAIS)
    df["pais_destino"] = df["Actor2CountryCode"].map(COD_A_PAIS)

    mask = df["pais_origen"].notna() & df["pais_destino"].notna()
    df_filt = df.loc[mask].copy()

    log.debug(
        "Filtro roster: %d/%d eventos conservados (%.1f%%)",
        len(df_filt), len(df), 100.0 * len(df_filt) / max(1, len(df))
    )
    return df_filt


def filtrar_cobertura(df: pd.DataFrame, min_mentions: int = MIN_NUM_MENTIONS) -> pd.DataFrame:
    """Conserva solo eventos con NumMentions >= min_mentions."""
    df_filt = df[df["NumMentions"] >= min_mentions].copy()
    log.debug(
        "Filtro cobertura (NumMentions ≥ %d): %d/%d eventos",
        min_mentions, len(df_filt), len(df),
    )
    return df_filt


def preprocesar_dia(ruta: Path) -> pd.DataFrame:
    """
    Pipeline de preprocesado para un CSV diario de GDELT.

    Aplica en orden: carga, filtro por roster, filtro por cobertura.
    Devuelve un DataFrame de eventos relevantes.
    """
    df = cargar_csv_gdelt(ruta)
    df = filtrar_roster(df)
    df = filtrar_cobertura(df)
    df = df.dropna(subset=["GoldsteinScale", "AvgTone", "QuadClass"]).reset_index(drop=True)
    return df


def preprocesar_rango(rutas: list[Path]) -> pd.DataFrame:
    """
    Preprocesa una lista de CSVs y devuelve un único DataFrame concatenado.
    """
    dfs: list[pd.DataFrame] = []
    for ruta in rutas:
        try:
            dfs.append(preprocesar_dia(ruta))
        except Exception as e:
            log.warning("Fallo procesando %s: %s", ruta.name, e)

    if not dfs:
        return pd.DataFrame()

    df_total = pd.concat(dfs, ignore_index=True)
    log.info("Preprocesado total: %d eventos en %d días", len(df_total), len(rutas))
    return df_total


def agregar_eventos_por_dia_y_par(df_eventos: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega los eventos a nivel (fecha, pais_origen, pais_destino, QuadClass).

    Esta agregación es el insumo directo del grafo: cada fila representa una
    "arista resumen" entre dos países en un día concreto, con sus atributos
    agregados.

    Devuelve un DataFrame con columnas:
        fecha, pais_origen, pais_destino, quadclass,
        n_eventos, goldstein_medio, tono_medio, num_mentions_total
    """
    if df_eventos.empty:
        return pd.DataFrame()

    df = df_eventos.copy()
    df["quadclass"] = df["QuadClass"].astype(str)

    grupos = df.groupby(
        ["fecha", "pais_origen", "pais_destino", "quadclass"],
        observed=True,
    )

    agregado = grupos.agg(
        n_eventos=("GLOBALEVENTID", "size"),
        goldstein_medio=("GoldsteinScale", "mean"),
        tono_medio=("AvgTone", "mean"),
        num_mentions_total=("NumMentions", "sum"),
    ).reset_index()

    return agregado
