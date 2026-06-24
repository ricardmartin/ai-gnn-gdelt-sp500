
# Recomendaciones

El código principal del proyecto se encuentra en el notebook: notebooks/01_entrenamiento_colab.ipynb


Para ejecutar el proyecto, se recomienda abrir directamente este archivo en Google Colab y ejecutarlo.

## Configuración de fechas

Las fechas definidas en 01_entrenamiento_colab.ipynb tienen prioridad sobre las indicadas en el archivo de configuración. Esta decisión se ha tomado para facilitar la edición y pruebas durante la fase de evaluación del proyecto.

## Uso en Google Colab gratuito

Si se utiliza la versión gratuita de Google Colab, se recomienda limitar el rango temporal utilizado debido a las restricciones de almacenamiento disponibles (aproximadamente 80 GB).

Las fechas actuales configuradas en el notebook están ajustadas para realizar un entrenamiento ligero pero suficiente.

Los datos históricos se descargan automáticamente durante la ejecución y posteriormente se realiza el filtrado necesario. Por este motivo, ampliar el número de años utilizados incrementará tanto el espacio requerido como el tiempo de ejecución.



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
│   └── 01_entrenamiento_colab.ipynb ABRIR EN COLAB Y EJECUTAR, LLAMA A TODO LO DEMÁS
└── data/
    ├── raw/                         CSVs de GDELT.
    └── processed/                   Datasets procesados y caché.
```

