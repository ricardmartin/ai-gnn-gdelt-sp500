"""
Modelos de referencia (baselines) para comparar con la HGNN.

Estos modelos representan complejidad creciente y permiten aislar la
contribución de cada componente del enfoque:

1. NAIVE          : predice siempre la clase mayoritaria del train.
2. LOGISTICA      : regresión logística sobre features aplanadas del grafo.
3. XGBOOST        : XGBoost sobre las mismas features aplanadas.
4. LSTM_FINANCIERA: LSTM alimentada solo con la ventana de retornos del SP500.
5. LSTM_GPR       : LSTM alimentada con retornos + una señal geopolítica
                    agregada (sin estructura de grafo). ESTE ES EL BASELINE
                    CRÍTICO porque es el que aísla "modelar la geopolítica
                    como grafo" frente a "modelarla como variable plana".

Solo los más simples (1, 2, 3) se implementan aquí completos; los LSTM se
dejan como esqueleto comentado porque requieren preparar series temporales
y pertenecen más a la fase de evaluación final.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logging import obtener_logger

log = obtener_logger(__name__)


class BaselineNaive:
    """Predice siempre la clase mayoritaria del conjunto de entrenamiento."""

    def __init__(self) -> None:
        self.clase_mayoritaria: int | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineNaive":
        counts = pd.Series(y).value_counts()
        self.clase_mayoritaria = int(counts.idxmax())
        log.info("Naive: clase mayoritaria = %d (%.1f%%)",
                 self.clase_mayoritaria, 100.0 * counts.iloc[0] / len(y))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.clase_mayoritaria is None:
            raise RuntimeError("BaselineNaive: llama a fit() primero")
        return np.full(len(X), self.clase_mayoritaria, dtype=np.int64)


def aplanar_grafo(data) -> np.ndarray:
    """
    Convierte un HeteroData en un vector plano de features.

    Concatena:
        - x del nodo market
        - vector "resumen" de los nodos country (media, max, std por feature)
        - número de aristas country-country
        - peso total de aristas country-country

    Esto permite alimentar modelos clásicos (regresión logística, XGBoost) con
    las mismas señales que recibe la GNN, eliminando solo la estructura de
    grafo. Es la base honesta para comparar.
    """
    x_market = data["market"].x.cpu().numpy().flatten()
    x_country = data["country"].x.cpu().numpy()

    # Resúmenes estadísticos del bloque country.
    resumen_country = np.concatenate([
        x_country.mean(axis=0),
        x_country.std(axis=0),
        x_country.max(axis=0),
    ])

    edge_attr_cc = data["country", "interactua", "country"].edge_attr.cpu().numpy()
    if edge_attr_cc.size > 0:
        num_aristas = float(edge_attr_cc.shape[0])
        peso_total = float(edge_attr_cc[:, 0].sum())
        tono_medio_aristas = float(edge_attr_cc[:, 1].mean())
    else:
        num_aristas, peso_total, tono_medio_aristas = 0.0, 0.0, 0.0

    extras = np.array([num_aristas, peso_total, tono_medio_aristas], dtype=np.float32)

    return np.concatenate([x_market, resumen_country, extras]).astype(np.float32)


def construir_matriz_features(dataset) -> tuple[np.ndarray, np.ndarray]:
    """
    Recorre un dataset y devuelve (X, y) listos para sklearn / XGBoost.
    """
    X_list = []
    y_list = []
    for i in range(len(dataset)):
        data, clase = dataset[i]
        X_list.append(aplanar_grafo(data))
        y_list.append(clase)
    X = np.vstack(X_list)
    y = np.array(y_list, dtype=np.int64)
    return X, y


def entrenar_logistica(X_train: np.ndarray, y_train: np.ndarray):
    """Entrena una regresión logística multinomial."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000, multi_class="auto")),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def entrenar_xgboost(X_train: np.ndarray, y_train: np.ndarray):
    """Entrena un XGBoost multiclass."""
    from xgboost import XGBClassifier

    modelo = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        verbosity=0,
    )
    modelo.fit(X_train, y_train)
    return modelo


# AJUSTAR: implementar LSTM_FINANCIERA y LSTM_GPR cuando se tengan series
# temporales preparadas. Ver TFM sección 4.3.6.
