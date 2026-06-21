"""
Evaluación: métricas de clasificación y simulación financiera.

Dos bloques de métricas:

1. CLASIFICACIÓN:
   - accuracy
   - F1 macro
   - F1 por clase
   - matriz de confusión

2. SIMULACIÓN FINANCIERA:
   - rentabilidad acumulada
   - rentabilidad vs buy & hold
   - Sharpe ratio
   - max drawdown
   - curva de capital (para graficar)

La estrategia simulada:
   - Predice "sube"   -> invertido en SP500 (mantiene si ya estaba).
   - Predice "neutro" -> mantiene la posición anterior.
   - Predice "baja"   -> a cash (vende si estaba dentro).
   - Si P(baja) >= UMBRAL_SHORT -> short (apuesta a la baja).

Las funciones aceptan arrays numpy o tensores torch indistintamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from config import UMBRAL_SHORT, TASA_LIBRE_RIESGO_ANUAL


def _a_numpy(x) -> np.ndarray:
    """Convierte cualquier entrada razonable a numpy."""
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)


# ---------------------------------------------------------------------------
# Métricas de CLASIFICACIÓN
# ---------------------------------------------------------------------------

@dataclass
class Metricas:
    """Conjunto de métricas de clasificación."""
    accuracy: float
    f1_macro: float
    f1_por_clase: np.ndarray
    matriz_confusion: np.ndarray
    n_muestras: int

    def resumen(self) -> str:
        return (
            f"acc={self.accuracy:.4f} | "
            f"F1_macro={self.f1_macro:.4f} | "
            f"F1_clases={self.f1_por_clase.round(3).tolist()} | "
            f"n={self.n_muestras}"
        )


def calcular_metricas(y_true, y_pred, num_clases: int = 3) -> Metricas:
    """Calcula las métricas de clasificación."""
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

    y_true = _a_numpy(y_true)
    y_pred = _a_numpy(y_pred)

    acc = float(accuracy_score(y_true, y_pred))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_clases = f1_score(
        y_true, y_pred, average=None, labels=list(range(num_clases)), zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(num_clases)))

    return Metricas(
        accuracy=acc,
        f1_macro=f1_macro,
        f1_por_clase=np.asarray(f1_clases),
        matriz_confusion=cm,
        n_muestras=len(y_true),
    )


# ---------------------------------------------------------------------------
# SIMULACIÓN FINANCIERA
# ---------------------------------------------------------------------------

# Convención de clases para que el código sea legible.
CLASE_BAJA = 0
CLASE_NEUTRO = 1
CLASE_SUBE = 2


@dataclass
class MetricasFinancieras:
    """Resultados de la simulación financiera para un fold/conjunto."""
    # Rentabilidades como fracción (0.05 = +5%, -0.03 = -3%).
    rentabilidad_estrategia: float
    rentabilidad_buy_hold: float
    rentabilidad_vs_bh: float        # estrategia - buy_hold (diferencia absoluta en %)
    sharpe_estrategia: float
    sharpe_buy_hold: float
    max_drawdown_estrategia: float   # peor caída desde un pico (negativo)
    max_drawdown_buy_hold: float
    # Conteos para auditoría
    n_dias: int
    dias_long: int
    dias_short: int
    dias_cash: int
    # Curvas para graficar
    curva_estrategia: np.ndarray     # capital normalizado a 1.0 al inicio
    curva_buy_hold: np.ndarray
    # Posiciones por día (1=long, 0=cash, -1=short), para debug
    posiciones: np.ndarray

    def resumen(self) -> str:
        return (
            f"rent_estr={100 * self.rentabilidad_estrategia:+.2f}% | "
            f"rent_BH={100 * self.rentabilidad_buy_hold:+.2f}% | "
            f"vs_BH={100 * self.rentabilidad_vs_bh:+.2f}pp | "
            f"sharpe={self.sharpe_estrategia:.2f} | "
            f"maxDD={100 * self.max_drawdown_estrategia:.2f}% | "
            f"long/short/cash={self.dias_long}/{self.dias_short}/{self.dias_cash}"
        )


def _calcular_posiciones(
    clases_predichas: np.ndarray,
    proba_baja: np.ndarray,
    umbral_short: float = UMBRAL_SHORT,
) -> np.ndarray:
    """
    Convierte predicciones en posiciones diarias siguiendo la lógica de la estrategia.

    Args:
        clases_predichas: array de enteros {0,1,2} con la clase del día.
        proba_baja: probabilidad P(clase=baja) del modelo para cada día.
        umbral_short: umbral mínimo para activar short.

    Returns:
        Array de int con la posición de cada día: 1=long, 0=cash, -1=short.
        La posición se "arrastra" cuando el modelo predice neutro.
    """
    n = len(clases_predichas)
    pos = np.zeros(n, dtype=np.int8)
    posicion_actual = 0  # arrancamos sin nada

    for i in range(n):
        c = int(clases_predichas[i])
        if c == CLASE_SUBE:
            posicion_actual = 1
        elif c == CLASE_BAJA:
            # Sale del SP500. Si la confianza es alta, además se pone corto.
            if proba_baja[i] >= umbral_short:
                posicion_actual = -1
            else:
                posicion_actual = 0
        else:  # CLASE_NEUTRO -> mantiene la posición anterior
            pass
        pos[i] = posicion_actual

    return pos


def _calcular_drawdown_maximo(curva: np.ndarray) -> float:
    """
    Calcula el máximo drawdown (peor caída desde un pico) de una curva de capital.

    Devuelve un número negativo (o 0 si la curva no baja nunca). Por ejemplo,
    -0.25 significa que en algún momento se perdió un 25% desde el máximo alcanzado.
    """
    if len(curva) == 0:
        return 0.0
    picos = np.maximum.accumulate(curva)
    drawdowns = (curva - picos) / picos
    return float(drawdowns.min())


def _calcular_sharpe(retornos: np.ndarray, tasa_libre_anual: float = TASA_LIBRE_RIESGO_ANUAL) -> float:
    """
    Sharpe ratio anualizado.

    Sharpe = (rentabilidad media - tasa_libre) / volatilidad, escalado por sqrt(252)
    para anualizar a partir de retornos diarios.
    """
    retornos = np.asarray(retornos, dtype=float)
    if len(retornos) < 2:
        return 0.0
    # Convertir tasa anual a diaria.
    tasa_diaria = tasa_libre_anual / 252.0
    exceso = retornos - tasa_diaria
    sigma = exceso.std(ddof=1)
    if sigma < 1e-12:
        return 0.0
    return float(np.sqrt(252.0) * exceso.mean() / sigma)


def simular_estrategia(
    probabilidades: np.ndarray,
    retornos_reales: np.ndarray,
    umbral_short: float = UMBRAL_SHORT,
) -> MetricasFinancieras:
    """
    Simula la estrategia y compara con buy & hold.

    Args:
        probabilidades: array de shape (n, 3) con [P(baja), P(neutro), P(sube)] por día.
        retornos_reales: array de shape (n,) con el retorno real de cada día (close-to-close).
        umbral_short: umbral mínimo de P(baja) para activar short.

    Returns:
        MetricasFinancieras con todos los resultados.
    """
    probabilidades = _a_numpy(probabilidades)
    retornos_reales = _a_numpy(retornos_reales).astype(float)

    if probabilidades.ndim != 2 or probabilidades.shape[1] != 3:
        raise ValueError(
            f"`probabilidades` debe tener shape (n, 3), llegó {probabilidades.shape}"
        )
    if len(probabilidades) != len(retornos_reales):
        raise ValueError(
            f"Longitudes incompatibles: probas={len(probabilidades)} "
            f"retornos={len(retornos_reales)}"
        )

    n = len(retornos_reales)
    if n == 0:
        # Caso degenerado: nada que simular.
        return MetricasFinancieras(
            rentabilidad_estrategia=0.0, rentabilidad_buy_hold=0.0,
            rentabilidad_vs_bh=0.0,
            sharpe_estrategia=0.0, sharpe_buy_hold=0.0,
            max_drawdown_estrategia=0.0, max_drawdown_buy_hold=0.0,
            n_dias=0, dias_long=0, dias_short=0, dias_cash=0,
            curva_estrategia=np.array([1.0]),
            curva_buy_hold=np.array([1.0]),
            posiciones=np.array([], dtype=np.int8),
        )

    # Decisiones diarias.
    clases_predichas = probabilidades.argmax(axis=1)
    proba_baja = probabilidades[:, CLASE_BAJA]
    posiciones = _calcular_posiciones(clases_predichas, proba_baja, umbral_short)

    # Retornos diarios de la estrategia: posición × retorno real del día.
    # Si pos=1 (long): replica el SP500.
    # Si pos=0 (cash): retorno cero.
    # Si pos=-1 (short): retorno opuesto al SP500.
    retornos_estrategia = posiciones.astype(float) * retornos_reales

    # Curvas de capital (capital normalizado a 1.0 al inicio).
    curva_estrategia = np.cumprod(1.0 + retornos_estrategia)
    curva_buy_hold = np.cumprod(1.0 + retornos_reales)

    # Rentabilidades acumuladas.
    rent_estrategia = float(curva_estrategia[-1] - 1.0)
    rent_buy_hold = float(curva_buy_hold[-1] - 1.0)

    return MetricasFinancieras(
        rentabilidad_estrategia=rent_estrategia,
        rentabilidad_buy_hold=rent_buy_hold,
        rentabilidad_vs_bh=rent_estrategia - rent_buy_hold,
        sharpe_estrategia=_calcular_sharpe(retornos_estrategia),
        sharpe_buy_hold=_calcular_sharpe(retornos_reales),
        max_drawdown_estrategia=_calcular_drawdown_maximo(curva_estrategia),
        max_drawdown_buy_hold=_calcular_drawdown_maximo(curva_buy_hold),
        n_dias=n,
        dias_long=int((posiciones == 1).sum()),
        dias_short=int((posiciones == -1).sum()),
        dias_cash=int((posiciones == 0).sum()),
        curva_estrategia=curva_estrategia,
        curva_buy_hold=curva_buy_hold,
        posiciones=posiciones,
    )


# ---------------------------------------------------------------------------
# Agregación de resultados a lo largo de folds/seeds
# ---------------------------------------------------------------------------

@dataclass
class ResultadoExperimento:
    """Agrupa métricas (clasificación + financieras) de múltiples folds y seeds."""
    metricas_por_fold: list[Metricas] = field(default_factory=list)
    metricas_financieras_por_fold: list[MetricasFinancieras] = field(default_factory=list)

    def agregar(
        self,
        m: Metricas,
        mf: MetricasFinancieras | None = None,
    ) -> None:
        self.metricas_por_fold.append(m)
        if mf is not None:
            self.metricas_financieras_por_fold.append(mf)

    def media_y_std(self) -> dict[str, tuple[float, float]]:
        """Devuelve media y desviación típica de las métricas principales."""
        out: dict[str, tuple[float, float]] = {}
        if self.metricas_por_fold:
            accs = [m.accuracy for m in self.metricas_por_fold]
            f1s = [m.f1_macro for m in self.metricas_por_fold]
            out["accuracy"] = (float(np.mean(accs)), float(np.std(accs)))
            out["f1_macro"] = (float(np.mean(f1s)), float(np.std(f1s)))
        if self.metricas_financieras_por_fold:
            rent = [m.rentabilidad_estrategia for m in self.metricas_financieras_por_fold]
            bh = [m.rentabilidad_buy_hold for m in self.metricas_financieras_por_fold]
            vs_bh = [m.rentabilidad_vs_bh for m in self.metricas_financieras_por_fold]
            sharpe = [m.sharpe_estrategia for m in self.metricas_financieras_por_fold]
            dd = [m.max_drawdown_estrategia for m in self.metricas_financieras_por_fold]
            out["rent_estrategia"] = (float(np.mean(rent)), float(np.std(rent)))
            out["rent_buy_hold"] = (float(np.mean(bh)), float(np.std(bh)))
            out["rent_vs_bh"] = (float(np.mean(vs_bh)), float(np.std(vs_bh)))
            out["sharpe"] = (float(np.mean(sharpe)), float(np.std(sharpe)))
            out["max_drawdown"] = (float(np.mean(dd)), float(np.std(dd)))
        return out

    def resumen_final(self) -> str:
        ms = self.media_y_std()
        if not ms:
            return "(sin resultados)"

        partes = []
        if "accuracy" in ms:
            partes.append(
                f"accuracy = {ms['accuracy'][0]:.4f} ± {ms['accuracy'][1]:.4f}"
            )
            partes.append(
                f"f1_macro = {ms['f1_macro'][0]:.4f} ± {ms['f1_macro'][1]:.4f}"
            )
        if "rent_estrategia" in ms:
            partes.append(
                f"rent_estrategia = {100*ms['rent_estrategia'][0]:+.2f}% "
                f"± {100*ms['rent_estrategia'][1]:.2f}%"
            )
            partes.append(
                f"rent_buy_hold = {100*ms['rent_buy_hold'][0]:+.2f}% "
                f"± {100*ms['rent_buy_hold'][1]:.2f}%"
            )
            partes.append(
                f"vs_BH = {100*ms['rent_vs_bh'][0]:+.2f}pp "
                f"± {100*ms['rent_vs_bh'][1]:.2f}pp"
            )
            partes.append(
                f"sharpe = {ms['sharpe'][0]:.2f} ± {ms['sharpe'][1]:.2f}"
            )
            partes.append(
                f"maxDD = {100*ms['max_drawdown'][0]:.2f}% "
                f"± {100*ms['max_drawdown'][1]:.2f}%"
            )

        return f"folds={len(self.metricas_por_fold)} | " + " | ".join(partes)
