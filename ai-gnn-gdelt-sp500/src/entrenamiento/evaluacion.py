"""
Evaluación: métricas de clasificación para el problema triclase.

Métricas incluidas:
    accuracy
    F1 macro
    F1 por clase
    matriz de confusión

Las funciones aceptan arrays numpy o tensores torch indistintamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch


def _a_numpy(x) -> np.ndarray:
    """Convierte cualquier entrada razonable a numpy."""
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)


@dataclass
class Metricas:
    """Conjunto de métricas resultantes de una evaluación."""
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
    """
    Calcula el conjunto completo de métricas.
    Args:
        y_true: etiquetas reales.
        y_pred: predicciones (clases enteras).
        num_clases: número de clases.
    """
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


@dataclass
class ResultadoExperimento:
    """Agrupa métricas de múltiples folds y/o semillas para reporte conjunto."""
    metricas_por_fold: list[Metricas] = field(default_factory=list)

    def agregar(self, m: Metricas) -> None:
        self.metricas_por_fold.append(m)

    def media_y_std(self) -> dict[str, tuple[float, float]]:
        """Devuelve media y desviación típica de cada métrica entre folds."""
        if not self.metricas_por_fold:
            return {}
        accs = [m.accuracy for m in self.metricas_por_fold]
        f1s = [m.f1_macro for m in self.metricas_por_fold]
        return {
            "accuracy": (float(np.mean(accs)), float(np.std(accs))),
            "f1_macro": (float(np.mean(f1s)), float(np.std(f1s))),
        }

    def resumen_final(self) -> str:
        ms = self.media_y_std()
        if not ms:
            return "(sin resultados)"
        return (
            f"accuracy = {ms['accuracy'][0]:.4f} ± {ms['accuracy'][1]:.4f} | "
            f"f1_macro = {ms['f1_macro'][0]:.4f} ± {ms['f1_macro'][1]:.4f} | "
            f"folds = {len(self.metricas_por_fold)}"
        )
