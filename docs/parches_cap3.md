# Parches de texto · Capítulo 3

Texto listo para pegar en `EntregaFINAL_TFM_Aguiló_Martín.docx`. Los identificadores son los de [checklist_capitulo3.md](checklist_capitulo3.md).

---

## 3.M1-A 🔴 · Fase 1 — reescritura

**Apartado:** §3.3 Metodología del trabajo. La descripción vigente hereda el problema de OE1 al hablar de «selección de periodos históricos relevantes»: no hubo selección, se ingirió el histórico completo. También omite los dos filtros y la cifra final de días operativos que sostiene todo lo que viene después.

**DICE:**

> Fase 1. Construcción del dataset geopolítico: Selección de periodos históricos relevantes dentro de GDELT, extracción de datos y preprocesamiento.

**ESCRIBE:**

> Fase 1. Construcción del dataset geopolítico: ingesta continua del histórico 2015-2025 de GDELT 1.0 Events, filtrado por roster de veinte países y por umbral de cobertura mediática (`NumMentions ≥ 5`), y preprocesamiento hasta obtener el dataset de 2.751 días operativos que alimenta las fases siguientes.

**Por qué:**

- «Selección de periodos» describe un diseño (elegir ventanas geopolíticamente relevantes) que la ejecución no siguió. El pipeline real recorre todo el rango 2015-2025 sin ventanas.
- El roster de veinte países y el umbral `NumMentions ≥ 5` son las dos operaciones que definen el dataset y no aparecen aquí. Están en `src/datos/preprocesar.py` (`filtrar_roster`, `filtrar_por_cobertura`).
- 2.751 días operativos es la cifra que enlaza esta fase con el capítulo 4 y con la evaluación walk-forward de la Fase 5. Sin ella, la metodología queda desconectada de los resultados.

**Consistencia:** aplicar simultáneamente con la reescritura de OE1 (§3.2). Ambos textos han de decir lo mismo — es lo que exige `X-Cap3-1` de la revisión cruzada.

---

## 3.M2-A 🟠 · Fase 2 — reescritura

**Apartado:** §3.3, Fase 2. Hereda «los mismos periodos seleccionados» de la Fase 1 y no menciona ni los indicadores complementarios (VIX, DXY, macro USA), ni la construcción por terciles del target. «Neutralidad» debe alinearse con el término elegido en la pasada global (checklist cap. 4 §5).

**DICE:**

> Fase 2. Construcción del dataset financiero: Obtención de datos históricos del S&P 500 para los mismos periodos seleccionados en la fase anterior. Definición de la variable objetivo: clasificación triclase (subida, bajada, neutralidad) del índice para la siguiente sesión.

**ESCRIBE:**

> Fase 2. Construcción del dataset financiero: descarga de la serie diaria del S&P 500 y de los indicadores complementarios (VIX, DXY e indicadores macro de EE. UU. vía FRED) para el mismo periodo 2015-2025. La variable objetivo es una clasificación triclase (subida, neutro, bajada) del retorno cierre-a-cierre de la sesión siguiente, construida por terciles del retorno estimados sobre el tramo de entrenamiento de cada fold (§4.3.5).

**Por qué:**

- Los tres indicadores complementarios están implementados en `src/datos/descarga_financiero.py` (`TICKER_VIX`, `TICKER_DXY`, `descargar_macro_fred`) y llegan al modelo vía `dataset.py`. No mencionarlos deja la Fase 2 incompleta.
- La etiqueta por terciles (`etiquetas.py:117`, modo `"terciles"`) es la decisión clave del target y §3 no la nombra. Se calcula sobre el train de cada fold para evitar fuga.
- «Neutro» (adjetivo entre sustantivos «subida, bajada») es lo que usa §4.3.1. Unificar aquí evita mantener dos términos.

---

## 3.M3-A 🟠 · Fase 3 — reescritura

**Apartado:** §3.3, Fase 3. La fase habla de «snapshots diarios», que evoca un DTDG puro. La decisión de §4.2.1 es un grafo persistente con refuerzo y decaimiento exponencial por QuadClass; el fichero por día es el estado acumulado, no un snapshot independiente.

**DICE:**

> Fase 3. Diseño y construcción del grafo geopolítico: Definición de qué entidades constituyen los nodos, qué eventos forman las aristas y qué atributos de GDELT se asignan como características. Generación de snapshots diarios del grafo.

**ESCRIBE:**

> Fase 3. Diseño y construcción del grafo geopolítico: definición de los nodos (países del roster y S&P 500), de las aristas (relaciones país-país generadas por los eventos de GDELT) y de los atributos asignados a cada entidad. El grafo se construye como una única estructura persistente cuya memoria se actualiza día a día mediante un mecanismo de refuerzo por nuevos eventos y de decaimiento exponencial por categoría de QuadClass sobre una ventana operativa de sesenta días (§4.2.1).

**Por qué:**

- «Snapshots diarios» describe una familia (DTDG) que §2.2.4 y §4.2.1 descartan explícitamente. Mantener el término contradice la decisión de arquitectura.
- Nombrar el mecanismo (refuerzo + decaimiento por QuadClass, ventana 60 días) alinea la fase con §4.2.1 y con `src/modelo/decay.py`.
- Incluir S&P 500 entre los nodos anticipa la Fase 4 y evita presentar la integración como algo posterior.

---

## 3.M4-A 🟠 · Fase 4 — reescritura

**Apartado:** §3.3, Fase 4. Correcta pero abstracta: en una memoria cerrada, la fase de diseño arquitectural debe nombrar la decisión adoptada.

**DICE:**

> Fase 4. Diseño e implementación del modelo: Evaluación de diferentes arquitecturas de GNN y diseño del mecanismo de fusión entre la información geopolítica del grafo y la información financiera del S&P 500.

**ESCRIBE:**

> Fase 4. Diseño e implementación del modelo: evaluación de arquitecturas de GNN para grafos heterogéneos y elección del mecanismo de integración con la señal del mercado. La familia arquitectural finalmente adoptada es HeteroGAT con capas GATv2 encapsuladas en `HeteroConv`, y el S&P 500 se integra como nodo adicional dentro del grafo heterogéneo, evitando la *late fusion* (§4.2.2, §4.2.3).

**Por qué:**

- HeteroGAT con GATv2 vía `HeteroConv` es la arquitectura implementada en `src/modelo/arquitectura.py` y ya justificada en §4.2.3.
- La integración como nodo (frente a *late fusion*) es la decisión que §2.3 y §4.2.2 fijan; nombrarla aquí cierra la fase sin dejarla abstracta.

---

## 3.M5-A 🔴 · Fase 5 — reescritura

**Apartado:** §3.3, Fase 5. Omite las tres decisiones metodológicas más importantes del trabajo (walk-forward, semillas, evaluación financiera) y llama métrica principal a «precisión y recall», que se reportan por clase pero no son las principales (F1 macro sí).

**DICE:**

> Fase 5. Entrenamiento y evaluación: Entrenamiento con los datos históricos seleccionados y evaluación del rendimiento mediante métricas de clasificación como accuracy, F1-score, precisión y recall.

**ESCRIBE:**

> Fase 5. Entrenamiento y evaluación: entrenamiento con esquema walk-forward de diez folds expansivos con embargo cero y 250 sesiones de validación por fold, promediando los resultados sobre tres semillas (0, 1, 2) para reportar la dispersión entre ejecuciones. La evaluación combina métricas de clasificación —exactitud, F1 macro (métrica principal), matriz de confusión y precisión y recall por clase— con una evaluación financiera complementaria basada en una estrategia de inversión simulada sobre las predicciones del modelo, cuyo indicador de referencia es el ratio de Sharpe (§5.4).

**Por qué:**

- Walk-forward, semillas y evaluación financiera son las tres piezas que sostienen todo el capítulo 5. Sin ellas la Fase 5 queda desconectada de los resultados.
- Walk-forward 10 folds expansivos, embargo 0, 250 sesiones de validación por fold y semillas {0, 1, 2}: implementado en `src/entrenamiento/walkforward.py` y `loop.py`.
- F1 macro es la métrica principal (`evaluacion.py:105`); «precisión y recall» son por clase.
- El ratio de Sharpe se calcula en la evaluación financiera de §5.4 y no aparecía en la fase.

---
