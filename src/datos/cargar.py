"""Entrada/salida de datos: lectura de GDELT 1.0 y descarga del S&P 500.

Funciones de I/O puro (descargar / leer). El preprocesamiento de GDELT hacia el
grafo vive en `preprocesar.py`; la construccion de etiquetas en `financiero.py`.
"""
from __future__ import annotations

import io
import os
import urllib.request
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Esquema de las 58 columnas de GDELT 1.0
# --------------------------------------------------------------------------- #
COLUMNAS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long",
    "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long",
    "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]
assert len(COLUMNAS) == 58, f"Esperadas 58 columnas, hay {len(COLUMNAS)}"

COLS_NUMERICAS = ["GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone"]

TICKER_SP500 = "^GSPC"


# --------------------------------------------------------------------------- #
# GDELT: descarga de ficheros diarios
# --------------------------------------------------------------------------- #
def descargar_dia(fecha: date, destino_dir="data/raw") -> str:
    """Descarga (y descomprime) el export diario de GDELT 1.0 para `fecha`."""
    os.makedirs(destino_dir, exist_ok=True)
    nombre = f"{fecha:%Y%m%d}.export.CSV"
    destino = os.path.join(destino_dir, nombre)
    if os.path.exists(destino):
        print(f"  {fecha:%Y%m%d}  ya existe")
        return destino
    url = f"http://data.gdeltproject.org/events/{nombre}.zip"
    with urllib.request.urlopen(url) as r:
        contenido = r.read()
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        with z.open(z.namelist()[0]) as f, open(destino, "wb") as o:
            o.write(f.read())
    print(f"  {fecha:%Y%m%d}  descargado")
    return destino


def descargar_rango(inicio: date, fin: date, destino_dir="data/raw") -> list[str]:
    """Descarga todos los dias del rango [inicio, fin] inclusive."""
    paths, f = [], inicio
    while f <= fin:
        paths.append(descargar_dia(f, destino_dir))
        f += timedelta(days=1)
    return paths


# --------------------------------------------------------------------------- #
# GDELT: carga de un dia
# --------------------------------------------------------------------------- #
def cargar_dia(path) -> pd.DataFrame:
    """Carga un CSV GDELT 1.0 (TSV sin cabecera) con tipos correctos."""
    df = pd.read_csv(
        path, sep="\t", header=None, names=COLUMNAS,
        dtype=str, na_values=[""], keep_default_na=False,
        quoting=3,  # csv.QUOTE_NONE: GDELT no usa comillas
    )
    for c in COLS_NUMERICAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# --------------------------------------------------------------------------- #
# S&P 500: descarga de Open/Close (resolucion diaria)
# --------------------------------------------------------------------------- #
def descargar_sp500(inicio: str, fin: str, cache="data/sp500.csv") -> pd.DataFrame:
    """Descarga Open/Close de ^GSPC en [inicio, fin) y cachea en disco.

    `fin` es exclusivo (convencion yfinance): usa el dia siguiente al ultimo deseado.
    Devuelve un DataFrame indexado por fecha (Timestamp) con columnas Open, Close.
    """
    cache = Path(cache)
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["Date"]).set_index("Date")
        return df[["Open", "Close"]]

    import yfinance as yf
    raw = yf.download(TICKER_SP500, start=inicio, end=fin, auto_adjust=False, progress=False)
    df = raw[["Open", "Close"]].copy()
    df.columns = ["Open", "Close"]
    df.index.name = "Date"
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(cache, index=False)
    return df
