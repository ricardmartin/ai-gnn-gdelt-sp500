"""
Descarga de datos financieros: S&P 500 y variables macroeconómicas.

- S&P 500: precios diarios (yfinance, ticker ^GSPC).
- Macro: VIX, tipos de la Fed, treasuries 10Y, etc. (FRED vía pandas-datareader
  o yfinance según disponibilidad).

Las series se cachean en `data/processed/` para no depender de la red en cada
ejecución.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.utils.logging import obtener_logger
from config import DIR_PROCESSED

log = obtener_logger(__name__)


# Tickers de yfinance usados por defecto.
TICKER_SP500 = "^GSPC"
TICKER_VIX = "^VIX"
TICKER_DXY = "DX-Y.NYB"   # índice del dólar

# Series macro de FRED (códigos oficiales).
SERIES_FRED: dict[str, str] = {
    "fed_funds": "DFF",       # Federal Funds Rate (diario)
    "treasury_10y": "DGS10",  # 10-Year Treasury Yield (diario)
    "cpi": "CPIAUCSL",        # CPI mensual
    "unemployment": "UNRATE", # tasa de paro mensual
}


def descargar_sp500(
    fecha_inicio: date,
    fecha_fin: date,
    forzar: bool = False,
) -> pd.DataFrame:
    """
    Descarga precios diarios del S&P 500.

    Returns:
        DataFrame con índice de fechas y columnas Open, High, Low, Close, Volume.
    """
    cache = DIR_PROCESSED / f"sp500_{fecha_inicio:%Y%m%d}_{fecha_fin:%Y%m%d}.csv"
    if cache.exists() and not forzar:
        log.debug("Usando caché: %s", cache.name)
        return pd.read_csv(cache, index_col=0, parse_dates=True)

    # Import diferido: yfinance no es necesario hasta que se llame esta función.
    import yfinance as yf

    log.info("Descargando S&P 500 desde %s hasta %s", fecha_inicio, fecha_fin)
    df = yf.download(
        TICKER_SP500,
        start=fecha_inicio.isoformat(),
        end=fecha_fin.isoformat(),
        progress=False,
        auto_adjust=False,
    )

    # yfinance puede devolver columnas multinivel (Price, Ticker). Aplanar.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "fecha"
    df.to_csv(cache)
    log.info("Guardado en caché: %s", cache.name)
    return df


def descargar_vix(
    fecha_inicio: date,
    fecha_fin: date,
    forzar: bool = False,
) -> pd.Series:
    """Descarga el VIX como serie diaria de cierres."""
    cache = DIR_PROCESSED / f"vix_{fecha_inicio:%Y%m%d}_{fecha_fin:%Y%m%d}.csv"
    if cache.exists() and not forzar:
        return pd.read_csv(cache, index_col=0, parse_dates=True).squeeze("columns")

    import yfinance as yf

    log.info("Descargando VIX desde %s hasta %s", fecha_inicio, fecha_fin)
    df = yf.download(
        TICKER_VIX,
        start=fecha_inicio.isoformat(),
        end=fecha_fin.isoformat(),
        progress=False,
        auto_adjust=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    serie = df["Close"].rename("vix")
    serie.to_csv(cache)
    return serie


def descargar_macro_fred(
    fecha_inicio: date,
    fecha_fin: date,
    forzar: bool = False,
) -> pd.DataFrame:
    """
    Descarga variables macroeconómicas de FRED.

    Devuelve un DataFrame con columnas según `SERIES_FRED`, alineadas por fecha
    diaria (las series mensuales se forward-fillean al uso diario).
    """
    cache = DIR_PROCESSED / f"macro_fred_{fecha_inicio:%Y%m%d}_{fecha_fin:%Y%m%d}.csv"
    if cache.exists() and not forzar:
        return pd.read_csv(cache, index_col=0, parse_dates=True)

    # Import diferido.
    from pandas_datareader import data as pdr  # type: ignore

    log.info("Descargando series FRED")
    series: dict[str, pd.Series] = {}
    for nombre, codigo in SERIES_FRED.items():
        try:
            s = pdr.DataReader(codigo, "fred", fecha_inicio, fecha_fin)
            series[nombre] = s.iloc[:, 0]
        except Exception as e:
            log.warning("No se pudo descargar %s (%s): %s", nombre, codigo, e)

    if not series:
        log.warning("Ninguna serie FRED descargada; devuelvo DataFrame vacío")
        return pd.DataFrame()

    df = pd.concat(series.values(), axis=1, keys=series.keys())
    df = df.resample("D").ffill()  # alineación diaria para las series mensuales
    df.index.name = "fecha"
    df.to_csv(cache)
    return df
