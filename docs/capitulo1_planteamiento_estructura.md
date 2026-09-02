# §1.2 y §1.3 — Redacción propuesta y guía

Documento auxiliar para redactar los apartados **1.2 Planteamiento del trabajo** y **1.3 Estructura del trabajo** del capítulo 1 de la memoria. El apartado 1.1 (Motivación) ya está redactado y se toma como punto de partida.

## Cómo leer este documento

Cada apartado lleva primero una **guía** con qué debe contener y por qué, y a continuación una **propuesta de redacción** lista para copiar al Word.

Antes de aplicar cualquier texto, revisar las notas cruzadas al final para ver qué debe alinearse con el resto de la memoria.

---

# §1.1 — Nota sobre la Motivación ya redactada

## Estado actual

La motivación describe correctamente:

- El papel del mercado como asignador de capital y formador de precios.
- La evolución hacia modelos híbridos que incorporan información externa (con citas a Bao et al., 2025 y Patel et al., 2025).
- El compromiso entre riqueza informacional y estabilidad del entrenamiento.
- El foco en S&P 500 y en la señal geopolítica como factor diferencial.
- La elección de una GNN sobre GDELT como aproximación técnica.

## Ajuste pendiente

La frase final dice:

> «El objetivo final es la creación de un modelo que prediga la subida, bajada o neutralidad del S&P 500 **antes de la apertura de mercado para ese día**.»

Este planteamiento entra en conflicto con la definición operativa fijada en §4.1-C y §4.3.5-C, donde la etiqueta se calcula sobre el retorno **cierre-a-cierre entre t y t+1**, no sobre la apertura. Es el mismo problema recogido como **3.OE3-A** en el checklist del capítulo 3.

**Recomendado:** sustituir la frase por:

> «El objetivo final es la creación de un modelo que prediga la dirección del S&P 500 en la sesión siguiente —subida, bajada o neutralidad— a partir del estado del grafo geopolítico y financiero al cierre de la jornada previa.»

Así el capítulo 1 aterriza ya alineado con la definición temporal de §4.3.5.

---

# §1.2 Planteamiento del trabajo

## Qué debe contener

Es el puente entre la motivación (por qué) y los objetivos formales del capítulo 3 (para qué). Ha de responder de forma concreta a **cuatro preguntas**:

1. **Qué problema exacto se aborda.** Aterrizar la motivación en una tarea concreta: clasificación diaria de la dirección del S&P 500.
2. **Qué datos se usan.** GDELT 1.0 como fuente geopolítica, cotizaciones y macros financieras como señal de mercado.
3. **Qué enfoque técnico.** Grafo heterogéneo con memoria decaimiento-refuerzo procesado por una GNN de atención (HeteroGAT con GATv2).
4. **Qué queda fuera del alcance.** Delimitación honesta: es un piloto experimental de TFM, no un sistema de producción; no evalúa periodos anteriores a 2015 ni sectores individuales; no incluye baselines geopolíticos sin grafo ni LSTM financieras (se dejan a §7.2).

No repetir la motivación. No entrar en detalle técnico de arquitectura (eso es §4). Este apartado debe leerse cómodamente en dos minutos.

## Propuesta de redacción

> El presente trabajo se propone diseñar, implementar y evaluar un modelo de predicción de la dirección del índice S&P 500 en la sesión siguiente, formulado como un problema de clasificación con tres clases —subida, neutralidad y bajada— definidas por terciles de la distribución histórica de retornos diarios.
>
> La propuesta se apoya en dos fuentes de información complementarias. Por un lado, GDELT 1.0 (Global Database of Events, Language, and Tone), que registra a diario los eventos geopolíticos publicados en medios de comunicación de todo el mundo desde 1979, del que se extrae la actividad diaria entre veinte actores considerados relevantes para el mercado estadounidense. Por otro, la cotización histórica del S&P 500 y un conjunto reducido de indicadores financieros y macroeconómicos (retornos a distintos horizontes, volatilidad, VIX, índice del dólar y tasas de referencia) que caracterizan el estado del mercado.
>
> A partir de estas dos fuentes se construye, para cada sesión bursátil del periodo 2015-2025, un grafo heterogéneo compuesto por veinte nodos país, un nodo mercado y tres tipos de relación entre ellos. Las aristas se refuerzan con cada nuevo evento y decaen exponencialmente en su ausencia, dotando al grafo de una memoria continua que evoluciona con la actualidad geopolítica. Este grafo se procesa mediante una red neuronal de grafos heterogénea con atención (HeteroGAT sobre GATv2), cuya representación final del nodo mercado alimenta la cabeza de clasificación de tres clases.
>
> El trabajo se enmarca como un piloto experimental dentro de un Trabajo Fin de Máster, con un alcance deliberadamente acotado en tres dimensiones. En cuanto a datos, el periodo de estudio se restringe a 2015-2025, tramo con una cobertura mediática de GDELT 1.0 relativamente homogénea. En cuanto a target, se predice el índice agregado y no sus once sectores GICS, cuya extensión queda identificada como línea natural de continuación. En cuanto a modelos de referencia, se comparan los resultados con un baseline trivial, una regresión logística y un XGBoost sobre las mismas features aplanadas; la comparación frente a modelos que incorporasen datos geopolíticos sin la estructura del grafo se reserva como línea futura (§7.2), por las razones que se detallan en el capítulo 6.
>
> La evaluación se realiza mediante un esquema de validación temporal walk-forward de diez folds expansivos con embargo cero, promediando resultados sobre tres semillas de inicialización, y se complementa con una evaluación financiera que traduce las predicciones del modelo a una estrategia de inversión simulada. Las métricas de referencia son la exactitud, la F1 macro y el ratio de Sharpe.

---

# §1.3 Estructura del trabajo

## Qué debe contener

Un mapa de lectura del documento: **una frase por capítulo** en el orden en el que aparecen. Debe permitir al lector decidir en qué capítulo entrar según lo que busque.

Recomendaciones de forma:

- Numeración explícita de los capítulos (**Capítulo 2**, no «el segundo apartado»).
- Ninguna frase debe superar dos líneas.
- Referencia final al anexo si existe.
- Cerrar el capítulo 1 con esta sección; nada después.

## Propuesta de redacción

> El presente documento se estructura en ocho capítulos y un anexo.
>
> El **Capítulo 1**, del que forma parte este apartado, introduce la motivación del trabajo, delimita el planteamiento y ofrece este mapa de lectura.
>
> El **Capítulo 2** revisa el contexto y el estado del arte: los fundamentos de la predicción de mercados financieros, el concepto de riesgo geopolítico y sus canales de transmisión, las bases de datos de eventos disponibles, los principios de las redes neuronales de grafos, y los trabajos previos que han combinado alguna de estas piezas para tareas de predicción bursátil.
>
> El **Capítulo 3** formaliza los objetivos general y específicos, y describe la metodología en fases con la que se ha ejecutado el trabajo.
>
> El **Capítulo 4** entra en la descripción detallada del experimento: cómo se filtran los datos de GDELT, qué decisiones técnicas sostienen el modelado (modelado temporal, integración del S&P 500 como nodo, familia arquitectural, diseño topológico y régimen de datos), y qué configuración final adopta el sistema, tanto en la estructura del grafo como en el modelo y en la cabeza de predicción.
>
> El **Capítulo 5** recoge los resultados del experimento: distribución del dataset, métricas de clasificación, comparación con los modelos de referencia, evaluación financiera y análisis complementarios de las predicciones.
>
> El **Capítulo 6** discute los resultados en relación con las decisiones tomadas y con las limitaciones del piloto.
>
> El **Capítulo 7** cierra el trabajo con las conclusiones y las líneas de trabajo futuro.
>
> El **Capítulo 8** recoge las referencias bibliográficas.
>
> Finalmente, el **Anexo A** contiene los materiales complementarios que soportan la reproducibilidad del experimento.

---

# Notas cruzadas con otros apartados

Al aplicar §1.2 y §1.3, revisar de paso:

- **§1.1 «antes de la apertura de mercado»** → sustituir por la frase alineada con §4.3.5 (ver bloque anterior).
- **Objetivo general (§3.1)**: la frase que resume el objetivo debe coincidir con la primera línea del §1.2.
- **Objetivos específicos (§3.2)**: OE1-OE6 recién redactados en el checklist del capítulo 3. §1.2 no debe listar OEs; solo anticipar el enfoque.
- **§4.3.5**: la definición operativa de las tres clases (terciles, cierre-a-cierre) debe coincidir con la descripción de §1.2.
- **§4.3.6**: el esquema walk-forward (10 folds expansivos, embargo cero, 3 semillas) debe coincidir con el resumen que hace §1.2.
- **§6**: las limitaciones que se anuncian en §1.2 («baselines geopolíticos sin grafo se reservan a §7.2») deben coincidir con el reconocimiento explícito de §6.
- **§7.2**: al llegar al capítulo 7, la lista de líneas futuras debe incluir todo lo que en §1.2 se ha reservado (baselines faltantes, sectores GICS, barrido de λ, aristas dinámicas, extracción de coeficientes de atención).

---

# Estimación de tiempo

- §1.2 nueva redacción: 15 min copiar + 10 min releer y ajustar tono.
- §1.3 nueva redacción: 5 min copiar.
- Ajuste de la frase final de §1.1: 2 min.
- Verificación de las notas cruzadas: 10 min.

**Total: ~30-45 min.**
