# Arquitectura del proyecto

Resumen técnico de qué hace cada módulo y cómo encajan.

## Diagrama de flujo

```
GDELT raw            yfinance              FRED
   │                    │                    │
   ▼                    ▼                    ▼
descarga_gdelt.py   descarga_financiero.py (SP500, VIX, macro)
   │                    │
   ▼                    │
preprocesar.py          │
(filtros, agregación)   │
   │                    │
   ├── df_eventos       │
   ▼                    │
agregar_eventos_por_dia_y_par
   │                    │
   ▼                    │                   etiquetas.py
df_agregado             ├──────────────────► (target triclase, corte horario)
   │                    │                       │
   │                    │                       ▼
   │                    │                   df_etiquetas
   ▼                    ▼                       │
            grafo.py (HeteroData por día)       │
                  │                             │
                  └── decay.py (Hawkes en aristas país-país)
                  │                             │
                  ▼                             ▼
                                   dataset.py (DatasetGrafoDiario)
                                              │
                                              ▼
                            entrenamiento/walkforward.py
                                              │
                                              ▼
                            entrenamiento/loop.py
                                              │
                                              ▼
                            modelo/arquitectura.py (HGNN)
                                              │
                                              ▼
                            entrenamiento/evaluacion.py (métricas)
```

## Decisiones clave (referencia rápida)

| Decisión | Valor actual | Dónde se cambia |
|---|---|---|
| Roster de países | 20 países propuestos | `src/utils/paises.py` |
| Pesos comercio bilateral | Estimaciones de orden de magnitud | `src/utils/paises.py` |
| Tipado de aristas país-país | QuadClass (4 categorías) | `config.py` (`TIPADO_ARISTAS`) |
| λ del decay Hawkes | 0.0693 (vida media ≈ 10 días) | `config.py` (`LAMBDA_DECAY`) |
| Ventana decay | 60 días | `config.py` (`VENTANA_DECAY_DIAS`) |
| Modo de etiqueta | sigma (±0.5σ) | `config.py` (`MODO_ETIQUETA`) |
| Corte horario | 21:00 UTC | `config.py` (`HORA_CIERRE_NY_UTC`) |
| Arquitectura GNN | HeteroGAT (GATv2+HeteroConv) | `src/modelo/arquitectura.py` |
| Dim embeddings | 64 | `config.py` (`MODELO.dim_oculta`) |
| Nº capas message passing | 2 | `config.py` (`MODELO.num_capas`) |
| Cabezas atención | 4 | `config.py` (`MODELO.num_cabezas`) |
| Dropout | 0.3 | `config.py` (`MODELO.dropout`) |
| LR / Weight decay | 1e-3 / 1e-4 | `config.py` (`ENTRENAMIENTO`) |
| Walk-forward | 5 folds, expansiva | `config.py` (`WALK_FORWARD`) |
| Semillas | (0, 1, 2) | `config.py` (`ENTRENAMIENTO.semillas`) |

## Lo que está marcado como `# AJUSTAR`

Buscar `AJUSTAR` en el código localiza todos los puntos que dependen del EDA
o de decisiones empíricas pendientes:

```
$ grep -rn "AJUSTAR" src/ config.py
```

## Lo que NO está implementado (a propósito)

- **HGT real:** se usa HeteroGAT (vía HeteroConv + GATv2). Migrar a HGT es
  cambiar la clase de capa en `src/modelo/arquitectura.py`.
- **Baselines LSTM:** mencionados en `src/modelo/baselines.py` como TODO.
  Pertenecen a la fase final de comparación.
- **Sectores GICS como nodos:** trabajo futuro, requiere GKG.
