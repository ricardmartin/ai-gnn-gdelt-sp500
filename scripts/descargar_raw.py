"""
Descarga masiva GDELT raw + finanzas. Ejecutar ANTES del notebook para
no bloquear el kernel durante 2-3 horas.

Uso:
    .venv/Scripts/python scripts/descargar_raw.py

Resumible: si un CSV ya existe, lo salta. Puede interrumpirse y reanudarse.
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.datos.descarga_gdelt import descargar_rango
from src.datos.descarga_financiero import descargar_sp500, descargar_vix, descargar_macro_fred


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    log = logging.getLogger("descargar_raw")

    fecha_ini = date.fromisoformat(config.FECHA_INICIO)
    fecha_fin = date.fromisoformat(config.FECHA_FIN)

    log.info("=" * 60)
    log.info("Descarga masiva GDELT + finanzas | %s -> %s", fecha_ini, fecha_fin)
    log.info("=" * 60)

    # 1. GDELT raw (resumible: salta CSVs ya en data/raw/)
    log.info("Descargando GDELT raw (esto puede tardar 2-3 h)...")
    rutas = descargar_rango(fecha_ini, fecha_fin)
    log.info("GDELT raw: %d CSVs disponibles", len(rutas))

    # 2. SP500 + VIX
    log.info("Descargando SP500...")
    precios = descargar_sp500(fecha_ini, fecha_fin)
    log.info("SP500: %d sesiones", len(precios))

    log.info("Descargando VIX...")
    vix = descargar_vix(fecha_ini, fecha_fin)
    log.info("VIX: %d puntos", len(vix))

    # 3. Macro FRED (opcional)
    try:
        log.info("Descargando macro FRED...")
        macro = descargar_macro_fred(fecha_ini, fecha_fin)
        log.info("Macro FRED: %d filas, cols=%s", len(macro), list(macro.columns))
    except Exception as e:
        log.warning("Macro FRED no disponible: %s", e)

    log.info("=" * 60)
    log.info("Descarga completa. Ahora puedes abrir el notebook y ejecutar.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
