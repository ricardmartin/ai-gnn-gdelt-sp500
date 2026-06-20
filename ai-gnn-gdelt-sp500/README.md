# ai-gnn-gdelt-sp500

Trabajo Fin de Máster · Predicción de la dirección del S&P 500 a partir de eventos
geopolíticos extraídos de GDELT, modelados como grafo heterogéneo dinámico y
procesados con una Red Neuronal de Grafos Heterogénea (HGNN).

## Idea en una frase

Construir un grafo donde los nodos son países (más el propio S&P 500 como nodo
adicional), las aristas país–país son interacciones geopolíticas extraídas de GDELT
con memoria temporal (decay tipo Hawkes), y las aristas país–mercado representan
la exposición estructural de cada actor al índice. Una HGNN procesa este grafo y
predice si el S&P 500 subirá, bajará o se mantendrá neutro al día siguiente.

## Estructura

```
ai-gnn-gdelt-sp500/
├── config.py                        Hiperparámetros centralizados.
├── requirements.txt                 Dependencias para Colab / local.
├── src/
│   ├── datos/
│   │   ├── descarga_gdelt.py        Descarga CSVs diarios de GDELT 1.0.
│   │   ├── descarga_financiero.py   Descarga S&P 500 (yfinance) y macro (FRED).
│   │   ├── preprocesar.py           Filtrado, dedup y agregación de eventos.
│   │   ├── etiquetas.py             Cálculo de la etiqueta triclase.
│   │   ├── grafo.py                 Construcción de HeteroData por día.
│   │   └── dataset.py               Dataset PyG que agrupa snapshots + etiquetas.
│   ├── modelo/
│   │   ├── arquitectura.py          HGNN heterogénea con atención.
│   │   ├── decay.py                 Refuerzo + decay temporal Hawkes.
│   │   └── baselines.py             Naive, regresión logística, XGBoost, LSTM.
│   ├── entrenamiento/
│   │   ├── walkforward.py           Particiones temporales.
│   │   ├── loop.py                  Bucle de entrenamiento por fold.
│   │   └── evaluacion.py            Métricas y reporte.
│   └── utils/
│       ├── paises.py                Roster de nodos y matriz de comercio bilateral.
│       └── logging.py               Logging consistente.
├── notebooks/
│   └── 01_entrenamiento_colab.ipynb Orquestador de extremo a extremo.
└── data/
    ├── raw/                         CSVs de GDELT.
    └── processed/                   Datasets procesados y caché.
```

## Uso rápido en Colab

```python
# 1) Clonar el repo
!git clone https://github.com/<usuario>/ai-gnn-gdelt-sp500.git
%cd ai-gnn-gdelt-sp500
!pip install -r requirements.txt

# 2) Lanzar el pipeline desde el notebook
# Ver: notebooks/01_entrenamiento_colab.ipynb
```

## Estado actual

Este repositorio es una base de trabajo. Los archivos contienen una implementación
funcional siguiendo el diseño del TFM, pero hay valores marcados como ajustables
(roster final de países, hiperparámetro λ del decay, umbral exacto de la clase
neutra, etc.) que deben fijarse empíricamente a partir del análisis exploratorio
de datos.

Puntos no cerrados que se marcan en los archivos con `# AJUSTAR:`

- Roster final de países (lista provisional en `src/utils/paises.py`)
- Matriz de pesos de comercio bilateral (placeholder en `src/utils/paises.py`)
- λ del decay temporal (valor inicial en `config.py`)
- Umbral de la clase neutra (valor inicial en `config.py`)
- Dimensiones del modelo (valores iniciales en `config.py`)
