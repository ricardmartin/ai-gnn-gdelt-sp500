"""
Configuración centralizada del proyecto.

Todos los hiperparámetros, rutas y valores ajustables del proyecto viven aquí.
Esto permite experimentar tocando un solo archivo, sin tener que rastrear
constantes dispersas por el código.

Los valores marcados con # AJUSTAR son los que se deben fijar empíricamente
a partir del análisis exploratorio.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple


# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------

# Directorio raíz del proyecto (resuelve automáticamente respecto a este archivo).
ROOT = Path(__file__).resolve().parent

# Datos crudos descargados de GDELT (un CSV por día).
DIR_RAW = ROOT / "data" / "raw"

# Datasets procesados y caché de resultados intermedios.
DIR_PROCESSED = ROOT / "data" / "processed"

# Checkpoints de modelos durante el entrenamiento.
DIR_CHECKPOINTS = ROOT / "checkpoints"

for d in (DIR_RAW, DIR_PROCESSED, DIR_CHECKPOINTS):
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Periodo temporal del experimento
# ---------------------------------------------------------------------------

# AJUSTAR: rango de fechas final tras decidir el periodo de entrenamiento.
FECHA_INICIO = "2015-01-01"
FECHA_FIN = "2025-01-01"

# Corte horario para evitar leakage: hora UTC de cierre del mercado NY.
# Eventos GDELT con timestamp posterior se asignan al día siguiente.
HORA_CIERRE_NY_UTC = 21  # 21:00 UTC ≈ 16:00 NY (cierre regular)


# ---------------------------------------------------------------------------
# Etiqueta triclase
# ---------------------------------------------------------------------------

# Modo de discretización del retorno diario en {baja, neutro, sube}.
# Opciones:
#   "fijo"     -> usar UMBRAL_NEUTRO fijo (p.ej. ±0.5 %).
#   "sigma"    -> usar ±UMBRAL_SIGMA * desviación típica histórica.
#   "terciles" -> dividir los retornos en terciles (clases balanceadas por diseño).
MODO_ETIQUETA = "sigma"

# AJUSTAR: cuando se conozca la distribución real de retornos.
UMBRAL_NEUTRO = 0.005  # 0.5 %, solo usado si MODO_ETIQUETA="fijo"
UMBRAL_SIGMA = 0.5     # solo usado si MODO_ETIQUETA="sigma"


# ---------------------------------------------------------------------------
# Simulación financiera
# ---------------------------------------------------------------------------

# Lógica de la estrategia:
#   - Predice "sube"   -> invertido en SP500 (mantiene si ya estaba dentro).
#   - Predice "neutro" -> mantiene la posición anterior (no hace nada).
#   - Predice "baja"   -> sale al cash (vende si estaba dentro).
#   - Si además P(baja) >= UMBRAL_SHORT -> entra en short (apuesta a la baja).
#
# Solo se aplica un umbral de confianza para activar el short, porque shortear
# tiene más riesgo y conviene exigir certeza alta. El resto de la lógica se
# decide únicamente por la clase predicha (argmax).
UMBRAL_SHORT = 0.70

# Tasa libre de riesgo anual usada para calcular el Sharpe ratio.
# 0.0 significa que toda la rentabilidad cuenta como exceso. Valores típicos:
#   0.00  -> simplificación habitual en estudios académicos
#   0.02  -> ~rentabilidad bonos Tesoro USA 10Y en periodos normales
#   0.04  -> ~rentabilidad bonos Tesoro USA 10Y en 2023-2024
TASA_LIBRE_RIESGO_ANUAL = 0.0


# ---------------------------------------------------------------------------
# Filtros de GDELT
# ---------------------------------------------------------------------------

# Solo se conservan eventos con al menos este número de menciones.
# Sirve para descartar ruido de baja cobertura mediática.
MIN_NUM_MENTIONS = 5

# Tipado de aristas país-país.
# Opciones:
#   "quadclass"     -> 4 categorías (cooperación verbal/material, conflicto verbal/material)
#   "eventrootcode" -> 20 categorías CAMEO (más granular)
TIPADO_ARISTAS = "quadclass"


# ---------------------------------------------------------------------------
# Decay temporal (Hawkes)
# ---------------------------------------------------------------------------

# Tasa de decaimiento. λ alto ↔ memoria corta; λ bajo ↔ memoria larga.
# La "vida media" en días es ln(2) / λ.
#   λ = 0.0693 -> vida media de 10 días
#   λ = 0.1386 -> vida media de 5 días
#   λ = 0.0347 -> vida media de 20 días
# AJUSTAR: barrido experimental.
LAMBDA_DECAY = 0.0693  # vida media ≈ 10 días por defecto

# Ventana máxima de eventos pasados a considerar (en días).
# Eventos más antiguos se descartan porque su contribución ya es despreciable.
VENTANA_DECAY_DIAS = 60


# ---------------------------------------------------------------------------
# Arquitectura del modelo
# ---------------------------------------------------------------------------

@dataclass
class ConfigModelo:
    """Hiperparámetros del modelo HGNN."""
    # Dimensión del espacio común tras la proyección inicial.
    dim_oculta: int = 64

    # Número de capas de message passing.
    num_capas: int = 2

    # Número de cabezas de atención en cada capa GAT.
    num_cabezas: int = 4

    # Dropout aplicado entre capas.
    dropout: float = 0.3

    # Número de clases de la cabeza de clasificación.
    num_clases: int = 3


# Instancia por defecto.
MODELO = ConfigModelo()


# ---------------------------------------------------------------------------
# Entrenamiento
# ---------------------------------------------------------------------------

@dataclass
class ConfigEntrenamiento:
    """Hiperparámetros del bucle de entrenamiento."""
    # Optimización
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    batch_size: int = 32

    # Duración del entrenamiento
    epochs_max: int = 100
    paciencia_early_stopping: int = 15

    # Función de pérdida
    usar_pesos_clase: bool = True   # ponderar cross-entropy si hay desbalance

    # Reproducibilidad: lista de semillas a usar.
    # Cada semilla produce un experimento independiente; se reporta media y dispersión.
    semillas: Tuple[int, ...] = (0, 1, 2)


ENTRENAMIENTO = ConfigEntrenamiento()


# ---------------------------------------------------------------------------
# Walk-forward
# ---------------------------------------------------------------------------

@dataclass
class ConfigWalkForward:
    """Hiperparámetros del esquema de validación temporal."""
    # Número de folds (particiones).
    num_folds: int = 5

    # Modo de ventana:
    #   "expansiva" -> el set de train crece en cada fold
    #   "deslizante" -> ventana de train de tamaño fijo
    modo: str = "expansiva"

    # Tamaño mínimo (en días) del primer set de train.
    train_inicial_dias: int = 365 * 2

    # Tamaño del set de validación dentro de cada fold (en días).
    validacion_dias: int = 90


WALK_FORWARD = ConfigWalkForward()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

NIVEL_LOG = "INFO"  # DEBUG / INFO / WARNING / ERROR
