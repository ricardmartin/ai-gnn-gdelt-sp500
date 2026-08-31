# Comparativa entrenamientos — decisión modelo final TFM

Documento resumen de los cuatro notebooks de entrenamiento (`01`, `02`, `03`, `04`) para escoger cuál presentar como resultado final del TFM.

---

## Estado de ejecución

| Notebook | Ejecutado | Outputs | Comentario |
|---|---|---|---|
| `01_entrenamiento_colab.ipynb` | Sí | 26 celdas | Ejecutado en Colab |
| `02_entrenamiento_local.ipynb` | Sí | 22 celdas | Local, terciles |
| `03_experimentos_etiquetado.ipynb` | Sí | 17 celdas | Local, primer intento asimétrico + temperature scaling |
| `04_experimentos_etiquetado.ipynb` | Sí | 12 celdas | Local, versión corregida del 03 con protocolo TFM-defendible |

---

## Diseño y protocolo

| Aspecto | 01 colab | 02 local | 03 | 04 |
|---|---|---|---|---|
| Etiquetado | terciles | terciles | asimétrico q20/q80 | asimétrico q20/q80 |
| Class weights | no | no | **sí** | **sí** |
| Warm-up 60d GDELT | parcial | parcial | parcial | **sí completo** |
| Cierre mercado con DST | UTC fijo | UTC fijo | UTC fijo | **America/New_York 16:00** |
| Exclusión ventanas GDELT 404 | no | no | no | **sí (135 muestras fuera)** |
| Cache versionada por cobertura | no | no | no | **sí (firma sha256)** |
| Folds | 15 | 10 × 3 semillas = 30 runs | 10 × 3 = 30 runs | 10 × 3 = 30 runs |
| OOS única por fecha (avg semillas) | no | no | no | **sí** |
| Calibración | ninguna | ninguna | **temperature scaling (T escalar)** | **temperatura + bias por clase** |
| Bloque calibración vs test separado | no | no | no | **sí (folds 0-4 vs 5-9)** |
| Umbrales sin mirar test | no | no | no | **sí (grid solo sobre calibración)** |
| Backtest neto (costes tx + short) | parcial | parcial | parcial | **sí** |
| Baseline majority por fold | acc trivial | acc trivial | acc trivial | **acc + F1 macro + balanced acc + MCC** |
| Métricas probabilísticas | no | no | **NLL, ECE (raw vs T-scaled)** | **NLL, Brier, ECE (raw vs cal)** |

---

## Resultados globales (media ± desv sobre todos los runs)

| Métrica | 01 | 02 | 03 | 04 |
|---|---|---|---|---|
| Accuracy | 0.5533 ± 0.11 | 0.4084 ± 0.05 | 0.4872 ± 0.14 | 0.5135 ± 0.13 |
| F1-macro | **0.4280 ± 0.07** | 0.3447 ± 0.04 | 0.3685 ± 0.05 | 0.3919 ± 0.04 |
| Rent estrategia | +8.36% ± 7.5 | +6.13% ± 11.3 | +5.42% ± 12.3 | +2.52% ± 12.1 |
| Rent buy & hold | +10.43% ± 6.4 | +13.32% ± 14.6 | +13.32% ± 14.6 | +12.58% ± 11.6 |
| vs BH (pp) | **-2.08 ± 4.95** | -7.19 ± 9.76 | -7.90 ± 13.63 | -10.06 ± 12.30 |
| Sharpe | **1.08 ± 0.93** | 0.72 ± 0.97 | 0.58 ± 0.86 | 0.34 ± 0.86 |
| MaxDD | -11.33% ± 8.9 | -11.48% ± 8.75 | **-10.72% ± 9.5** | -13.15% ± 8.42 |

## Diagnóstico OOS agregado

| Métrica | 01 | 02 | 03 | 04 |
|---|---|---|---|---|
| n OOS | 2505 (folds × semillas) | 7500 | 7500 | 2390 (semillas promediadas) |
| Baseline majority acc | 0.5605 | 0.3708 | **0.5688** | 0.5615 |
| HGNN acc | 0.5533 | 0.4084 | 0.4872 | 0.5222 |
| Supera baseline (acc) | **NO -0.007** | Sí +0.038 | **NO -0.082** | NO -0.039 |
| Supera baseline (F1 macro) | +0.171 (0.428 vs 0.257) | +0.156 (0.345 vs 0.189) | +0.128 (0.369 vs 0.241) | **+0.117 (0.352 vs 0.235)** |
| Ratio capturado | +0.059 | +0.017 | — | — |
| Recall clase baja | 0.280 | 0.250 | 0.266 | 0.216 |
| Recall clase sube | 0.481 | 0.394 | 0.466 | 0.455 |

## Calibración (solo 03 y 04)

| Métrica | 03 (T scaling) | 04 (T + bias) |
|---|---|---|
| Método | Escalar T = 1.397 | T=1.035 + bias [-0.46, +0.71, -0.25] |
| Test evaluación calibración | Mismo OOS (no separado) | Bloque test aislado (folds 5-9) |
| NLL raw / cal | 1.076 → 1.064 | 1.058 → 0.970 |
| ECE raw / cal | 0.053 → **0.044 (mejora)** | 0.022 → 0.048 (empeora) |
| Brier raw / cal | — | 0.629 → 0.572 (mejora) |

## Backtest en periodo test

| Setup | 01 (mejor u_short) | 02 (mejor u_short) | 03 (calibrada mejor combo) | 04 (umbrales congelados) |
|---|---|---|---|---|
| Umbrales | u_s=0.80 | u_s=0.60 | u_s=0.60, u_l=0.40 | u_s=0.60, u_l=0.40 (congelado) |
| Rent estrategia | +231.4% | +487.3% | +1960.8% | +103.56% |
| Rent BH periodo | +332.2% | +3160.6% | +3160.6% | +86.90% |
| **vs BH** | **-101 pp** | -2673 pp | -1200 pp | **+16.66 pp** |
| Sharpe | 0.71 | 0.46 | 0.65 | **0.98** |
| MaxDD | -33.7% | -44.4% | -55.4% | **-18.90%** |
| Umbrales elegidos sin ver test | no | no | no | **sí** |

---

## Diferencias metodológicas clave

### 01 colab
- 15 folds walk-forward, terciles fijos
- Sin calibración
- Diagnóstico propio: modelo NO supera baseline en accuracy
- Barrido de umbrales sobre todo el OOS → fuga de información al elegir umbral
- Mejor sharpe global pero recall clase baja pobre

### 02 local
- 30 ejecuciones, terciles balanceado
- Ratio capturado 0.017 (casi nulo)
- BH del periodo +3160% en mercado muy alcista
- Pierde a BH por 27 pp

### 03 experimentos etiquetado
- Etiquetado asimétrico q20/q80 + class weights
- Temperature scaling escalar T=1.397 (mejora NLL y ECE modestamente)
- **NO supera baseline majority (-0.082 en acc)** — el modelo "siempre neutro" es mejor en accuracy pura
- Sí supera baseline en F1 macro (+0.128) porque distribuye entre clases
- Barrido umbrales sobre TODO el OOS → +1960% con calibradas u=0.60/0.40, pero **BH del mismo periodo +3160%**, sigue perdiendo por 1200 pp
- Recall clase baja 0.266, precision 0.242 → short débil
- Sin bloque test aislado: el barrido se hace mirando lo que luego reportas

### 04 experimentos etiquetado (versión corregida del 03)
- Primera celda documenta 10 correcciones metodológicas respecto a 03
- Único con **separación bloque calibración (folds 0-4) vs test final (folds 5-9)**
- Único con umbrales `u_short=0.60, u_long=0.40` **congelados** desde calibración
- Ensemble por promedio de probabilidades entre semillas antes de métricas y backtest (no triplica días)
- Baseline majority correcto por fold, con macro-F1, balanced acc, MCC
- Auto-decisión del notebook: `Señal SÍ, Calibración mejora NLL SÍ, Estrategia supera BH neto SÍ`

---

## Puntos débiles de cada uno

| Notebook | Debilidad principal |
|---|---|
| 01 | No supera su propio baseline majority. Umbrales sobre test. Colab (menos reproducible) |
| 02 | Pierde a BH por 27 pp. Ratio capturado ~0 |
| 03 | Barrido umbrales sobre OOS entero → fuga; pierde a BH por 1200 pp incluso con la mejor combo calibrada; NO supera baseline en acc |
| 04 | Global -10 pp vs BH, ganancia solo en test final. ECE empeora tras calibración (bias overfittea). Recall clase baja 0.22 (short débil) |

---

## Recomendación: **04**

### Razones defendibles ante tribunal

1. **Único con protocolo metodológicamente correcto**
   - Calibración temporal con folds separados
   - Umbrales elegidos sin mirar test
   - Baselines correctos por fold
   - Ensemble de semillas antes de métricas (no cuenta días 3 veces)
   - Warm-up completo GDELT + DST + exclusión ventanas incompletas

2. **Bate baseline majority por margen medible en F1-macro** (+0.117) y balanced accuracy (+0.06). Los otros tres también, pero solo 04 lo hace bajo protocolo válido.

3. **Test out-of-sample honesto supera buy & hold**: **+103.56 % vs +86.90 %, sharpe 0.98, MaxDD -18.90 %**. Único que gana a BH con protocolo válido. 01, 02 y 03 pierden a BH por márgenes brutales incluso con umbrales elegidos mirando el test.

4. **Métricas probabilísticas completas** (NLL, Brier, ECE) con comparación raw vs calibradas. Permite discutir calibración honestamente, incluyendo que ECE empeora en test (autocrítica valorada por tribunal).

5. **Documentación explícita de las 10 correcciones metodológicas** frente al notebook 03 en la primera celda del notebook — narrativa clara para la memoria.

### Cómo enmarcarlo en la memoria del TFM

- **01, 02, 03** = iteraciones exploratorias que pusieron de manifiesto sesgos metodológicos (umbrales sobre test, ausencia de calibración con folds separados, promedios de semillas incorrectos, aliasing DST, ventanas GDELT incompletas).
- **04** = experimento final corregido, con protocolo de evaluación TFM-defendible.
- Ser honesto sobre lo que 04 no demuestra: la señal no es robusta en toda la muestra. El global pierde a BH; solo el test aislado (2020-2025) gana. Marcar como **evidencia parcial de alpha condicional al régimen**.
- Trabajo futuro: **ablación market-only / GDELT-only / combinado** para atribuir la ganancia al grafo GDELT (ya sugerido en la última celda markdown de 04).

### Riesgos anticipados en la defensa

- **"¿Por qué el global pierde y solo gana el test final?"** → el test final es el bloque limpio; el global mezcla folds con distribuciones muy heterogéneas y regímenes distintos.
- **"¿Por qué la calibración empeora ECE en test?"** → el bias por clase overfittea al bloque de calibración; se reporta honestamente porque la temperatura sola no basta con class-weighted loss.
- **"¿Por qué u_long = 0.40 tan bajo?"** → el grid sobre calibración lo seleccionó; en régimen alcista el modelo captura long fácil. Discutir como limitación.
- **"¿03 no baja mejor la NLL con solo T?"** → 03 mejora NLL de 1.076 a 1.064 (marginal); 04 baja de 1.058 a 0.970 (más significativo). Además 04 separa bloques, 03 no.

---

## Decisión final

**Escoger `04_experimentos_etiquetado.ipynb` como resultado final del TFM.**

Único protocolo defendible metodológicamente y único que bate buy & hold en el bloque test aislado con métricas de clasificación, calibración y backtest neto reportadas de forma honesta.
