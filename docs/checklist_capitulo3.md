# Checklist de correcciones · Capítulo 3

Lista accionable de [revision_capitulo3.md](revision_capitulo3.md). Los identificadores coinciden: si algo no se entiende, el detalle completo con la frase literal está allí.

**Progreso:** 0 / 18

🔴 error de hecho · 🟠 alineación con caps. 4-6 · 🟡 mejora · ⚪ forma

> ⚠️ Este capítulo es breve pero contiene el hallazgo más grave del documento a nivel académico: **tres de los cuatro objetivos específicos no coinciden con el trabajo ejecutado**. Reescritura prioritaria.

---

## 1 · Bloque exprés (los objetivos específicos, todos a la vez)

- [x] 🔴 **3.OE-B** · Numerar los objetivos como **OE1, OE2, OE3, OE4**. Sin numeración explícita, §4 y §7 no pueden referenciarlos con claridad
- [x] 🔴 **3.OE1-A** · **OE1** no describe el trabajo. Reescribir: no hay «selección de periodos geopolíticamente relevantes»; hay **periodo continuo 2015-2025** sobre roster fijo de 20 países, 2.751 grafos diarios
- [x] 🔴 **3.OE2-A** · **OE2** promete «revisión manual de una muestra representativa» que no está documentada. Dos opciones: recogerla en §4-§5 si se hizo, o sustituirla por validación cuantitativa (distribución de grados, top pares, distribución QuadClass)
- [x] 🔴 **3.OE3-A** · **OE3** promete pipeline en vivo «antes de la apertura» que no existe. Además, la etiqueta es cierre-a-cierre de t+1, no apertura, y el corte horario es inerte con GDELT 1.0 (§4.1-C). Reformular en términos de flujo reproducible offline
- [x] 🔴 **3.OE4-A** · **OE4** promete superar «un modelo sin información geopolítica» que no se construyó. Es el mismo problema que **X-1** del cap. 4. Reescribir OE4, §4.3.6 y §6 en el mismo commit. Dos baselines afectados:
  - **LSTM financiera** (§4.3.6-E) — no existe en `src/modelo/baselines.py` (solo `BaselineNaive`, `entrenar_logistica`, `entrenar_xgboost`)
  - **Baseline geopolítico agregado sin grafo** (§4.3.6-F) — no existe
  - §5.3 evalúa **3 baselines** (naive, LR, XGBoost), no los 5 prometidos en §4.3.6

---

## 2 · Objetivo general

- [ ] 🟡 **3.OG-A** · Unificar «S&P 500» / «SP500» en todo el documento. El objetivo general es la frase más citable del trabajo

---

## 3 · Metodología — las cinco fases, alineadas con lo ejecutado

- [ ] 🔴 **3.M1-A** · **Fase 1** hereda el problema de OE1. Reescribir en términos de ingesta continua 2015-2025, filtro por roster (20 países), filtro por `NumMentions ≥ 5`, hasta 2.751 días operativos
- [ ] 🟠 **3.M2-A** · **Fase 2** hereda el mismo problema + falta mencionar terciles y macro (VIX, DXY, USA macro). «Neutralidad» / «neutro»: alinear con el resto del documento
- [ ] 🟠 **3.M3-A** · **Fase 3** dice «snapshots diarios». La decisión de §4.2.1 es **grafo persistente con decay por QuadClass + ventana 60 días**, no snapshots. Reescribir
- [ ] 🟠 **3.M4-A** · **Fase 4** cierra abstracta. Declarar la decisión: **HeteroGAT con GATv2 vía HeteroConv + integración del S&P 500 como nodo del grafo** (§4.2.2, §4.2.3)
- [ ] 🔴 **3.M5-A** · **Fase 5** olvida walk-forward, semillas y Sharpe. Reescribir:

  > «Entrenamiento con esquema walk-forward de 10 folds expansivos, embargo cero, 250 sesiones de validación por fold, promediando sobre 3 semillas (0, 1, 2). Evaluación mediante métricas de clasificación (exactitud, F1 macro, matriz de confusión, precisión y recall por clase) y evaluación financiera complementaria mediante estrategia simulada (ratio de Sharpe).»

---

## 4 · Piezas que faltan por completo

- [ ] 🟡 **3.CRON-A** · Añadir **cronograma** (tabla de tres columnas: fase / semanas / hitos) usando fechas reales del historial de commits
- [ ] 🟡 **3.HERR-A** · Añadir el **stack técnico**: Python, PyTorch, PyTorch Geometric, pandas, entorno de ejecución (Colab GPU T4 + local CPU). Citar notebooks `01_entrenamiento_colab.ipynb` y `02_entrenamiento_local.ipynb`
- [ ] 🟡 **3.GRUPO-A** · Frase final que remita a la sección inicial «Organización del trabajo en grupo». Acota autoría de las cinco fases

---

## 5 · Formas

- [ ] ⚪ **3.F-A** · «neutralidad» vs «neutro»: unificar. *(ya en el checklist §5 del cap. 4)*
- [ ] ⚪ **3.F-B** · «snapshots» → «instantáneas» o «estados diarios del grafo». Desaparece si se aplica 3.M3-A
- [ ] ⚪ **3.F-C** · «predicción triclase» sin definir en la primera aparición. Añadir «(subida, neutro, bajada)» la primera vez
- [ ] ⚪ **3.F-D** · Revisar punto final en los cuatro OE

---

## 6 · Incoherencias con otros capítulos

- [ ] 🟠 **X-Cap3-1** · OE1/Fase 1 vs realidad del dataset. Consolidar 3.OE1-A + 3.M1-A en el mismo pase
- [x] 🟠 **X-Cap3-2** · OE4 vs §5.3 y §6. Consolidar 3.OE4-A con X-1 del cap. 4 y con §6
- [x] 🟠 **X-Cap3-3** · OE3 vs §4.1-C y §4.3.5. Los tres apartados hablan de la misma decisión inejecutable. Reformular coordinado

---

## 7 · Verificaciones antes de reescribir

- [ ] ¿Se hizo alguna forma de **revisión manual** del grafo durante el desarrollo? (para decidir 3.OE2-A)
- [ ] ¿Existe algún script o notebook que, dado un día, produzca la predicción del siguiente? (para decidir 3.OE3-A). Si sí, documentarlo. Si no, reformular
- [ ] Enumerar **hitos reales** del trabajo (`git log --pretty=format:"%h %ad %s" --date=short`) para poblar el cronograma de 3.CRON-A

---

## Anexo · Alineación objetivo por objetivo

| Objetivo | Formulación actual | Ejecutado | Consistencia |
|---|---|---|---|
| OG  | Diseñar, implementar y evaluar el modelo | Hecho | ✅ Sí |
| OE1 | Seleccionar periodos históricos relevantes | Periodo continuo 2015-2025 | 🔴 No |
| OE2 | Diseñar el grafo + revisión manual | Grafo diseñado, revisión no documentada | 🔴 Parcial |
| OE3 | Automatizar predicción antes de la apertura | Pipeline offline, sin apertura, sin en vivo | 🔴 No |
| OE4 | F1 superior al modelo sin información geopolítica | Baseline no construido | 🔴 No |

**El objetivo general se cumplió. Los cuatro específicos han quedado descolgados de la ejecución real.** Reescribir con máxima prioridad.
