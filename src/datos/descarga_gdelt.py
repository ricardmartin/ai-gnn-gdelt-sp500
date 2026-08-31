"""
Descarga de GDELT 1.0 Events.

GDELT 1.0 publica un fichero CSV por día (o por mes/año para fechas
históricas antiguas), comprimido en ZIP, en:

    http://data.gdeltproject.org/events/{YYYYMMDD}.export.CSV.zip

Cada fichero contiene un esquema fijo de 58 columnas sin cabecera. Este
módulo descarga los CSV crudos a `data/raw/` y los descomprime; el filtrado
y la selección de columnas se hacen después en `preprocesar.py`.
"""

from __future__ import annotations

import io
import os
import urllib.request
import urllib.error
import zipfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from src.utils.logging import obtener_logger
from config import DIR_RAW

log = obtener_logger(__name__)

# URL base del repositorio público de GDELT 1.0 Events (formato diario).
_BASE_URL_DIARIO = "http://data.gdeltproject.org/events"


@dataclass(frozen=True)
class CoberturaGDELT:
    """Resultado auditable de la cobertura diaria disponible en disco."""

    fecha_inicio: date
    fecha_fin: date
    rutas: tuple[Path, ...]
    faltantes: tuple[date, ...]
    vacios: tuple[date, ...]

    @property
    def completa(self) -> bool:
        return not self.faltantes and not self.vacios

    @property
    def dias_esperados(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days + 1

    def resumen(self) -> str:
        return (
            f"{len(self.rutas)}/{self.dias_esperados} días válidos | "
            f"faltantes={len(self.faltantes)} | vacíos={len(self.vacios)}"
        )


def auditar_cobertura_local(
    fecha_inicio: date,
    fecha_fin: date,
    directorio: Path | str | None = None,
) -> CoberturaGDELT:
    """Comprueba cada fecha esperada; no usa heurísticas por número de archivos."""
    if fecha_fin < fecha_inicio:
        raise ValueError("fecha_fin debe ser ≥ fecha_inicio")

    directorio = Path(directorio) if directorio is not None else DIR_RAW
    rutas: list[Path] = []
    faltantes: list[date] = []
    vacios: list[date] = []
    fecha = fecha_inicio
    while fecha <= fecha_fin:
        ruta = directorio / f"{fecha:%Y%m%d}.export.CSV"
        if not ruta.exists():
            faltantes.append(fecha)
        elif ruta.stat().st_size == 0:
            vacios.append(fecha)
        else:
            rutas.append(ruta)
        fecha += timedelta(days=1)

    return CoberturaGDELT(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        rutas=tuple(rutas),
        faltantes=tuple(faltantes),
        vacios=tuple(vacios),
    )


def _ruta_destino(fecha: date) -> Path:
    """Ruta local donde se guarda el CSV descomprimido para una fecha dada."""
    return DIR_RAW / f"{fecha:%Y%m%d}.export.CSV"


def descargar_dia(fecha: date, sobrescribir: bool = False) -> Path | None:
    """
    Descarga el CSV diario de GDELT 1.0 correspondiente a `fecha`.

    Args:
        fecha: fecha del día a descargar.
        sobrescribir: si False (por defecto), no vuelve a descargar el fichero
            si ya existe en disco.

    Returns:
        Ruta al CSV descomprimido en `data/raw/`. None si el fichero no existe
        en el servidor (algunos días tempranos pueden faltar).
    """
    destino = _ruta_destino(fecha)

    if destino.exists() and not sobrescribir:
        log.debug("Ya existe: %s", destino.name)
        return destino

    nombre_csv = f"{fecha:%Y%m%d}.export.CSV"
    url = f"{_BASE_URL_DIARIO}/{nombre_csv}.zip"

    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            contenido = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.warning("No existe en el servidor: %s", url)
            return None
        raise
    except urllib.error.URLError as e:
        log.error("Fallo de red descargando %s: %s", url, e)
        raise

    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        nombre_interno = z.namelist()[0]
        with z.open(nombre_interno) as f_in, open(destino, "wb") as f_out:
            f_out.write(f_in.read())

    log.info("Descargado: %s", destino.name)
    return destino


def descargar_rango(
    fecha_inicio: date,
    fecha_fin: date,
    sobrescribir: bool = False,
    exigir_completo: bool = False,
) -> list[Path]:
    """
    Descarga todos los días entre `fecha_inicio` y `fecha_fin` (ambas incluidas).

    Si un día no existe en el servidor, lo omite y continúa. Con
    `exigir_completo=True`, los 404 confirmados también se consideran una
    ausencia explicada; solo se falla por huecos no confirmados o archivos
    locales vacíos.

    Returns:
        Lista de rutas a los CSVs descargados (omitiendo los que faltan).
    """
    if fecha_fin < fecha_inicio:
        raise ValueError("fecha_fin debe ser ≥ fecha_inicio")

    rutas: list[Path] = []
    no_disponibles_404: list[date] = []
    n_dias = (fecha_fin - fecha_inicio).days + 1
    log.info("Descargando GDELT desde %s hasta %s (%d días)",
             fecha_inicio, fecha_fin, n_dias)

    fecha = fecha_inicio
    while fecha <= fecha_fin:
        ruta = descargar_dia(fecha, sobrescribir=sobrescribir)
        if ruta is not None:
            rutas.append(ruta)
        else:
            # descargar_dia solo devuelve None cuando el servidor responde 404.
            no_disponibles_404.append(fecha)
        fecha += timedelta(days=1)

    cobertura = auditar_cobertura_local(fecha_inicio, fecha_fin)
    log.info("Descarga completada: %s", cobertura.resumen())
    confirmados_404 = set(no_disponibles_404)
    faltantes_no_confirmados = [
        fecha for fecha in cobertura.faltantes if fecha not in confirmados_404
    ]
    if exigir_completo and (faltantes_no_confirmados or cobertura.vacios):
        muestra = [
            f.isoformat()
            for f in (*faltantes_no_confirmados, *cobertura.vacios)[:10]
        ]
        raise RuntimeError(
            "Cobertura GDELT con huecos no explicados tras la descarga: "
            f"{cobertura.resumen()} | muestra={muestra}"
        )
    if cobertura.faltantes:
        log.warning(
            "Se continúa con %d días ausentes confirmados como 404; "
            "las ventanas afectadas deben excluirse del experimento.",
            len(cobertura.faltantes),
        )
    return list(cobertura.rutas)


# Esquema oficial de GDELT 1.0 Events (58 columnas, sin cabecera).
# Se referencia desde preprocesar.py para nombrar las columnas al leer.
COLUMNAS_GDELT_1_0: tuple[str, ...] = (
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
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
)

# Columnas numéricas que se deben castear a float al cargar el CSV.
COLUMNAS_NUMERICAS: tuple[str, ...] = (
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
)

# Columnas relevantes para el TFM (resto se descarta).
COLUMNAS_RELEVANTES: tuple[str, ...] = (
    "GLOBALEVENTID", "SQLDATE", "DATEADDED",
    "Actor1CountryCode", "Actor2CountryCode",
    "EventCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "AvgTone",
    "NumMentions", "NumSources", "NumArticles",
)
