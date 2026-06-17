# GNN + GDELT + S&P 500

Predicción de la dirección diaria del S&P 500 (sube / baja / neutro) a partir de
eventos geopolíticos de GDELT, modelados como un grafo dinámico discreto y
procesados con una red neuronal de grafos (GNN). TFM.

## Estructura

```
src/                    código estable (.py)
├── datos/
│   ├── cargar.py       I/O: descarga/lectura de GDELT y S&P 500 (yfinance)
│   ├── preprocesar.py  GDELT -> df_grafo (URL, texto sintético, clustering, filtros)
│   ├── grafo.py        construcción del grafo (snapshot PyG por día)
│   └── financiero.py   etiquetas triclase close-to-close del S&P 500
├── modelo/
│   ├── arquitectura.py GNN (GATv2) + cabeza de clasificación
│   └── decay.py        decaimiento temporal tipo Hawkes (pendiente)
├── entrenamiento/
│   ├── loop.py         bucle de entrenamiento (pendiente)
│   └── evaluacion.py   métricas y walk-forward (pendiente)
└── utils.py
notebooks/              exploración y experimentos (.ipynb)
```

Regla: si algo se usa en más de un sitio, va a `src/`; si es exploración o
presentación, va a `notebooks/`.

## Datos

- **GDELT 1.0 Events** (diario), descarga vía `src.datos.cargar.descargar_rango`.
- **S&P 500** (^GSPC, Open/Close diario) vía `src.datos.cargar.descargar_sp500`.
- Periodo piloto: invasión de Ucrania — entrenamiento ~2 semanas previas al
  24-feb-2022, predicción del 25-feb-2022.

## Instalación

```bash
pip install -r requirements.txt
```

## Verificación rápida

```bash
python -m src.datos.financiero      # etiquetas del S&P 500 alineadas a días GDELT
python -m src.modelo.arquitectura   # forward pass de la GNN sobre snapshots con caché
```
