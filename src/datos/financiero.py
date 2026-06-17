"""Fase 2: datos del S&P 500 y construccion de la variable objetivo.

Descarga apertura/cierre del indice (^GSPC) y deriva la etiqueta triclase que el
modelo predice ANTES de la apertura de cada sesion:

    label(D) = signo( close_D - close_{D-1} )   (rendimiento close-to-close)
      sube   si  ret > +tau
      baja   si  ret < -tau
      neutro si  |ret| <= tau           (tau por defecto = 0.1%)

Como el snapshot del grafo esta indexado por el dia GDELT (el dia de los eventos),
se alinea cada dia-predictor g con su siguiente sesion de mercado D = next_trading(g),
de modo que: eventos de g  ->  predicen el movimiento de D.
"""
from __future__ import annotations

import pandas as pd

from .cargar import descargar_sp500

CLASES = {0: "baja", 1: "neutro", 2: "sube"}
CLASE_A_ID = {"baja": 0, "neutro": 1, "sube": 2}


def construir_labels(sp500: pd.DataFrame, tau: float = 0.001) -> pd.DataFrame:
    """Anade prev_close, ret close-to-close y la clase triclase por sesion.

    La primera fila queda sin prev_close (NaN) y por tanto sin clase: no es
    predecible con los datos disponibles.
    """
    df = sp500.sort_index().copy()
    df["prev_close"] = df["Close"].shift(1)
    df["ret"] = df["Close"] / df["prev_close"] - 1.0

    def clasificar(r):
        if pd.isna(r):
            return None
        if r > tau:
            return "sube"
        if r < -tau:
            return "baja"
        return "neutro"

    df["clase"] = df["ret"].map(clasificar)
    df["y"] = df["clase"].map(lambda c: CLASE_A_ID.get(c) if c is not None else None)
    return df


def alinear_predictor_mercado(gdelt_dates, labels: pd.DataFrame) -> pd.DataFrame:
    """Mapea cada dia-predictor (GDELT) a su siguiente sesion de mercado y su etiqueta.

    `gdelt_dates`: iterable de strings 'YYYYMMDD' (los dias de eventos disponibles).
    Devuelve un DataFrame [gdelt_date, market_date, Open, Close, prev_close, ret, clase, y].
    """
    market_idx = labels.index
    filas = []
    for g in sorted(gdelt_dates):
        g_ts = pd.Timestamp(g)
        futuras = market_idx[market_idx > g_ts]
        if len(futuras) == 0:
            continue  # no hay sesion posterior cargada
        D = futuras[0]
        fila = labels.loc[D]
        filas.append({
            "gdelt_date": g,
            "market_date": D.strftime("%Y-%m-%d"),
            "Open": fila["Open"],
            "Close": fila["Close"],
            "prev_close": fila["prev_close"],
            "ret": fila["ret"],
            "clase": fila["clase"],
            "y": fila["y"],
        })
    out = pd.DataFrame(filas)
    return out


def construir_targets(gdelt_dates, inicio: str, fin: str, tau: float = 0.001,
                      cache="data/sp500.csv") -> pd.DataFrame:
    """Atajo: descarga SP500, calcula labels y alinea con los dias GDELT dados."""
    sp = descargar_sp500(inicio, fin, cache=cache)
    labels = construir_labels(sp, tau=tau)
    return alinear_predictor_mercado(gdelt_dates, labels)


if __name__ == "__main__":
    from pathlib import Path as _P
    dias_gdelt = sorted(p.name[:8] for p in _P("data/raw").glob("2022*.export.CSV"))
    tgt = construir_targets(dias_gdelt, "2022-02-09", "2022-02-26", tau=0.001)
    print("Targets (dia GDELT -> sesion de mercado predicha):\n")
    cols = ["gdelt_date", "market_date", "prev_close", "Close", "ret", "clase", "y"]
    print(tgt[cols].round(4).to_string(index=False))
    print("\nReparto de clases:", tgt["clase"].value_counts().to_dict())
