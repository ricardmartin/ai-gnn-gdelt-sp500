"""
Cálculo de la etiqueta triclase del S&P 500 y alineación temporal con grafos GDELT.

Etiqueta: para predecir el día de mercado `t+1`, se calcula el retorno
close-to-close del SP500 entre los días t y t+1 y se discretiza en tres clases
{baja=0, neutro=1, sube=2} según el umbral definido en `config.py`.

Alineación temporal (anti-leakage): la información geopolítica usada para
predecir el día t+1 debe limitarse a los eventos GDELT publicados ANTES del
cierre del mercado del día t. Eventos posteriores se asignan al siguiente día.

ANTI-LEAKAGE DE ETIQUETAS (corrección metodológica):
Los umbrales que separan las clases (la sigma en modo "sigma", los percentiles
en modo "terciles") NO deben calcularse sobre toda la serie, porque eso usa
información del futuro para definir las fronteras de clase del pasado. El flujo
correcto es por fold:

    umbrales = calcular_umbrales(retornos[idx_train])   # SOLO train
    clases   = aplicar_umbrales(retornos, umbrales)      # train y test con el
                                                         # umbral "congelado"

`construir_etiquetas_diarias` sigue calculando una clase global, pero esa clase
es PROVISIONAL: sirve para el EDA y para alinear fechas. El entrenamiento
(`entrenar_un_fold`) recalcula las clases por fold con `clases_para_fold`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.logging import obtener_logger
from config import (
    MODO_ETIQUETA, UMBRAL_NEUTRO, UMBRAL_SIGMA,
    UMBRAL_Q_INF, UMBRAL_Q_SUP,
)

log = obtener_logger(__name__)


CLASE_BAJA = 0
CLASE_NEUTRO = 1
CLASE_SUBE = 2


# ---------------------------------------------------------------------------
# Umbrales de discretización (calculados SOLO con datos de train)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Umbrales:
    """
    Fronteras de clase 'congeladas', calculadas exclusivamente con el train.

    Para modos "fijo" y "sigma": frontera simétrica en ±`umbral`
    (q_inf = -umbral, q_sup = +umbral).
    Para modo "terciles": q_inf = percentil 33 y q_sup = percentil 66 del train.
    """
    modo: str
    q_inf: float
    q_sup: float

    def resumen(self) -> str:
        return f"modo={self.modo} | q_inf={self.q_inf:+.5f} | q_sup={self.q_sup:+.5f}"


def _config_default(nombre: str):
    """Lee el valor actual del config (respeta overrides en runtime)."""
    import config
    return getattr(config, nombre)


def calcular_umbrales(
    retornos_train,
    modo: str = None,
    umbral_fijo: float = None,
    umbral_sigma: float = None,
    q_inf_pct: float = None,
    q_sup_pct: float = None,
) -> Umbrales:
    """
    Calcula las fronteras de clase usando ÚNICAMENTE retornos del train.

    Args:
        retornos_train: array/Serie de retornos del conjunto de ENTRENAMIENTO.
        modo: "fijo", "sigma", "terciles" o "asimetrico".
        umbral_fijo: usado si modo="fijo".
        umbral_sigma: multiplicador de la sigma si modo="sigma".
        q_inf_pct: percentil inferior (0-1) si modo="asimetrico".
        q_sup_pct: percentil superior (0-1) si modo="asimetrico".

    Returns:
        Umbrales congelados, aplicables a cualquier conjunto (train o test).
    """
    if modo is None:         modo = _config_default("MODO_ETIQUETA")
    if umbral_fijo is None:  umbral_fijo = _config_default("UMBRAL_NEUTRO")
    if umbral_sigma is None: umbral_sigma = _config_default("UMBRAL_SIGMA")
    if q_inf_pct is None:    q_inf_pct = _config_default("UMBRAL_Q_INF")
    if q_sup_pct is None:    q_sup_pct = _config_default("UMBRAL_Q_SUP")

    r = np.asarray(retornos_train, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) == 0:
        raise ValueError("calcular_umbrales: retornos_train vacío o todo NaN")

    if modo == "fijo":
        u = float(umbral_fijo)
        return Umbrales(modo=modo, q_inf=-u, q_sup=u)

    if modo == "sigma":
        sigma = float(np.std(r))
        u = float(umbral_sigma) * sigma
        return Umbrales(modo=modo, q_inf=-u, q_sup=u)

    if modo == "terciles":
        q33, q66 = np.quantile(r, [1.0 / 3.0, 2.0 / 3.0])
        return Umbrales(modo=modo, q_inf=float(q33), q_sup=float(q66))

    if modo == "asimetrico":
        if not (0.0 < q_inf_pct < q_sup_pct < 1.0):
            raise ValueError(
                f"asimetrico requiere 0 < q_inf_pct < q_sup_pct < 1, "
                f"recibido q_inf_pct={q_inf_pct}, q_sup_pct={q_sup_pct}"
            )
        q_lo, q_hi = np.quantile(r, [q_inf_pct, q_sup_pct])
        return Umbrales(modo=modo, q_inf=float(q_lo), q_sup=float(q_hi))

    raise ValueError(f"Modo de etiqueta desconocido: {modo}")


def aplicar_umbrales(retornos, umbrales: Umbrales) -> np.ndarray:
    """
    Discretiza retornos con unos umbrales ya congelados.

    Args:
        retornos: array/Serie de retornos (puede incluir NaN -> clase -1).
        umbrales: fronteras calculadas con `calcular_umbrales` sobre el train.

    Returns:
        Array int64 de clases {0=baja, 1=neutro, 2=sube}; -1 donde el retorno
        es NaN (para descartar).
    """
    r = np.asarray(retornos, dtype=float)
    clases = np.full(len(r), CLASE_NEUTRO, dtype=np.int64)
    clases[r < umbrales.q_inf] = CLASE_BAJA
    clases[r > umbrales.q_sup] = CLASE_SUBE
    clases[np.isnan(r)] = -1
    return clases


def clases_para_fold(
    retornos_por_indice,
    idx_train,
    modo: str = None,
    umbral_fijo: float = None,
    umbral_sigma: float = None,
    q_inf_pct: float = None,
    q_sup_pct: float = None,
) -> tuple[np.ndarray, Umbrales]:
    """
    Calcula las clases de TODO el dataset para un fold concreto, con umbrales
    derivados exclusivamente de los índices de train de ese fold.

    Es la función que deben usar tanto la HGNN como los baselines para que
    todos los modelos compitan con exactamente las mismas etiquetas.

    Args:
        retornos_por_indice: array de retornos de longitud len(dataset), en el
            mismo orden de índices que usa el dataset.
        idx_train: índices de train del fold.

    Returns:
        (clases, umbrales): array int64 de longitud len(dataset) y los
        umbrales usados (para logging/trazabilidad).
    """
    retornos_por_indice = np.asarray(retornos_por_indice, dtype=float)
    idx_train = np.asarray(idx_train, dtype=int)
    umbrales = calcular_umbrales(
        retornos_por_indice[idx_train],
        modo=modo, umbral_fijo=umbral_fijo, umbral_sigma=umbral_sigma,
        q_inf_pct=q_inf_pct, q_sup_pct=q_sup_pct,
    )
    clases = aplicar_umbrales(retornos_por_indice, umbrales)
    log.info("Etiquetas por fold: %s", umbrales.resumen())
    dist = np.bincount(clases[idx_train][clases[idx_train] >= 0], minlength=3)
    log.info("Distribución en train del fold (baja/neutro/sube): %s", dist.tolist())
    return clases, umbrales


# ---------------------------------------------------------------------------
# API previa (se mantiene por compatibilidad; la clase global es PROVISIONAL)
# ---------------------------------------------------------------------------

def calcular_retornos(precios_sp500: pd.DataFrame) -> pd.Series:
    """
    Calcula el retorno close-to-close diario del S&P 500.

    Args:
        precios_sp500: DataFrame con índice de fechas y columna 'Close'.

    Returns:
        Serie de retornos diarios (NaN para el primer día).
    """
    if "Close" not in precios_sp500.columns:
        raise ValueError("Se esperaba columna 'Close' en los precios del SP500")
    close = precios_sp500["Close"].astype(float)
    return close.pct_change().rename("retorno")


def discretizar_retornos(
    retornos: pd.Series,
    modo: str = None,
    umbral_fijo: float = None,
    umbral_sigma: float = None,
) -> pd.Series:
    """
    Discretiza retornos continuos en {baja=0, neutro=1, sube=2}.

    ATENCIÓN: esta función calcula los umbrales sobre TODA la serie que recibe.
    Solo debe usarse para EDA o para etiquetas provisionales. Para entrenar y
    evaluar hay que usar `clases_para_fold` (umbral solo del train del fold).
    """
    r = retornos.dropna()
    umbrales = calcular_umbrales(
        r.values, modo=modo, umbral_fijo=umbral_fijo, umbral_sigma=umbral_sigma,
    )
    log.info("Discretización PROVISIONAL (serie completa): %s", umbrales.resumen())
    clases = aplicar_umbrales(retornos.values, umbrales)
    return pd.Series(clases, index=retornos.index, dtype="int64")


def construir_etiquetas_diarias(precios_sp500: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el DataFrame de etiquetas usado durante el entrenamiento.

    Cada fila representa una sesión de mercado t+1 con su etiqueta. La columna
    `fecha_grafo` indica qué día se debe usar para construir el grafo predictor
    (= sesión anterior, antes del cierre).

    NOTA ANTI-LEAKAGE: la columna `clase` que devuelve esta función es
    PROVISIONAL (umbral calculado sobre toda la serie) y sirve solo para EDA y
    alineación de fechas. Durante el entrenamiento, `entrenar_un_fold` la
    sustituye por las clases del fold (umbral solo del train) si recibe
    `retornos_por_indice`. La columna `retorno` es la fuente de verdad.

    Devuelve:
        DataFrame con columnas
            fecha_grafo (date)       -> qué grafo se construye
            fecha_target (date)      -> qué sesión se predice (siguiente día hábil)
            retorno (float)          -> retorno close-to-close
            clase (int)              -> 0=baja, 1=neutro, 2=sube (PROVISIONAL)
    """
    retornos = calcular_retornos(precios_sp500)
    clases = discretizar_retornos(retornos)

    df = pd.DataFrame({
        "fecha_target": retornos.index,
        "retorno": retornos.values,
        "clase": clases.values,
    })
    # El grafo predictor es el del día hábil ANTERIOR a la sesión predicha.
    # En la práctica, "día anterior" se calcula con shift (1 sesión bursátil).
    df["fecha_grafo"] = df["fecha_target"].shift(1)

    # Descartar filas sin grafo previo (primera) y sin retorno (NaN inicial).
    df = df.dropna(subset=["fecha_grafo", "retorno"])
    df = df[df["clase"] != -1].reset_index(drop=True)

    # Convertir a fechas (sin hora) para alinear con los días GDELT.
    df["fecha_target"] = pd.to_datetime(df["fecha_target"]).dt.normalize()
    df["fecha_grafo"] = pd.to_datetime(df["fecha_grafo"]).dt.normalize()
    df["clase"] = df["clase"].astype("int64")

    log.info("Etiquetas construidas: %d sesiones", len(df))
    log.info(
        "Distribución de clases (PROVISIONAL, se recalcula por fold):\n%s",
        df["clase"].value_counts().sort_index(),
    )
    return df


def mascara_historial_gdelt_completo(
    fechas_grafo,
    fechas_faltantes,
    ventana_dias: int,
) -> np.ndarray:
    """
    Indica qué grafos tienen completa su ventana histórica GDELT.

    Una fecha es inválida si cualquier día ausente cae dentro del intervalo
    inclusivo [`fecha_grafo - ventana_dias`, `fecha_grafo`]. Es preferible
    excluir esas muestras a interpretar un día no publicado como cero eventos.
    """
    if int(ventana_dias) < 0:
        raise ValueError("ventana_dias no puede ser negativo")

    fechas = pd.DatetimeIndex(pd.to_datetime(fechas_grafo)).normalize()
    faltantes = pd.DatetimeIndex(pd.to_datetime(list(fechas_faltantes))).normalize()
    faltantes = faltantes.dropna().unique().sort_values()

    if len(faltantes) == 0:
        return np.ones(len(fechas), dtype=bool)

    fechas_d = fechas.to_numpy(dtype="datetime64[D]")
    faltantes_d = faltantes.to_numpy(dtype="datetime64[D]")
    inicios = fechas_d - np.timedelta64(int(ventana_dias), "D")
    izquierda = np.searchsorted(faltantes_d, inicios, side="left")
    derecha = np.searchsorted(faltantes_d, fechas_d, side="right")
    return (izquierda == derecha) & ~np.isnat(fechas_d)


def aplicar_corte_horario(
    df_eventos: pd.DataFrame,
    zona_mercado: str = None,
    hora_cierre_local: int = None,
) -> pd.DataFrame:
    """
    Asigna cada evento GDELT al día efectivo según el cierre local de Nueva
    York. La conversión de zona horaria resuelve automáticamente el DST.

    Eventos con DATEADDED posterior al cierre se asignan al día siguiente
    (los usará el grafo predictor de la sesión t+2, no la t+1).

    Args:
        df_eventos: DataFrame con columnas SQLDATE y DATEADDED. DATEADDED se
            interpreta como UTC, que es la convención de GDELT.
        zona_mercado: zona IANA; por defecto `config.ZONA_HORARIA_MERCADO`.
        hora_cierre_local: hora local de cierre; por defecto la configurada.

    Returns:
        Mismo DataFrame con columna `fecha_grafo` que indica a qué día
        contribuye cada evento.
    """
    if "DATEADDED" not in df_eventos.columns:
        raise ValueError("aplicar_corte_horario requiere la columna DATEADDED")

    if zona_mercado is None:
        zona_mercado = _config_default("ZONA_HORARIA_MERCADO")
    if hora_cierre_local is None:
        hora_cierre_local = _config_default("HORA_CIERRE_MERCADO_LOCAL")
    if not (0 <= int(hora_cierre_local) <= 23):
        raise ValueError("hora_cierre_local debe estar entre 0 y 23")

    df = df_eventos.copy()
    # DATEADDED tiene formato YYYYMMDDHHMMSS en GDELT 1.0 desde 2013.
    # Antes de 2013 sólo hay YYYYMMDD, en cuyo caso el corte no es aplicable
    # y se usa SQLDATE directamente.
    valores = df["DATEADDED"].astype("string").str.strip()
    ts_added = pd.to_datetime(
        valores, format="%Y%m%d%H%M%S", errors="coerce", utc=True,
    )
    ts_added = ts_added.fillna(
        pd.to_datetime(valores, format="%Y%m%d", errors="coerce", utc=True)
    )

    ts_local = ts_added.dt.tz_convert(zona_mercado)
    fecha_local = ts_local.dt.tz_localize(None).dt.normalize()
    despues_cierre = ts_local.dt.hour >= int(hora_cierre_local)
    fecha_efectiva = fecha_local + pd.to_timedelta(
        despues_cierre.fillna(False).astype("int64"), unit="D",
    )

    # Para timestamps inválidos se conserva SQLDATE como fallback trazable.
    if "SQLDATE" in df.columns:
        fecha_sql = pd.to_datetime(
            df["SQLDATE"].astype("string"), format="%Y%m%d", errors="coerce",
        )
        fecha_efectiva = fecha_efectiva.fillna(fecha_sql)

    df["fecha_grafo"] = fecha_efectiva
    return df
