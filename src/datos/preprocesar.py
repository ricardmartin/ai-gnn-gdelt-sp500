"""
Preprocesado de eventos GDELT.

Toma los CSVs crudos en `data/raw/`, los carga, filtra y agrega para producir
un DataFrame de eventos relevantes listo para construir el grafo.

Filtros aplicados:

1. Se descartan filas en las que NINGUNO de los dos actores pertenece al ROSTER
   (filtro OR: basta con que Actor1 O Actor2 sea un país relevante).
   Esto captura eventos como CHN→SYR donde China es el actor relevante aunque
   Siria no esté en el roster.
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

    Se leen del disco ÚNICAMENTE las columnas relevantes (usecols), en lugar de
    cargar las 58 como texto y recortar después. Esto reduce el consumo de RAM
    por fichero ~4-5x y evita la fragmentación de memoria al procesar miles de
    ficheros en bucle.
    """
    df = pd.read_csv(
        ruta,
        sep="\t",
        header=None,
        names=list(COLUMNAS_GDELT_1_0),
        usecols=list(COLUMNAS_RELEVANTES),
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
    Conserva eventos en los que AL MENOS UNO de los dos actores pertenece al
    ROSTER de países definido en `src/utils/paises.py` (filtro OR).

    Esto captura eventos donde un país del roster actúa sobre un tercero
    irrelevante (p.ej. CHN→SYR) o donde un tercero actúa sobre un país del
    roster (p.ej. SYR→CHN). Ambos aportan señal sobre CHN aunque SYR no
    esté en el roster.

    Cuando uno de los actores no está en el roster, su columna queda como NaN.
    Las funciones de agregación y grafo manejan correctamente estos NaN
    ignorando el extremo desconocido de la arista.

    Añade dos columnas auxiliares:
        pais_origen  -> id del nodo de Actor1 (NaN si no está en roster)
        pais_destino -> id del nodo de Actor2 (NaN si no está en roster)
    """
    df = df.copy()
    df["pais_origen"] = df["Actor1CountryCode"].map(COD_A_PAIS)
    df["pais_destino"] = df["Actor2CountryCode"].map(COD_A_PAIS)

    # OR: basta con que al menos un actor sea del roster.
    mask = df["pais_origen"].notna() | df["pais_destino"].notna()
    df_filt = df.loc[mask].copy()

    log.debug(
        "Filtro roster (OR): %d/%d eventos conservados (%.1f%%)",
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
    for i, ruta in enumerate(rutas):
        try:
            dfs.append(preprocesar_dia(ruta))
        except Exception as e:
            log.warning("Fallo procesando %s: %s", ruta.name, e)
        # Liberación periódica para que glibc devuelva memoria al sistema y no
        # se acumule fragmentación al procesar miles de ficheros.
        if (i + 1) % 200 == 0:
            import gc
            gc.collect()

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

    IMPORTANTE: esta función produce ÚNICAMENTE las ARISTAS país-país, para las
    que se necesitan los dos extremos en el roster. Los eventos de un solo actor
    (uno de pais_origen/pais_destino es NaN tras el filtro OR) NO generan arista
    y se descartan aquí. Esos eventos SÍ deben alimentar las features del nodo
    conocido; de eso se encarga `agregar_participacion_por_dia_y_pais`, que es
    la función que consume `calcular_features_countries` en grafo.py.

    Devuelve un DataFrame con columnas:
        fecha, pais_origen, pais_destino, quadclass,
        n_eventos, goldstein_medio, tono_medio, num_mentions_total
    """
    if df_eventos.empty:
        return pd.DataFrame()

    df = df_eventos.copy()
    df["quadclass"] = df["QuadClass"].astype(str)

    # Para las aristas necesitamos los dos extremos conocidos.
    df_aristas = df.dropna(subset=["pais_origen", "pais_destino"])

    if df_aristas.empty:
        return pd.DataFrame()

    grupos = df_aristas.groupby(
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


def agregar_participacion_por_dia_y_pais(df_eventos: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega los eventos a nivel (fecha, pais, rol, QuadClass) para las FEATURES
    DE NODO.

    A diferencia de `agregar_eventos_por_dia_y_par` (que solo conserva eventos
    con ambos extremos en el roster, porque construye aristas), aquí se cuenta
    la PARTICIPACIÓN de cada país en eventos, incluyendo los eventos en los que
    solo uno de los actores pertenece al roster (filtro OR del §4.1 del TFM).

    Cada evento se "despliega" en una o dos filas de participación según cuántos
    de sus actores estén en el roster:
        - CHN→SYR  -> una fila: (CHN, rol="origen")        [SYR no está]
        - SYR→CHN  -> una fila: (CHN, rol="destino")       [SYR no está]
        - USA→CHN  -> dos filas: (USA, "origen"), (CHN, "destino")

    De este modo un evento del tipo CHN→SYR, que no genera arista, sí contribuye
    a las features del nodo CHN, que es justo lo que el filtro OR pretende
    capturar y lo que el §4.3.2 describe como "el número de eventos en que
    participa" cada país.

    Devuelve un DataFrame con columnas:
        fecha, pais, rol, quadclass,
        n_eventos, goldstein_medio, tono_medio, num_mentions_total
    donde rol ∈ {"origen", "destino"}.
    """
    if df_eventos.empty:
        return pd.DataFrame()

    df = df_eventos.copy()
    df["quadclass"] = df["QuadClass"].astype(str)

    cols_evento = [
        "fecha", "pais", "rol", "quadclass",
        "GLOBALEVENTID", "GoldsteinScale", "AvgTone", "NumMentions",
    ]

    bloques: list[pd.DataFrame] = []
    for col_actor, rol in (("pais_origen", "origen"), ("pais_destino", "destino")):
        sub = df.dropna(subset=[col_actor]).copy()
        if sub.empty:
            continue
        sub = sub.rename(columns={col_actor: "pais"})
        sub["rol"] = rol
        bloques.append(sub[cols_evento])

    if not bloques:
        return pd.DataFrame()

    participacion = pd.concat(bloques, ignore_index=True)

    agregado = participacion.groupby(
        ["fecha", "pais", "rol", "quadclass"],
        observed=True,
    ).agg(
        n_eventos=("GLOBALEVENTID", "size"),
        goldstein_medio=("GoldsteinScale", "mean"),
        tono_medio=("AvgTone", "mean"),
        num_mentions_total=("NumMentions", "sum"),
    ).reset_index()

    return agregado


def _parquet_disponible() -> bool:
    """True si hay un motor de Parquet instalado (pyarrow o fastparquet)."""
    for mod in ("pyarrow", "fastparquet"):
        try:
            __import__(mod)
            return True
        except Exception:
            continue
    return False


def _guardar_df(df: pd.DataFrame, ruta_sin_ext: Path) -> Path:
    """Guarda en Parquet si se puede; si no, cae a pickle. Devuelve la ruta."""
    if _parquet_disponible():
        ruta = ruta_sin_ext.with_suffix(".parquet")
        df.to_parquet(ruta, index=False)
    else:
        ruta = ruta_sin_ext.with_suffix(".pkl")
        df.to_pickle(ruta)
    return ruta


def _existe_tramo(ruta_sin_ext: Path) -> bool:
    """True si el tramo ya está en disco en cualquiera de los dos formatos."""
    return (ruta_sin_ext.with_suffix(".parquet").exists()
            or ruta_sin_ext.with_suffix(".pkl").exists())


def _leer_subdir(d: Path) -> pd.DataFrame:
    """Lee y concatena todos los .parquet (o .pkl) de una carpeta."""
    ficheros = sorted(d.glob("*.parquet")) or sorted(d.glob("*.pkl"))
    if not ficheros:
        return pd.DataFrame()
    leer = pd.read_parquet if ficheros[0].suffix == ".parquet" else pd.read_pickle
    return pd.concat([leer(f) for f in ficheros], ignore_index=True)


def preprocesar_y_agregar_por_tramos(
    rutas: list[Path],
    dir_salida: Path | str,
    dias_por_tramo: int = 180,
    sobrescribir: bool = False,
) -> None:
    """
    Procesa los CSV de GDELT POR TRAMOS para acotar el uso de RAM.

    En lugar de cargar todos los eventos de todo el rango en memoria a la vez
    (lo que desborda la RAM con muchos años), se procesa el rango en bloques de
    `dias_por_tramo` ficheros. De cada bloque se calculan los agregados (aristas
    y participación) y se guardan en disco (Parquet); después se libera la RAM
    antes de pasar al siguiente bloque. Así el pico de memoria es el de UN tramo,
    no el del rango completo, sea de 3 o de 20 años.

    Es RESUMIBLE: si los Parquet de un tramo ya existen y `sobrescribir=False`,
    ese tramo se salta. Útil si Colab se desconecta a medias.

    EQUIVALENCIA: el resultado es idéntico a procesar todo de golpe, porque cada
    día pertenece a un único tramo y las agregaciones son por día (no cruzan
    días). Ningún grupo (fecha, país, ...) se parte entre dos tramos.

    Args:
        rutas: lista de rutas a los CSV diarios (se ordenan por nombre, que en
            GDELT es AAAAMMDD, garantizando orden temporal).
        dir_salida: carpeta donde guardar los agregados (p.ej. una carpeta de
            Google Drive). Se crean dentro subcarpetas `aristas/` y
            `participacion/`.
        dias_por_tramo: nº de ficheros por bloque. Bájalo si aún vas justo de
            RAM, súbelo si te sobra y quieres menos ficheros.
        sobrescribir: si True, reprocesa tramos aunque ya estén en disco.
    """
    import gc
    import math

    dir_salida = Path(dir_salida)
    (dir_salida / "aristas").mkdir(parents=True, exist_ok=True)
    (dir_salida / "participacion").mkdir(parents=True, exist_ok=True)

    rutas = sorted(rutas, key=lambda p: p.name)
    n_tramos = math.ceil(len(rutas) / dias_por_tramo)
    log.info("Procesando %d ficheros en %d tramos de %d días",
             len(rutas), n_tramos, dias_por_tramo)

    for k in range(n_tramos):
        tramo = rutas[k * dias_por_tramo:(k + 1) * dias_por_tramo]
        base_aristas = dir_salida / "aristas" / f"tramo_{k:04d}"
        base_part = dir_salida / "participacion" / f"tramo_{k:04d}"

        if _existe_tramo(base_aristas) and _existe_tramo(base_part) and not sobrescribir:
            log.info("Tramo %d/%d ya en disco, se salta", k + 1, n_tramos)
            continue

        df_ev = preprocesar_rango(tramo)
        agg_e = agregar_eventos_por_dia_y_par(df_ev)
        agg_p = agregar_participacion_por_dia_y_pais(df_ev)

        _guardar_df(agg_e, base_aristas)
        _guardar_df(agg_p, base_part)

        log.info("Tramo %d/%d: %d aristas, %d participaciones -> guardado",
                 k + 1, n_tramos, len(agg_e), len(agg_p))

        # Liberar RAM antes del siguiente tramo.
        del df_ev, agg_e, agg_p
        gc.collect()


def cargar_agregados_de_disco(
    dir_salida: Path | str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lee y concatena todos los agregados por tramos guardados en disco por
    `preprocesar_y_agregar_por_tramos`.

    Devuelve (df_aristas, df_participacion), ya listos para el dataset. Estos
    DataFrames son el "concentrado" pequeño: caben de sobra en RAM aunque el
    rango original fuera de 20 años.
    """
    dir_salida = Path(dir_salida)

    df_aristas = _leer_subdir(dir_salida / "aristas")
    df_participacion = _leer_subdir(dir_salida / "participacion")
    log.info("Agregados cargados de disco: %d aristas, %d participaciones",
             len(df_aristas), len(df_participacion))
    return df_aristas, df_participacion
