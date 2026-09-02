# Revisión cruzada · Capítulos 2, 3 y 4

**Fecha:** 2026-09-02
**Alcance:** contradicciones directas y errores críticos que solo emergen al leer los tres capítulos juntos. No se repiten los hallazgos internos ya recogidos en `revision_capitulo2.md`, `revision_capitulo3.md` y `revision_capitulo4.md`.

## Cómo leer este documento

Cada contradicción cruza dos o más capítulos. Se indica en qué apartado de cada capítulo aparece la afirmación, qué dice cada uno, y por qué no pueden ser simultáneamente ciertas.

| Severidad | Significado |
|---|---|
| 🔥 **CRÍTICO** | Un tribunal que lea los dos apartados enfrentados detecta el desfase inmediatamente. Bloquea la defensa. |
| 🟥 **GRAVE** | Contradicción evidente, no bloqueante pero comprometida. |
| 🟧 **MODERADO** | Incoherencia recuperable con una frase de puente. |

**Recuento:** 8 críticos · 6 graves · 5 moderados = **19 contradicciones cruzadas**.

---

# 1. Contradicciones críticas (🔥)

Ordenadas por daño reputacional en una defensa.

## 🔥 C-1 · Los cuatro objetivos específicos vs la ejecución

**Dónde se choca:**
- **§3** define OE1, OE2, OE3, OE4.
- **§4** describe cómo se ejecutó cada uno.
- **§5, §6** reportan lo obtenido.

**Contradicción:**

| Objetivo | §3 promete | §4-§5-§6 hicieron | ¿Coherente? |
|---|---|---|---|
| OE1 | Seleccionar **periodos geopolíticamente relevantes** | Periodo continuo 2015-2025, 2.751 días | 🔥 No |
| OE2 | Diseño + **revisión manual** de muestra | Diseño ejecutado (§4.2), revisión no documentada | 🔥 No |
| OE3 | **Automatizar predicción antes de la apertura** | Pipeline offline, etiqueta cierre-a-cierre, corte horario inerte (§4.1-C) | 🔥 No |
| OE4 | Superar F1 de **modelo sin información geopolítica** | Baseline geopolítico sin grafo **no construido** (§6 lo admite) | 🔥 No |

**Por qué importa:** un tribunal empieza la lectura por §3 para saber qué se propone, y luego cruza con §5-§6 para juzgar si se cumple. Cuatro de cuatro objetivos específicos descolgados es la clase de error que decide la nota.

**Consolidar en:** un único pase que toque §3 (OE1-OE4), §4.3.6 (fase de baselines), §5.3 (tabla comparativa) y §6 (asunción de limitación). Todos deben decir lo mismo.

## 🔥 C-2 · «HGT» como modelo empleado en cuatro apartados, pero se usó GATv2

**Dónde se choca:**
- **§2.2.3** describe HATS (basado en GAT jerárquico), Chen et al. (GNN + LSTM), FSTGAT (GAT mejorado). No menciona HGT.
- **§4.2.3** cierra la decisión en **HeteroGAT con GATv2** (Brody et al. 2022), no HGT.
- **§4.2.2, §4.2.4, §4.3.4** siguen diciendo «HGT» **cuatro veces** como si fuera el modelo utilizado.

**Contradicción:** §4.2.3 anuncia una decisión que el resto del capítulo 4 ignora. Además, HGT no está en §2 en absoluto: aparece por primera vez en §4.2.3 y ya como opción descartada, sin justificación previa en el estado del arte.

**Por qué importa:** el capítulo 4 se contradice consigo mismo, y §2 no prepara al lector para nombres que aparecen sin fondo teórico.

**Consolidar en:** buscar y reemplazar «HGT» en las cuatro ocurrencias identificadas (§4.2.2, §4.2.4, §4.3.4 ×2) → «GATv2». Y en §2.2.3 añadir una línea que marque qué hereda el trabajo de FSTGAT (variante de GAT sobre grafo dinámico).

## 🔥 C-3 · «Antes de la apertura» / corte horario / cierre-a-cierre — tres apartados con tres descripciones distintas

**Dónde se choca:**
- **§3 OE3** promete «señal de inversión **antes de la apertura de cada sesión bursátil**».
- **§4.3.5** describe el corte de las 16:00 America/New_York para separar información pre/post-cierre.
- **§4.1-C** demuestra que el corte horario **es inerte**: GDELT 1.0 no tiene resolución intradía en `DATEADDED`, todo colapsa a la fecha de publicación.
- El código calcula la etiqueta como **retorno cierre-a-cierre de t+1**.

**Contradicción en cadena:** OE3 promete apertura → §4.3.5 dice cierre + corte horario → §4.1-C revela que el corte no funciona → código usa cierre-a-cierre. **Ninguna de las cuatro descripciones coincide con las demás.**

**Por qué importa:** el mecanismo de anti-*leakage* es central en cualquier trabajo de predicción financiera. Que la memoria describa un mecanismo distinto en cada capítulo hunde la credibilidad de la disciplina temporal del experimento.

**Consolidar en:** decisión de fondo (declararlo bien redondeado): la cadencia diaria de GDELT 1.0 garantiza la separación temporal sin necesidad de corte horario. La etiqueta es cierre-a-cierre de t+1. OE3 se reformula sin «apertura», §4.3.5 se reformula sin corte, §4.1-C se declara como consecuencia coherente de la fuente elegida.

## 🔥 C-4 · Nodo USA con macro — §4.3.2 lo promete, el código no lo hace, §3 no lo menciona

**Dónde se choca:**
- **§4.3.2-E** describe «El nodo correspondiente a Estados Unidos constituye un caso especial: se contempla enriquecerlo con características macroeconómicas adicionales (tasa Reserva Federal, bonos Tesoro, inflación)».
- **Código** (`grafo.py:51`): todos los países llevan **las mismas 11 features**. Las macro USA acabaron en el nodo mercado (`grafo.py:57`), no en el nodo USA.
- **§4.3.2-F**: `USAR_MACRO = False` en el experimento del capítulo 5 — esas macro **están a cero**.
- **§3** no menciona nada de macro en USA.

**Contradicción:** §4.3.2 describe una arquitectura que no existe. Un tribunal que abra el repositorio buscando esas features no las encuentra.

**Por qué importa:** el error de hecho más comprometido del capítulo 4 (ver revisión).

**Consolidar en:** reescribir §4.3.2 con las 9 features reales del nodo mercado, declarando cuáles quedaron inactivas (DXY, macro con `USAR_MACRO = False`) y por qué.

## 🔥 C-5 · Baseline «sin información geopolítica»: propagado en 3 capítulos, no existe en 0

**Dónde se choca:**
- **§3 OE4**: «F1-score superior al de un **modelo de referencia sin información geopolítica**».
- **§4.3.6-F**: «Resulta particularmente relevante un baseline que combine los datos financieros con una señal geopolítica agregada pero sin estructura de grafo».
- **§5.3** evalúa tres baselines: naive, LR, XGBoost. **Todos usan features del grafo aplanadas** — es decir, sí tienen información geopolítica. Ninguno es «sin geopolítica».
- **§6** admite literalmente que los baselines adicionales «no se han construido en este piloto».

**Contradicción:** §3 y §4.3.6 lo prometen. §5 no lo aporta. §6 lo admite ausente. Cuatro apartados con cuatro posiciones distintas.

**Por qué importa:** OE4 es literalmente el criterio de éxito del trabajo. Que no exista el baseline que valida OE4 tira abajo la lógica de evaluación.

**Consolidar en:** reescribir OE4 y §4.3.6-F para que promitan lo que sí se construyó (superar baselines aplanados). Y §6 se puede mantener como está, o suavizar. Los tres apartados dicen entonces lo mismo.

## 🔥 C-6 · LSTM financiera: prometida en §3 y §4.3.6, ausente en §5

**Dónde se choca:**
- **§3 Fase 5** habla de «entrenamiento y evaluación» sin nombrar baselines concretos, pero deja el gancho.
- **§4.3.6-E**: «modelos de series temporales como una **LSTM alimentada únicamente con datos financieros**».
- **§5.3**: no hay LSTM. El `src/modelo/baselines.py` solo tiene `BaselineNaive`, `entrenar_logistica`, `entrenar_xgboost`.

**Contradicción:** §4.3.6 la lista como baseline. §5.3 la omite. §6 lo admite implícitamente al hablar de «modelos de referencia adicionales que no se han construido».

**Por qué importa:** un lector que va a §5.3 buscando la LSTM anunciada en §4.3.6 no la encuentra y descubre el hueco antes de llegar a §6.

**Consolidar en:** mismo commit que C-5.

## 🔥 C-7 · «Crecimiento exponencial de fuentes» — §2.1.3 y §5 lo afirman, los datos del propio trabajo lo desmienten

**Dónde se choca:**
- **§2.1.3**: «el crecimiento exponencial de fuentes se debe a la inclusión de webs y otras fuentes contemporáneas, lo que crea una situación en la que en la actualidad se registran más eventos que en el pasado».
- **§5**: «el número de fuentes y de eventos capturados crece de forma acusada con el tiempo… los años más recientes presentan una cobertura considerablemente más densa».
- **Datos del propio dataset**: eventos por año **caen** desde 2016 (2016: 2.927.300 → 2025: 1.396.372).

**Contradicción:** una afirmación cualitativa que los datos cuantitativos del capítulo del que forma parte contradicen directamente. Además, §5 usa la afirmación para justificar el rango 2015-2025, cuando los datos invierten el argumento.

**Por qué importa:** un tribunal con el gráfico de eventos por año lo ve en 10 segundos.

**Consolidar en:** corregir en §2.1.3 y §5 en el mismo pase. Meter el gráfico de eventos por año en §4.1 como evidencia. Convertir la afirmación en «la cobertura de GDELT 1.0 se estabiliza y decrece ligeramente tras 2016, tras el relevo de 2.0».

## 🔥 C-8 · Los baselines: §4 promete 5, §5 evalúa 3, §3 y §6 no coinciden

**Dónde se choca:**
- **§3** no fija cuántos baselines.
- **§4.3.6** lista **5**: trivial, LR, XGBoost, LSTM financiera, baseline geopolítico agregado sin grafo.
- **§5.3** evalúa **3**: naive, LR, XGBoost.
- **§6** admite que faltan «modelos de referencia adicionales».

**Contradicción cuantitativa directa.** Cinco prometidos, tres evaluados, dos no construidos, sin que §3 haya dicho nada.

**Consolidar en:** ver C-5 y C-6. Se resuelven a la vez.

---

# 2. Contradicciones graves (🟥)

## 🟥 G-1 · §2.1.3 presenta GDELT como «actualización cada 15 minutos», §4.1 elige la versión diaria

**Dónde se choca:**
- **§2.1.3**: «se actualiza cada 15 minutos» sin distinguir versiones.
- **§4.1**: elige **GDELT 1.0**, cadencia diaria. Descarta 2.0 explícitamente.
- **§4.2.1-A** en la revisión: los 15 minutos son de 2.0 y no aprovechables.

**Contradicción:** §2.1.3 presenta como ventaja lo que §4.1 descarta. El lector llega a §4.1 sin contexto para entender por qué la cadencia intradía «no se aprovecha».

**Consolidar en:** distinguir versiones en §2.1.3.

## 🟥 G-2 · «Snapshots diarios» vs «grafo persistente con decay»

**Dónde se choca:**
- **§3 Fase 3**: «Generación de **snapshots diarios** del grafo».
- **§4.2.1**: cierra en «un único **grafo persistente** cuyas aristas se refuerzan y decaen».
- **§2.2.4**: describe DTDG (snapshots), CTDG (continuo) y estáticos. La opción de §4.2.1 no encaja en ninguna.

**Contradicción:** tres descripciones distintas del mismo mecanismo temporal en tres capítulos.

**Consolidar en:** §2.2.4 añade la cuarta variante (grafo persistente con decay), §3 Fase 3 se reformula en esos términos, §4.2.1 queda como referencia canónica.

## 🟥 G-3 · Interpretabilidad por atención: §4.2.2 la promete, la ejecución no la extrae, §7 la mueve a futuro

**Dónde se choca:**
- **§2.2.3**: no discute interpretabilidad por atención en el marco de HeteroGAT.
- **§4.2.2**: «se puede responder a preguntas como qué países influyeron más en la predicción del 24 de febrero de 2022 con una respuesta numérica concreta y trazable».
- **Código**: no hay ningún `return_attention_weights` en `src/` ni en los notebooks.
- **§5**: no recoge ningún análisis de pesos de atención.
- **§7 (líneas futuras)** o el propio §4.2.2 tras corrección: se rebaja a análisis futuro.

**Contradicción:** §4.2.2 presenta la interpretabilidad como propiedad activa del modelo entregado. El código no la ejecuta. §5 no la reporta.

**Estado:** el checklist del capítulo 4 marca **4.2.2-C** como cerrado (párrafo rebajado a línea futura). **Verificar que en el docx la corrección está aplicada.** Si no, es 🔥.

## 🟥 G-4 · Chen et al. (2023): §2.3 lo critica por granularidad geográfica, §4.2.2 lo critica por late fusion

**Dónde se choca:**
- **§2.3**: «se ha utilizado de forma muy centrada en un país, priorizando las relaciones entre las empresas en vez de los vínculos de los países».
- **§4.2.2**: argumento distinto — «GNN-LSTM separado equivale a late fusion; grafo y target nunca interactúan dentro del mismo modelo».

**Contradicción:** dos argumentos distintos, ambos válidos, pero §4.2.2 usa el segundo para justificar la decisión arquitectural. §2.3 solo apunta el primero, con lo que el capítulo 4 aterriza sin apoyo teórico.

**Consolidar en:** añadir el argumento de late fusion a §2.3.

## 🟥 G-5 · Neutralidad / neutro / clases

**Dónde se choca:**
- **§3 Fase 2**: «neutralidad».
- **§4.3.1**: «neutro».
- **§4.3.5** y **§5**: «neutralidad».

**Contradicción:** vocabulario inconsistente para la clase central del problema.

**Consolidar en:** una decisión y pasada global.

## 🟥 G-6 · «QuadClass» aparece en §4 sin haber sido introducido en §2

**Dónde se choca:**
- **§2.1.3** describe CAMEO con tres niveles (EventRootCode, EventBaseCode, EventCode). **No menciona QuadClass**.
- **§4.2.4** decide granularidad en QuadClass (4 categorías) sin explicar qué es.

**Contradicción:** §4 asume un concepto que §2 no ha introducido.

**Consolidar en:** una línea en §2.1.3 introduciendo QuadClass como agrupamiento de alto nivel de CAMEO.

---

# 3. Contradicciones moderadas (🟧)

## 🟧 M-1 · Terciles como esquema de etiquetado

**Dónde se choca:**
- **§3 Fase 2**: menciona clasificación triclase pero no dice cómo se define el umbral.
- **§4.3.5-A**: «se determinará… contemplándose opciones».
- **§5**: usa terciles recalculados por fold.

**Consolidar en:** §3 Fase 2 y §4.3.5-A cierran la decisión.

## 🟧 M-2 · Walk-forward: ausente en §3, presente en §4, ejecutado en §5

**Dónde se choca:**
- **§3 Fase 5**: no menciona walk-forward.
- **§4.3.6-A**: lo anuncia como esquema, sin cifras (10 folds).
- **§5**: reporta 10 folds.

**Consolidar en:** §3 Fase 5 y §4.3.6-A.

## 🟧 M-3 · «Representación vectorial» en singular contra «representaciones vectoriales»

Ocho apariciones en el documento. Ya recogido en checklist del capítulo 4 (§5). Ver también capítulo 2 (§2.2.3).

## 🟧 M-4 · HGNN como concepto se introduce en §4.2.3 sin apoyo en §2.1.4

Ver 2.1.4-A.

## 🟧 M-5 · Plakandaras: autores mal citados

**Texto** en §2.2.1 y §2.3: «Plakandaras, Gogas & Papadimitriou».
**Bibliografía §8**: «Plakandaras, V., Gupta, R., & Wong, W. K.».

**Contradicción interna** en el propio §2. Ver 2.2.1-A.

---

# 4. Errores críticos individuales (no cruzados, pero recopilados aquí por gravedad)

Estos ya están en las revisiones individuales, pero se recopilan para tener la lista completa de lo que un tribunal detectaría:

- **§4.3.2-A**: OPEP+ como nodo (no lo es).
- **§4.3.2-D**: «producto interior bruto mundial» (real: comercio bilateral).
- **§4.3.2-F**: DXY «índice del dólar» que nunca se rellena en el vector del nodo mercado.
- **§4.2.4-A**: «militar / comercial / diplomático / legislativo» como categorías que QuadClass no tiene.
- **§4.3.4-C**: «dropout y normalización» — no hay ninguna capa de normalización.
- **§4.2.3-B**: `to_hetero()` presentado como técnica usada — el código usa `HeteroConv` explícito.
- **§2.3-A**: «cuatro cuestiones» y solo tres viñetas.
- **§4.1**: describe seis páginas de un pipeline (URL, embeddings, LDA) que no forma parte del pipeline de producción.

Cada uno se detecta cruzando el texto con el código de HEAD. Ver revisiones individuales.

---

# 5. Prioridades para reescritura

Ordenadas por daño reputacional en la defensa.

## Prioridad máxima — la reescritura de los 4 OEs

1. **C-1 → C-5 → C-6 → C-8** en un solo movimiento. Toca §3 (OEs), §4.3.6 (baselines), §5.3 (comparativa), §6 (limitación). El commit tiene que dejar los cuatro apartados diciendo lo mismo. Sin esto, la defensa se cae por los objetivos.

## Prioridad alta — los cuatro errores de hecho del capítulo 4

2. **C-2** buscar y reemplazar «HGT» → «GATv2» en §4.
3. **C-4** reescribir §4.3.2-E (nodo USA + macro reales).
4. **§4.3.2-F** DXY inactivo, `USAR_MACRO = False`.
5. **C-3** decisión sobre cierre-a-cierre + reformulación de §4.3.5 y OE3.

## Prioridad media — puentes entre §2 y §4

6. **G-2** grafo persistente en §2.2.4.
7. **G-6** QuadClass en §2.1.3.
8. **M-4** HGNN al final de §2.1.4.
9. **G-1** distinción GDELT 1.0/2.0 en §2.1.3.

## Prioridad media-baja — narrativa y coherencia argumental

10. **G-3** verificar que §4.2.2 tiene la interpretabilidad rebajada a línea futura en el docx (checklist marca hecho).
11. **G-4** añadir argumento de late fusion a §2.3.
12. **C-7** corregir crecimiento exponencial en §2.1.3 y §5.

## Prioridad baja — vocabulario, forma, referencias

13. **G-5** neutralidad / neutro.
14. **M-3** representación vectorial.
15. **M-5** Plakandaras.
16. Bibliografía §8: cuatro citas huérfanas de §2.2.3, prefijos, orden alfabético.

---

# 6. Nota final

Los 3 capítulos han sido escritos en momentos distintos del desarrollo. Al leerlos juntos:

- **§2** describe el estado del arte y el enfoque conceptual **antes** de que el trabajo estuviera hecho.
- **§3** describe los objetivos **como se plantearon** al inicio, con un diseño que se modificó durante la ejecución.
- **§4** describe el sistema **como debía ser**, con verbos en futuro y varias decisiones sin cerrar.
- El **código** implementa una **versión concreta** de todo eso, con decisiones tomadas.

La operación pendiente es alinear los cuatro artefactos en el mismo tiempo verbal y con los mismos valores. La revisión individual de cada capítulo describe el «qué». Este documento describe **qué contradicciones sobreviven al leer los tres juntos**.

Después de las **prioridades máxima y alta** (11 acciones), el documento pierde el 90 % del riesgo de defensa. Las prioridades media y baja son mejora de nota.
