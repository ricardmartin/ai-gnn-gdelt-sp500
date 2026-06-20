"""
Configuración de logging consistente para todo el proyecto.

Uso típico desde otros módulos:

    from src.utils.logging import obtener_logger
    log = obtener_logger(__name__)
    log.info("Mensaje")
"""

import logging
import sys
from pathlib import Path


_CONFIGURADO = False


def configurar_logging(nivel: str = "INFO", archivo: Path | None = None) -> None:
    """
    Configura el logging raíz una sola vez.

    Args:
        nivel: nivel mínimo a mostrar (DEBUG, INFO, WARNING, ERROR).
        archivo: si se indica, también vuelca los logs a este fichero.
    """
    global _CONFIGURADO
    if _CONFIGURADO:
        return

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if archivo is not None:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(archivo, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    _CONFIGURADO = True


def obtener_logger(nombre: str) -> logging.Logger:
    """Devuelve un logger configurado de forma consistente."""
    if not _CONFIGURADO:
        configurar_logging()
    return logging.getLogger(nombre)
