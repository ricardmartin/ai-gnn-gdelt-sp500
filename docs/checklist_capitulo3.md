# Checklist de correcciones · Capítulo 3

Lista accionable de [revision_capitulo3.md](revision_capitulo3.md). Los identificadores coinciden: si algo no se entiende, el detalle completo con la frase literal está allí.

**Quedan 16 tareas.** Los cinco objetivos específicos, que eran el bloque grave de este capítulo, ya están reescritos como OE1-OE6 y se han retirado de esta lista.

> ## ⚠️ Lo primero de todo
>
> **En §3.2 conviven las cuatro viñetas antiguas de objetivos específicos y los nuevos OE1-OE6, una lista detrás de la otra.** Las viejas prometen «periodos geopolíticamente relevantes», «revisión manual de una muestra», «señal de inversión antes de la apertura» y «superar a un modelo de referencia sin información geopolítica» — exactamente las cuatro cosas que OE1-OE6 corrigen. El texto nuevo se pegó y el viejo no se borró, así que el documento se contradice en la misma página.
>
> **Acción: borrar las cuatro viñetas y dejar solo OE1-OE6.** Es el error más grave que le queda a la memoria y se arregla en dos minutos.

🔴 error de hecho · 🟠 alineación con caps. 4-6 · 🟡 mejora · ⚪ forma

> 📍 **Cómo se trabaja con este fichero, estado general y decisiones ya tomadas: [GUIA_REVISION_TFM.md](GUIA_REVISION_TFM.md).**

---

## 1 · Objetivo general

- [ ] 🟡 **3.OG-A** · Unificar «S&P 500» / «SP500» en todo el documento (conviven 17 y 32 apariciones). El objetivo general es la frase más citable del trabajo, así que ahí importa especialmente
- [ ] 🟡 **3.OG-B** · El objetivo general no dice que la predicción sea **triclase** ni cuál es el **horizonte**, y no distingue la integración propia (S&P 500 como nodo del grafo) de la *late fusion* que §2.3 descarta. Propuesta:

  > «Diseñar, implementar y evaluar un modelo de predicción de la dirección del S&P 500 en la sesión siguiente —subida, neutralidad o bajada— basado en redes neuronales de grafos heterogéneos, que integre en una única estructura los eventos geopolíticos extraídos de GDELT y los indicadores del propio mercado, sobre el periodo 2015-2025.»

  Deliberadamente **no** incluye criterio de éxito («superando a modelos de referencia»): eso es OE4, y meterlo en el objetivo general lo convierte en promesa evaluable, que es el problema que tenían los cuatro OE antiguos

---

## 2 · Metodología — las cinco fases, alineadas con lo ejecutado

- [ ] 🔴 **3.M1-A** · **Fase 1** hereda el problema de OE1. Reescribir en términos de ingesta continua 2015-2025, filtro por roster (20 países), filtro por `NumMentions ≥ 5`, hasta 2.751 días operativos
- [ ] 🟠 **3.M2-A** · **Fase 2** hereda el mismo problema + falta mencionar terciles y macro (VIX, DXY, USA macro). «Neutralidad» / «neutro»: alinear con el resto del documento
- [ ] 🟠 **3.M3-A** · **Fase 3** dice «snapshots diarios». La decisión de §4.2.1 es **grafo persistente con decay por QuadClass + ventana 60 días**, no snapshots. Reescribir
- [ ] 🟠 **3.M4-A** · **Fase 4** cierra abstracta. Declarar la decisión: **HeteroGAT con GATv2 vía HeteroConv + integración del S&P 500 como nodo del grafo** (§4.2.2, §4.2.3)
- [ ] 🔴 **3.M5-A** · **Fase 5** olvida walk-forward, semillas y Sharpe. Reescribir:

  > «Entrenamiento con esquema walk-forward de 10 folds expansivos, embargo cero, 250 sesiones de validación por fold, promediando sobre 3 semillas (0, 1, 2). Evaluación mediante métricas de clasificación (exactitud, F1 macro, matriz de confusión, precisión y recall por clase) y evaluación financiera complementaria mediante estrategia simulada (ratio de Sharpe).»

---

## 3 · Piezas que faltan por completo

- [ ] 🟡 **3.CRON-A** · Añadir **cronograma** (tabla de tres columnas: fase / semanas / hitos) usando fechas reales del historial de commits
- [ ] 🟡 **3.HERR-A** · Añadir el **stack técnico**: Python, PyTorch, PyTorch Geometric, pandas, entorno de ejecución (Colab GPU T4 + local CPU). Citar notebooks `01_entrenamiento_colab.ipynb` y `02_entrenamiento_local.ipynb`
- [ ] 🟡 **3.GRUPO-A** · Frase final que remita a la sección inicial «Organización del trabajo en grupo». Acota autoría de las cinco fases

---

## 4 · Formas

- [ ] ⚪ **3.F-A** · «neutralidad» vs «neutro»: unificar. *(ya en el checklist §5 del cap. 4)*
- [ ] ⚪ **3.F-B** · «snapshots» → «instantáneas» o «estados diarios del grafo». Desaparece si se aplica 3.M3-A
- [ ] ⚪ **3.F-C** · «predicción triclase» sin definir en la primera aparición. Añadir «(subida, neutro, bajada)» la primera vez
- [ ] ⚪ **3.F-D** · Revisar el punto final de los seis OE (ahora son OE1-OE6, no cuatro)

---

## 5 · Incoherencias con otros capítulos

- [ ] 🟠 **X-Cap3-1** · OE1 ya está reescrito, pero la **Fase 1** de la metodología sigue con la versión antigua. Aplicar 3.M1-A y comprobar que ambos digan lo mismo: periodo continuo 2015-2025, roster de 20 países, `NumMentions ≥ 5`, 2.751 días operativos

---

## 6 · Verificaciones

- [ ] ¿Se hizo alguna forma de **revisión manual** del grafo durante el desarrollo? Es la única que no se puede contestar desde el repositorio. Si se hizo (aunque fuera inspeccionar a ojo un día de aristas), documentarla en §4; si no, OE2 ya está bien como está, porque habla de validación cuantitativa

**Resueltas (2026-09-03), no hace falta repetirlas:**

- **No existe predicción en vivo.** No hay script ni notebook que, dado un día, produzca la predicción del siguiente. OE3 hace bien en hablar de flujo reproducible offline: **no reintroducir** la promesa de «señal antes de la apertura» al reescribir la Fase 3
- **Hitos reales** para el cronograma de 3.CRON-A: la tabla ya está montada en [GUIA_REVISION_TFM.md](GUIA_REVISION_TFM.md) §6, a partir de `git log`

---

*Método: cuando una tarea se resuelve se **borra** de esta lista, no se marca. Lo que aparece aquí es exactamente lo que queda por hacer. El historial vive en git.*
