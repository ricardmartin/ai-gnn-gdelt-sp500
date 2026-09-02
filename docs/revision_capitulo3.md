# Revisión del capítulo 3 de la memoria

**Fecha:** 2026-09-02
**Documento revisado:** `EntregaFINAL_TFM_Aguiló_Martín.docx`
**Contrastado contra:** capítulo 4 (decisiones ejecutadas), capítulo 5 (resultados), capítulo 6 (limitaciones asumidas) y el código en HEAD.
**Alcance:** capítulo 3 completo (Objetivo general + 4 objetivos específicos + 5 fases de metodología).

## Cómo leer este documento

Cada hallazgo lleva identificador, severidad, **DÓNDE** está (frase literal) y **QUÉ** hay que poner.

| Severidad | Significado |
|---|---|
| 🔴 **ERROR** | El objetivo o la fase promete algo que el trabajo no hizo, o que quedó descartado durante la ejecución. |
| 🟠 **ALINEACIÓN** | Incoherencia con capítulos 4-6. |
| 🟡 **MEJORA** | Hueco argumental, cronograma ausente, métricas incompletas. |
| ⚪ **FORMA** | Errata, formato, catalanismo, numeración. |

**Recuento:** 6 errores · 3 alineaciones · 5 mejoras · 4 formas = **18 puntos**.

Este capítulo es breve (una página), pero contiene el problema más comprometido del documento a nivel académico: **tres de los cuatro objetivos específicos no coinciden con el trabajo ejecutado**. Un tribunal que lea §3 y luego §5-§6 detectará el desfase inmediatamente.

## Ya corregido desde la versión anterior

Nada específico a este capítulo. El párrafo introductorio de §3 no se ha revisado en pasadas anteriores.

---

# 1. Objetivo general

Está bien formulado y coincide con el trabajo ejecutado.

### 🟡 3.OG-A · Consistencia con «S&P 500» / «SP500»

**DÓNDE:** «predicción de la dirección del **S&P 500** basado en redes neuronales de grafos».

**QUÉ PASA:** el capítulo 3 usa «S&P 500» con espacio, el capítulo 5 tiende a «SP500» sin espacio. Es la misma decisión de estilo que se recoge en el checklist del capítulo 4 (§5), y afecta al objetivo general, que es la frase más citable del trabajo.

**QUÉ HACER:** unificar en todo el documento. Cualquiera de los dos es defendible, pero uno solo.

---

# 2. Objetivos específicos

Son cuatro. **Tres de los cuatro tienen un problema serio de correspondencia con lo ejecutado.** Este es el hallazgo más grave del capítulo.

## 🔴 3.OE1-A · «Periodos históricos geopolíticamente relevantes» no se seleccionaron

**DÓNDE:** OE1 — «Definir y seleccionar un conjunto de **periodos históricos geopolíticamente relevantes** dentro de GDELT que permitan construir un dataset representativo y manejable para el entrenamiento del modelo.»

**QUÉ PASA:** el trabajo no seleccionó «periodos geopolíticamente relevantes». Usa el periodo **continuo 2015-2025**, sin cortes ni selección temática. El dataset son 2.751 grafos diarios (2015-01-01 a 2025-06-30 aproximadamente), como confirma el capítulo 5.

La formulación de OE1 corresponde a un diseño distinto —selección de episodios (Ucrania, Brexit, COVID, etc.) para entrenar sobre eventos concretos— que se descartó en favor del entrenamiento sobre serie continua.

**QUÉ HACER:** reescribir OE1 para reflejar lo que sí se hizo: **construir un dataset diario continuo del periodo 2015-2025 sobre un roster fijo de 20 países**. El concepto de «periodos relevantes» pertenece a una versión anterior del diseño.

## 🔴 3.OE2-A · «Revisión manual de una muestra representativa» no está documentada

**DÓNDE:** OE2 — «Diseñar la representación en grafo de las relaciones entre actores geopolíticos, definiendo nodos, aristas y atributos, y validando el resultado mediante una **revisión manual de una muestra representativa**.»

**QUÉ PASA:** ni el capítulo 4 ni el 5 recogen una revisión manual del grafo. El diseño de nodos, aristas y atributos sí está documentado (§4.2.2 a §4.2.4, §4.3.2), pero la parte de «validación mediante revisión manual» no aparece en ningún sitio del documento. O se hizo y no se subió, o no se hizo.

**QUÉ HACER:** dos opciones honestas.
- Si se hizo (por ejemplo, se abrieron manualmente varios días para comprobar que las aristas más pesadas correspondían a eventos reales): recogerlo en un párrafo de §4.1 o §5, con una tabla de ejemplo (día, arista más pesada, evento que la generó).
- Si no se hizo: reformular OE2 quitando la validación manual y sustituirla por una validación cuantitativa (distribución de grados, distribución por QuadClass, top 10 pares origen-destino), que sí es material que existe o puede generarse en media hora.

## 🔴 3.OE3-A · «Predicción diaria antes de la apertura» no se automatizó

**DÓNDE:** OE3 — «**Automatizar la predicción diaria** del modelo, verificando que sea capaz de generar una señal de inversión **antes de la apertura de cada sesión bursátil**.»

**QUÉ PASA:** dos problemas:

1. **No hay pipeline en vivo.** El código entrena y evalúa retrospectivamente sobre el dataset histórico. No existe un notebook o script programado que se ejecute cada día antes de la apertura, ni un `README` que documente cómo hacerlo funcionar así.

2. **La etiqueta no es «antes de la apertura».** En la definición operativa (ver §4.1-C y §4.3.5), la etiqueta se calcula sobre **retorno cierre-a-cierre de t+1**, no sobre la apertura. Además, el corte horario diseñado para «antes de la apertura» resulta inerte con GDELT 1.0 porque el campo `DATEADDED` de 1.0 no tiene resolución intradía (ver 4.1-C).

**QUÉ HACER:** reformular OE3 en términos de lo que sí se hizo. Dos posibilidades:
- «Diseñar un flujo reproducible desde la ingesta de GDELT hasta la evaluación, que permita generar predicciones diarias offline sobre un histórico completo».
- «Verificar que la construcción del grafo del día t utiliza únicamente información disponible antes del cierre del mercado de esa jornada, para que la predicción de t+1 sea temporalmente válida».

La segunda es más honesta con la cadencia diaria de 1.0 y no promete un pipeline en vivo que no existe.

## 🔴 3.OE4-A · «F1 superior al modelo sin información geopolítica» apunta a un baseline que no se construyó

**DÓNDE:** OE4 — «Implementar la integración de la GNN con los datos históricos del S&P 500 para la predicción triclase, alcanzando un **F1-score superior al de un modelo de referencia sin información geopolítica**.»

**QUÉ PASA:** este es el mismo hallazgo **X-1** de `revision_capitulo4.md`. §4.3.6 promete cinco baselines (trivial, LR, XGBoost, LSTM financiera, baseline con datos financieros + señal geopolítica sin grafo). §5.3 evalúa tres (trivial, LR, XGBoost). El baseline específico «datos financieros sin información geopolítica» es la LSTM financiera, y **no se construyó** (el capítulo 6 ya lo admite).

Concretamente: XGBoost usa las features del grafo aplanadas (agregados de GDELT). No es un modelo «sin información geopolítica». La regresión logística tampoco. El baseline naive es trivial.

Es decir: OE4 se apoya en un experimento que el capítulo 6 declara no ejecutado. Un tribunal cerrará el círculo entre §3 y §6 y verá el hueco.

**QUÉ HACER:** dos opciones.
- **Reformular OE4** en términos de baselines efectivamente construidos: superar el baseline trivial y aproximarse a modelos clásicos con features aplanadas. Es una promesa más modesta pero verificable.
- **Mantener la formulación actual** y declarar en §7.1 en qué grado se cumplió OE4, reconociendo que la comparación específica frente a un modelo sin señal geopolítica queda como línea futura. El capítulo 6 ya prepara este movimiento.

La primera opción es más limpia. La segunda respeta la ambición del planteamiento original.

## 🔴 3.OE-B · Los objetivos específicos no están numerados

**DÓNDE:** los cuatro objetivos son párrafos consecutivos sin identificador («OE1», «OE2», etc.).

**QUÉ PASA:** el capítulo 4 (§X-1 en la revisión previa) y el propio checklist se refieren a «el objetivo específico 4», pero el lector no puede localizarlo rápido porque no hay numeración explícita. Es un problema de forma que afecta a la trazabilidad.

**QUÉ HACER:** añadir «OE1:», «OE2:», «OE3:», «OE4:» al inicio de cada viñeta, o convertirlos en lista numerada. Facilita las referencias cruzadas y la lectura del capítulo 7.

---

# 3. Metodología del trabajo

Cinco fases. La estructura es correcta y las fases están razonablemente ordenadas. Los problemas son de detalle: qué se dice y qué falta.

## 🔴 3.M1-A · Fase 1 arrastra el problema de OE1

**DÓNDE:** Fase 1 — «**Selección de periodos históricos relevantes** dentro de GDELT, extracción de datos y preprocesamiento.»

**QUÉ PASA:** mismo problema que OE1. No hubo selección de periodos.

**QUÉ HACER:** reescribir como «Ingesta del histórico completo 2015-2025 de GDELT 1.0, filtrado por roster de 20 países y por umbral de cobertura (`NumMentions ≥ 5`), y preprocesamiento hasta obtener el dataset de 2.751 días operativos».

## 🟠 3.M2-A · Fase 2 arrastra la misma referencia y añade el desalineo del target

**DÓNDE:** Fase 2 — «Obtención de datos históricos del S&P 500 para los mismos periodos seleccionados en la fase anterior. Definición de la variable objetivo: clasificación triclase (subida, bajada, **neutralidad**) del índice para la siguiente sesión.»

**QUÉ PASA:** dos cosas.
- «Los mismos periodos seleccionados» hereda el problema de OE1/Fase 1.
- «Neutralidad» es el término del capítulo 5. Pero §4.3.1 dice «neutro». Es la misma incoherencia de vocabulario del checklist del capítulo 4 (§5, pasada global). Aquí conviene alinear al término que se use en el resto del documento tras la unificación.

**QUÉ HACER:** reescribir como «Descarga de datos históricos del S&P 500 y de indicadores complementarios (VIX, DXY, macro USA) para el mismo periodo, y construcción de la etiqueta triclase por terciles del retorno cierre-a-cierre de t+1». Incluye la operación de terciles (§4.3.5) que ahora falta.

## 🟠 3.M3-A · Fase 3 dice «snapshots diarios», la decisión final es distinta

**DÓNDE:** Fase 3 — «Definición de qué entidades constituyen los nodos, qué eventos forman las aristas y qué atributos de GDELT se asignan como características. **Generación de snapshots diarios del grafo**.»

**QUÉ PASA:** §4.2.1 cerró la decisión en un **único grafo persistente con memoria decaimiento-refuerzo**, no en snapshots diarios independientes. Operativamente sí hay un fichero por día (2.751 grafos), pero cada uno se construye a partir del acumulado con decay, no como un DTDG puro.

**QUÉ HACER:** dos frases.
- «Construcción, para cada día del periodo, del estado del grafo persistente aplicando refuerzo y decaimiento exponencial por QuadClass (§4.2.1)».
- Mencionar la ventana operativa de 60 días si se quiere dar contexto operativo aquí.

## 🟠 3.M4-A · Fase 4 no menciona que se acabó eligiendo GATv2 vía HeteroConv

**DÓNDE:** Fase 4 — «Evaluación de diferentes arquitecturas de GNN y diseño del mecanismo de fusión entre la información geopolítica del grafo y la información financiera del S&P 500.»

**QUÉ PASA:** correcto pero abstracto. En un capítulo de metodología cerrada (el trabajo ya se hizo) tiene sentido nombrar la decisión: HeteroGAT con GATv2 vía HeteroConv, e integración del S&P 500 como nodo del grafo (no late fusion).

**QUÉ HACER:** una línea que cierre la fase: «La familia arquitectural finalmente adoptada es HeteroGAT con GATv2 vía HeteroConv, y el S&P 500 se integra como nodo adicional dentro del grafo heterogéneo (§4.2.2 y §4.2.3)».

## 🔴 3.M5-A · Fase 5 no menciona walk-forward, ni semillas, ni evaluación financiera

**DÓNDE:** Fase 5 — «Entrenamiento con los datos históricos seleccionados y evaluación del rendimiento mediante métricas de clasificación como **accuracy, F1-score, precisión y recall**.»

**QUÉ PASA:** faltan las tres decisiones metodológicas más importantes del trabajo, todas ya ejecutadas.
- **Walk-forward** con 10 folds expansivos, embargo 0, 250 sesiones de validación por fold. Es el esquema de validación que define el rigor temporal del trabajo.
- **Tres semillas (0, 1, 2)** con reporte de dispersión.
- **Evaluación financiera** (Sharpe ratio, ver §5.4). El capítulo 3 la lista como métrica de clasificación pero no la nombra.

Además, «precisión y recall» se reportan por clase pero no son la métrica principal (que es F1-macro).

**QUÉ HACER:** reescribir la fase completa:

> «Fase 5. Entrenamiento y evaluación. Entrenamiento con esquema walk-forward de 10 folds expansivos con embargo cero y 250 sesiones de validación por fold, promediando resultados sobre 3 semillas (0, 1, 2). Evaluación mediante métricas de clasificación (exactitud, F1 macro, matriz de confusión, precisión y recall por clase) y evaluación financiera complementaria mediante una estrategia de inversión simulada basada en las predicciones del modelo (ratio de Sharpe).»

Esta reescritura convierte una fase abstracta en la fase que sostiene todo el capítulo 5.

---

# 4. Piezas que faltan por completo

## 🟡 3.CRON-A · No hay cronograma ni diagrama de Gantt

**DÓNDE:** ausencia.

**QUÉ PASA:** una memoria de TFM suele incluir un cronograma con hitos, y este capítulo es el lugar natural para meterlo. Sin él, la sección de metodología se queda en cinco viñetas sin contexto temporal.

**QUÉ HACER:** una tabla de tres columnas —fase / semanas / hitos— con las fechas reales del trabajo. Es material fácil de recuperar del historial de commits (`git log`) y sube el nivel del capítulo.

## 🟡 3.HERR-A · No se listan las herramientas técnicas

**DÓNDE:** ausencia.

**QUÉ PASA:** el capítulo no menciona Python, PyTorch, PyTorch Geometric, notebooks Colab/local, hardware usado. Todo esto es información metodológica que un tribunal puede pedir.

**QUÉ HACER:** un párrafo final o una viñeta bajo Fase 4 que enumere el stack: Python 3.x, PyTorch, PyTorch Geometric, pandas, ejecutado sobre Colab (GPU T4) y en local (CPU). Los notebooks concretos (`01_entrenamiento_colab.ipynb`, `02_entrenamiento_local.ipynb`) pueden citarse por nombre.

## 🟡 3.GRUPO-A · La sección «Organización del trabajo en grupo» está delante del capítulo 3 pero no se enlaza

**DÓNDE:** el documento tiene una sección «Organización del trabajo en grupo / Partes que aborda el TFE» antes del capítulo 1, pero el capítulo 3 no la referencia.

**QUÉ PASA:** al ser un TFM en grupo, la metodología debería incluir una línea que remita a esa sección para dejar claro qué partes cubre cada miembro del equipo. Sin esa remisión, la sección inicial queda huérfana y la metodología del capítulo 3 queda sin acotación de autoría.

**QUÉ HACER:** una frase al final del capítulo 3 que remita a la sección inicial y aclare que las cinco fases descritas se han desarrollado bajo el reparto ahí especificado.

---

# 5. Alineación con otros capítulos

## 🟠 X-Cap3-1 · OE1/Fase 1 vs realidad del dataset

Ver 3.OE1-A y 3.M1-A. Es el mismo problema en dos formulaciones distintas: el diseño original preveía selección de periodos, la ejecución final usó continuo. Necesitan corregirse a la vez.

## 🟠 X-Cap3-2 · OE4 vs §5.3 y §6

Ver 3.OE4-A. Es el mismo problema que X-1 en `revision_capitulo4.md`. §3, §4.3.6 y §6 tienen que decir lo mismo tras la corrección. Consolidar todos los cambios en un solo pase.

## 🟠 X-Cap3-3 · OE3 vs §4.1-C y §4.3.5

Ver 3.OE3-A. La promesa de «antes de la apertura» aterriza en §4.3.5 con el mecanismo de corte horario, que a su vez es inerte con GDELT 1.0 (§4.1-C). Los tres apartados hablan de la misma decisión inejecutable y hay que reformularlos coordinados.

---

# 6. Formas

## ⚪ 3.F-A · «neutralidad» vs «neutro»

Ver 3.M2-A y el checklist del capítulo 4 (§5). El capítulo 3 usa «neutralidad», el capítulo 4 alterna. Unificar en un solo pase.

## ⚪ 3.F-B · La Fase 3 dice «snapshots»

Anglicismo. En castellano, «instantáneas» o «estados del grafo por día». En la práctica, si se reescribe la fase como propone 3.M3-A, la palabra desaparece.

## ⚪ 3.F-C · «triclase» sin definir en la primera aparición

**DÓNDE:** OE4 y Fase 2 hablan de «predicción triclase» / «clasificación triclase» sin haberlo definido antes en este capítulo.

**QUÉ HACER:** en la primera aparición, añadir la definición entre paréntesis: «predicción triclase (subida, neutro, bajada)».

## ⚪ 3.F-D · Falta punto final en OE1

**DÓNDE:** OE1 termina en «...manejable para el entrenamiento del modelo.»

Al releerlo tiene punto. Pero el checklist original del cap. 4 identificaba varias frases sin punto en distintos apartados. Revisar los cuatro OE de un tirón.

---

# 7. Orden de trabajo recomendado

## Bloque 1 — Los objetivos específicos, en un solo pase

1. **3.OE-B** · Añadir numeración OE1-OE4.
2. **3.OE1-A + 3.M1-A** · Reescribir OE1 y Fase 1 en términos del periodo continuo 2015-2025.
3. **3.OE2-A** · Decidir: recoger validación manual (si existe) en §4-§5, o reformular OE2 con validación cuantitativa.
4. **3.OE3-A** · Reformular OE3 para no prometer pipeline en vivo. Alinear con §4.1-C y §4.3.5.
5. **3.OE4-A + X-1 (ch4) + §6** · Reescribir OE4 y §4.3.6 y §6 en el mismo commit, para que los tres digan lo mismo sobre baselines.

## Bloque 2 — La metodología, alineada con lo ejecutado

6. **3.M2-A** · Reescribir Fase 2 con datos financieros + macro + terciles.
7. **3.M3-A** · Reescribir Fase 3 con grafo persistente + decay por QuadClass + ventana 60 días.
8. **3.M4-A** · Cerrar Fase 4 con la decisión de HeteroGAT + GATv2 + integración de nodo mercado.
9. **3.M5-A** · Reescribir Fase 5 con walk-forward + semillas + Sharpe.

## Bloque 3 — Piezas que faltan

10. **3.CRON-A** · Añadir cronograma o tabla de hitos.
11. **3.HERR-A** · Añadir stack técnico.
12. **3.GRUPO-A** · Enlazar con la sección de reparto de trabajo en grupo.

## Bloque 4 — Formas

13. **3.OG-A** y **3.F-A** · Pasadas globales de «S&P 500» / «SP500» y «neutralidad» / «neutro».
14. **3.F-B**, **3.F-C**, **3.F-D** · Snapshots, triclase sin definir, puntos finales.

---

# Anexo · Alineación objetivo por objetivo

| Objetivo | Formulación actual | Ejecutado | Consistencia |
|---|---|---|---|
| OE1 | Seleccionar periodos históricos relevantes | Periodo continuo 2015-2025 | 🔴 No |
| OE2 | Diseñar el grafo + revisión manual | Grafo diseñado (§4.2), revisión manual no documentada | 🔴 Parcial |
| OE3 | Automatizar predicción antes de la apertura | Pipeline retrospectivo, sin apertura, sin en vivo | 🔴 No |
| OE4 | F1 superior al modelo sin información geopolítica | Baseline sin información geopolítica no construido | 🔴 No |
| OG  | Diseñar, implementar y evaluar el modelo | Hecho | ✅ Sí |

Es decir: el objetivo general se cumplió, pero los cuatro específicos han quedado descolgados de la realidad del trabajo. Este capítulo es el más urgente de reescribir después de los errores de hecho del capítulo 4.
