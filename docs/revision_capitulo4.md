# Revisión del capítulo 4 de la memoria

**Fecha:** 2026-09-02
**Documento revisado:** `EntregaFINAL_TFM_Aguiló_Martín.docx (1).pdf`
**Contrastado contra:** el código de este repositorio en HEAD (`config.py`, `src/datos/`, `src/modelo/`)
**Alcance:** capítulo 4 completo (4.1, 4.2.1–4.2.5, 4.3.1–4.3.6) más las incoherencias que arrastra con los capítulos 5 y 6.

## Cómo leer este documento

Cada hallazgo lleva un identificador, una severidad, **DÓNDE** está (apartado + frase literal) y **QUÉ** hay que poner.

| Severidad | Significado |
|---|---|
| 🔴 **ERROR** | La memoria afirma algo que el código no hace. Hay que corregirlo sí o sí. |
| 🟠 **DESAJUSTE** | Está en futuro o sin decidir, en un capítulo que describe un experimento ya ejecutado. |
| 🟡 **MEJORA** | Hueco argumental, justificación ausente o débil. |
| ⚪ **FORMA** | Errata, formato, estilo. |

**Recuento:** 12 errores · 19 desajustes · 11 mejoras · 14 formas = **56 puntos**.

## Ya corregido desde la versión anterior

Para no volver sobre ello: la viñeta de GDELT 1.0 vs 2.0 en §4.1, el «tres aspectos» que ahora dice «dos», `Fama(1907)` → `Fama(1970)`, el párrafo introductorio de §2.1, «aproximadamente veinte nodos» → «veinte nodos» en §4.2.4, la retirada de la OPEP+ de §4.2.4, y el párrafo nuevo de granularidad QuadClass con su tabla.

---

# 1. Lo que hay que decidir antes de tocar nada

Tres preguntas cuya respuesta cambia qué se escribe. Sin ellas, buena parte de lo que sigue queda en el aire.

**P1. ¿Se hizo el barrido de la velocidad de decaimiento (λ)?**
§4.3.3 promete que «se tratará como un hiperparámetro a explorar» y que «esta exploración constituye en sí misma un resultado de interés». El capítulo 5 no la recoge. `config.py` dice `AJUSTAR: barrido experimental` junto a `LAMBDA_DECAY`. Si no se hizo, esa promesa hay que retirarla o pasarla a trabajo futuro.

**P2. ¿Se va a implementar algún baseline más?**
§4.3.6 promete una LSTM financiera y, sobre todo, «un baseline que combine los datos financieros con una señal geopolítica agregada pero sin estructura de grafo». Ninguno de los dos existe: `src/modelo/baselines.py` solo implementa `BaselineNaive`, `entrenar_logistica` y `entrenar_xgboost`, y §5.3 confirma que solo se evaluaron esos tres. El capítulo 6 ya admite la carencia. **Ver el hallazgo X-1: hay contradicción directa entre 4.3.6 y 6.**

**P3. ¿Las cifras del capítulo 5 salen de una ejecución posterior a la que yo audité?**
La memoria da exactitud 0,4124 y F1-macro 0,3523, con columnas de la matriz de confusión 2011 / 3115 / 2374. Los resultados almacenados del `02_entrenamiento_local.ipynb` que revisé daban 0,4084 y 0,3447, con columnas 1832 / 3183 / 2485. Los totales por fila coinciden (2445 / 2274 / 2781), así que las etiquetas son las mismas y lo que cambia son las predicciones: hubo un reentrenamiento. **Confirma de qué ejecución salen las cifras del capítulo 5 y guarda ese `resultados.json`**, porque es la que hay que citar en el anexo.

---

# 2. Apartado 4.1 — Filtrado de datos

Este apartado tiene el problema más grave de todo el capítulo, y no es de redacción.

## 🔴 4.1-A · El apartado describe un pipeline que no es el que construyó el grafo

**DÓNDE:** desde «Es necesario realizar una limpieza inicial…» hasta «Se asigna a cada noticia el tema de su documento representativo». Son unas seis páginas: normalización de URL, texto sintético, representaciones vectoriales con `all-MiniLM-L6-v2`, agrupamiento k-NN por similitud coseno y LDA.

**QUÉ PASA:** nada de eso está en el código de producción. El pipeline real es [`preprocesar_dia`](../src/datos/preprocesar.py#L117) y tiene exactamente cinco pasos:

1. `cargar_csv_gdelt` — lee **13 de las 58 columnas** vía `usecols`
2. `filtrar_roster` — conserva la fila si Actor1 **o** Actor2 está en el roster de 20 países
3. `filtrar_cobertura` — `NumMentions >= 5`
4. `dropna` sobre `GoldsteinScale`, `AvgTone`, `QuadClass`
5. `aplicar_corte_horario` — que además es inerte (ver 4.1-B)

No hay normalización de URL, ni embeddings, ni clustering, ni LDA. De hecho la URL ni siquiera se carga: no está entre las 13 columnas de `COLUMNAS_RELEVANTES`.

**QUÉ HACER:** no hay que borrar esas páginas — el trabajo se hizo y tiene valor. Hay que **reencuadrarlas como exploración descartada**. Dos cambios:

- Una frase al principio del bloque que anuncie que lo que sigue es una fase exploratoria sobre muestras de uno y tres días, cuyo resultado fue descartar esas técnicas.
- Una **tabla de dos columnas** al final del apartado: técnica evaluada / incorporada al pipeline final, con el motivo en una línea. Cinco filas: normalización de URL (no), texto sintético (no), representaciones vectoriales + agrupamiento (no), LDA (no), umbral `NumMentions ≥ 5` (**sí**).

Esa tabla convierte seis páginas de material huérfano en una decisión metodológica documentada, y cuesta media hora.

## 🔴 4.1-B · El pipeline real no aparece en ninguna parte

**DÓNDE:** no existe. Es una ausencia.

**QUÉ PASA:** el lector termina §4.1 sin saber cuántos eventos entran al grafo. Todos los números del apartado (118.201 → 107.248 → 22.572 → 19.423) pertenecen a la vía exploratoria descartada.

**QUÉ PONER:** una tabla con el embudo real. Cifras medidas sobre 6 días muestreados con el código de producción:

| Etapa | Filas | % del bruto |
|---|---:|---:|
| Eventos brutos | 1.029.338 | 100 % |
| Tras filtro de roster (20 países, OR) | 550.331 | 53,5 % |
| Tras `NumMentions ≥ 5` | 238.688 | 23,2 % |
| Tras `dropna` (Goldstein / Tone / QuadClass) | 238.688 | 23,2 % |

El reparto se mantiene entre 53–55 % y 22–24 % a lo largo de 2015–2025. Que el `dropna` no descarte nada también es información: dice que GDELT 1.0 rellena siempre esos tres campos.

## 🔴 4.1-C · El corte horario anti-leakage es inerte

**DÓNDE:** §4.1 no lo menciona; §4.3.5 lo describe («la construcción del grafo correspondiente a un día t debe limitarse a los eventos disponibles hasta el cierre del mercado de esa jornada»).

**QUÉ PASA:** en los CSV de GDELT 1.0 el campo `DATEADDED` es la columna 57 y contiene **ocho dígitos**: `20180509`. No hay hora. `aplicar_corte_horario` intenta parsear `%Y%m%d%H%M%S`, falla siempre y cae al fallback de fecha, devolviendo la misma fecha de publicación. El corte de las 16:00 America/New_York **no filtra ni una sola fila del dataset**.

Verificado comparando `data/agregados/` con `data/agregados_nb04_dst_v2_.../`: son idénticos día a día tanto en horario de verano como de invierno (712 aristas y 17.361 eventos el 2018-05-09 en ambos). Si el corte hiciera algo, no podrían coincidir.

**QUÉ HACER:** hay que decirlo, y conviene decirlo bien porque tiene una lectura favorable. La cadencia diaria de 1.0 significa que el fichero del día *t* se publica la mañana de *t+1*; la etiqueta es el retorno cierre-a-cierre de *t+1*. El corte horario es innecesario **porque la propia granularidad de la fuente ya garantiza la separación temporal**. Declarado así, deja de ser un agujero y pasa a ser una consecuencia coherente de la elección de fuente hecha en la primera viñeta del apartado.

Lo que no se puede dejar es §4.3.5 describiendo un mecanismo que el código no puede ejecutar.

## 🟡 4.1-D · El argumento de los «más de 20 años» no sostiene la decisión

**DÓNDE:** segunda viñeta: «GKG y 2.0 tienen noticias desde el 2013 y 2015, mientras que su versión 1.0 tiene más de 20 años de noticias.»

**QUÉ PASA:** el capítulo 5 usa **2015–2025**. GDELT 2.0 arranca en febrero de 2015, o sea que cubre prácticamente todo el periodo de estudio. La ventaja de profundidad histórica que se invoca aquí nunca se aprovecha, y es la clase de detalle que un tribunal cruza sin esfuerzo: «eligieron 1.0 por sus veinte años y luego usaron solo desde 2015».

**QUÉ HACER:** o se retira la viñeta y se deja la primera como único argumento —que ya es sólida y está bien escrita—, o se reformula como capacidad de extensión futura del trabajo, dejando claro que en este estudio no se ha usado.

## 🟡 4.1-E · Solo se nombran 5 columnas de las 13 que se cargan

**DÓNDE:** «se identifican las siguientes columnas numéricas» + la lista de cinco (GoldsteinScale, NumMentions, NumSources, NumArticles, AvgTone).

**QUÉ PASA:** `COLUMNAS_RELEVANTES` en [`descarga_gdelt.py`](../src/datos/descarga_gdelt.py) carga **trece**: GLOBALEVENTID, SQLDATE, DATEADDED, Actor1CountryCode, Actor2CountryCode, EventCode, EventRootCode, QuadClass, GoldsteinScale, AvgTone, NumMentions, NumSources, NumArticles.

**QUÉ PONER:** una tabla de tres columnas —columna / tipo / para qué se usa (nodo, arista, filtro, característica)— con las trece. Justifica de paso por qué se descartan las otras 45 y sustituye a la lista actual, que se queda corta.

## 🟡 4.1-F · «Un único día de datos como muestra»

**DÓNDE:** «Para el desarrollo del proceso de tratamiento de datos, se opta por trabajar con un único día de datos como muestra»

**QUÉ PASA:** más adelante se amplía a tres días, pero la frase queda como una debilidad metodológica enunciada sin justificación ni matiz. Y falta el punto final.

**QUÉ HACER:** justificarlo (es una exploración, no una medición) y adelantar que la estabilidad se comprueba después sobre tres días. Con la tabla de 4.1-A delante, deja de chirriar.

## 🟡 4.1-G · El filtro de relevancia geopolítica está descrito sin precisión

**DÓNDE:** «Relevancia geopolítica: Conservar solo eventos en los que haya al menos un actor de gran importancia.»

**QUÉ PASA:** es correcto pero vago. En el código es un **OR explícito** sobre `Actor1CountryCode` y `Actor2CountryCode` contra el roster de 20 países: `df["pais_origen"].notna() | df["pais_destino"].notna()`. El docstring del módulo lo justifica con un ejemplo bueno (CHN→SYR se conserva porque China es relevante aunque Siria no esté en el roster).

**QUÉ PONER:** el criterio exacto y ese ejemplo. Es una decisión de diseño no trivial —un AND daría un grafo mucho más pequeño y sesgado— y ahora no se defiende.

## ⚪ 4.1-H · Erratas y formato

| Dónde | Qué | Poner |
|---|---|---|
| Lista de columnas | «Puntuacioón» | Puntuación |
| Lista de columnas | «notícia» (acento catalán) | noticia |
| Ficheros mensuales | «cuando llega al 2005 **són** anuales» | son |
| Ficheros mensuales | falta el sujeto | GDELT empaqueta… |
| Texto sintético | «Latent **Drichlet** Allocation» | Dirichlet |
| Estabilidad entre días | «el porcentaje de singletons del **grupoing**» | del agrupamiento |
| LDA | «complementar el **gruposy** descubrir temas» | los grupos y descubrir |
| Umbral | «para ver **cual** es el umbral» | cuál |
| Volumen de ficheros | «100000 a 300000» | 100.000 a 300.000 |
| Todo el apartado | conviven «118 201» (espacio), «288.925» (punto) y «100000» (nada) | Punto de millar en todo el documento |
| Figura de reducción | la barra dice «Post filtrado dirigido (**§4.7**)» | Ese apartado no existe en la memoria. Regenerar la figura o recortar la etiqueta |
| Tabla LDA | cabecera «Document» y valores «3,306» con coma | «Documentos» y 3.306 con punto de millar |

---

# 3. Apartado 4.2 — Decisiones técnicas

## 4.2.1 Modelado temporal del grafo

### 🔴 4.2.1-A · El rechazo de CTDG se apoya en una granularidad que el dataset no tiene

**DÓNDE:** «Aunque conceptualmente fiel a la naturaleza de GDELT, que se actualiza cada 15 minutos, esta granularidad resulta excesiva para una tarea cuya predicción es diaria.»

**QUÉ PASA:** dos problemas encadenados. Los 15 minutos son de **GDELT 2.0**, que se descartó en §4.1. Y en GDELT 1.0, como se explica en 4.1-C, no hay ningún timestamp intradía. CTDG no es excesivo: es **imposible** con esta fuente.

**QUÉ PONER:** el argumento honesto, que además es más fuerte. Pasa de «pudimos pero no quisimos» a «la fuente no lo permite», que nadie puede discutir, y de paso desaparece la incoherencia con §4.1.

### 🔴 4.2.1-B · El decay diferenciado por QuadClass no aparece

**DÓNDE:** ausencia. Todo el apartado habla de un decaimiento exponencial único.

**QUÉ PASA:** el código no aplica una λ única. Aplica un multiplicador por categoría CAMEO ([`config.py:150`](../config.py#L150)):

| QuadClass | Multiplicador | Vida media |
|---|---:|---:|
| 1 Cooperación verbal | 1,5 | 6,7 días |
| 2 Cooperación material | 1,0 | 10 días |
| 3 Conflicto verbal | 0,7 | 14,3 días |
| 4 Conflicto material | 0,4 | 25 días |

El conflicto material se recuerda **3,7 veces más** que la cooperación verbal. Y el comentario del propio `config.py` lo justifica con exactamente el argumento que hace este apartado: «una guerra no desaparece en 10 días; una declaración diplomática sí», conectado con las tres fases de Caldara e Iacoviello.

**QUÉ HACER:** subir esa tabla a §4.2.1. Es la decisión de diseño más original de la sección y ahora mismo está enterrada en un comentario de código. Ahora el apartado hace el razonamiento teórico y **no dice que esté implementado**.

### 🔴 4.2.1-C · Hawkes sin ninguna cita

**DÓNDE:** «los procesos de Hawkes son un modelo estocástico ampliamente utilizado en finanzas para modelar contagio entre mercados y otras dinámicas de auto-excitación».

**QUÉ PASA:** no hay ni un Hawkes en la bibliografía del trabajo. Es la justificación teórica del mecanismo central del grafo y va sin respaldo, en un capítulo donde todo lo demás sí lo lleva.

**QUÉ PONER:** Hawkes (1971) para el original y Bacry, Mastromatteo & Muzy (2015) para la revisión canónica en finanzas. Y añadirlos a §8.

### 🟡 4.2.1-D · Sobreafirmación sobre la validación del método

**DÓNDE:** «no se trata de una fórmula ad hoc, sino de una formulación que tiene precedente y validación en el campo».

**QUÉ PASA:** lo validado son los procesos de Hawkes. Lo implementado es decaimiento exponencial con refuerzo: no hay intensidad condicional, no hay auto-excitación entre pares, y λ no se estima — está fijada a mano en 0,0693. En el párrafo anterior se escribe «inspirada en los procesos de Hawkes», que es exacto; esta frase se lo carga.

La pregunta previsible en la defensa es «¿estimaron λ por máxima verosimilitud?», y la respuesta es no.

**QUÉ HACER:** mantener «inspirada» y bajar el remate a precedente conceptual, sin reclamar validación de la formulación concreta.

### 🟡 4.2.1-E · «Un único grafo persistente» frente a la ventana de 60 días

**DÓNDE:** «mantener un único grafo persistente», y en §4.3.3 «a partir del histórico de eventos acumulado hasta esa fecha».

**QUÉ PASA:** no es el histórico acumulado. `VENTANA_DECAY_DIAS = 60` corta en seco a los 60 días. Para la λ base es casi inocuo —a 60 días queda el 1,6 % del peso—, pero **para conflicto material no**: con vida media de 25 días, a los 60 días todavía queda el **19 %**, y ahí el truncamiento sí borra señal. El propio comentario de `config.py` dice «su contribución ya es despreciable», y para la clase más persistente no lo es.

**QUÉ HACER:** declarar la ventana y su efecto. Subir `VENTANA_DECAY_DIAS` cuesta un reentrenamiento; declararlo cuesta una frase. Si vas justo, decláralo como limitación.

### 🟡 4.2.1-F · Faltan todas las cifras

**DÓNDE:** todo el apartado.

**QUÉ PASA:** se justifica un mecanismo de decaimiento sin dar ni λ (0,0693), ni la vida media (10 días), ni la ventana (60 días). §4.3.3 los aplaza otra vez a «se ajustarán durante la experimentación».

### ⚪ 4.2.1-G · «Adicionalmente» abriendo párrafo

Calco del inglés *additionally*. En castellano, «Además».

## 4.2.2 Integración del SP500

### 🔴 4.2.2-A · Se atribuye la interpretabilidad al HGT, que no se usó

**DÓNDE:** «el mecanismo de atención **del HGT** permite, para cada predicción, obtener los coeficientes de atención que el modelo ha asignado a cada arista país-SP500».

**QUÉ PONER:** GATv2. El modelo usa `GATv2Conv` envuelto en `HeteroConv` ([`arquitectura.py:92`](../src/modelo/arquitectura.py#L92)). Es la primera de **cuatro** apariciones del HGT como si fuera el modelo empleado.

### 🔴 4.2.2-B · El grafo tiene tres relaciones, no dos

**DÓNDE:** todo el párrafo de «las dos modalidades interactúan en cada iteración del procesamiento», y también §4.2.3 y §4.3.2 cuando dicen «dos tipos de aristas (país-país y país-mercado)».

**QUÉ PASA:** el modelo declara **tres** tipos de relación:

- `('country', 'interactua', 'country')`
- `('country', 'expone', 'market')`
- `('market', 'influye', 'country')`

La tercera es precisamente la que hace verdad el argumento central de este apartado. Sin ella, el nodo mercado solo recibiría mensajes y nunca devolvería, y la frase «los nodos país reciben información del estado del mercado a través de las aristas que les conectan con el SP500» sería falsa. **El mejor argumento de §4.2.2 se apoya en una relación que la memoria nunca declara.**

## 4.2.3 Arquitectura del modelo

### 🟠 4.2.3-A · La decisión sigue abierta

**DÓNDE:** «La decisión final entre HGT y HeteroGAT **no se ha cerrado** a nivel arquitectural y **se determinará empíricamente** durante la fase de implementación» y «Esta decisión menor **se reserva** como ajuste empírico una vez implementado el flujo de trabajo básico».

**QUÉ PONER:** se cerró en **HeteroGAT**, y además con **GATv2** (Brody, Alon & Yahav, 2022), no con el GAT original. Sustituir el párrafo por el motivo real de la elección.

Si se cita GATv2 hay que añadir Brody et al. a la bibliografía, donde ahora solo está Veličković et al. (2018).

### 🔴 4.2.3-B · `to_hetero()` no se usó

**DÓNDE:** «HeteroGAT puede obtenerse de forma sencilla aplicando la función `to_hetero()` de PyTorch Geometric a un GAT estándar».

**QUÉ PASA:** el código no usa `to_hetero()`. Usa `HeteroConv` con un `GATv2Conv` **explícito por cada tipo de relación**. Son dos APIs distintas que producen grafos de cómputo distintos, y la diferencia importa para el argumento de parámetros de §4.2.4.

## 4.2.4 Diseño topológico

### 🔴 4.2.4-A · La justificación del tipado contradice la granularidad elegida

**DÓNDE:** «El tipado permite al modelo distinguir eventos **militares, comerciales, diplomáticos o legislativos**», dos párrafos antes de anunciar que se usa QuadClass.

**QUÉ PASA:** QuadClass tiene cuatro categorías —cooperación verbal, cooperación material, conflicto verbal, conflicto material— y **no distingue militar de comercial ni de diplomático ni de legislativo**. Esa distinción requeriría EventRootCode, que es justo lo que se descarta.

Es un problema real de coherencia interna, y además reaparece en §4.2.4 más abajo («Si una arista USA-Rusia está etiquetada como "militar"… a diferencia de una arista USA-China etiquetada como "comercial"») y otra vez en §4.3.2 («militar frente a diplomática»). Con QuadClass, ninguno de esos ejemplos es posible.

**QUÉ HACER:** reescribir los ejemplos en términos del eje que sí captura QuadClass: cooperación frente a conflicto, y verbal frente a material. Un ataque y una declaración hostil quedan separados; una sanción comercial y un despliegue militar no. Y decirlo: es una limitación real del tipado elegido, y reconocerla vale más que un ejemplo que no se sostiene.

### 🔴 4.2.4-B · Tercera aparición del HGT

**DÓNDE:** «el mecanismo de atención **del HGT** puede aprender a tratarla de forma distinta a una arista USA-China».

**QUÉ PONER:** GATv2.

### 🟡 4.2.4-C · Los pesos de comercio bilateral son estimaciones propias

**DÓNDE:** «pesos iniciales informados por el comercio bilateral con Estados Unidos».

**QUÉ PASA:** `PESOS_COMERCIO_BILATERAL` en [`src/utils/paises.py`](../src/utils/paises.py) son valores fijados a mano, con un comentario en el propio código que dice `AJUSTAR … UN Comtrade`. No proceden de ninguna fuente citada.

**QUÉ HACER:** o se cita la fuente, o se declara que son estimaciones de orden de magnitud usadas como *prior* no entrenable. Lo segundo es defendible; lo que no se puede es dejar que el lector suponga que hay una fuente detrás.

### ⚪ 4.2.4-D · La tabla de QuadClass está mal maquetada

**DÓNDE:** la tabla nueva.

**QUÉ PASA:** en el PDF la cabecera parte «% eventos» en tres líneas y el total de aristas sale roto como «2.198.6 / 57».

**QUÉ HACER:** ensanchar las columnas, alinear a la derecha las cuatro numéricas, y añadir debajo las dos líneas que faltan:

*Nota. Los porcentajes de eventos no suman exactamente 100 por efecto del redondeo.*
Fuente: Elaboración propia.

Y el pie: Tabla X. *Distribución de eventos y aristas por QuadClass en el periodo 2015-2025.*

## 4.2.5 Régimen de datos y dimensionamiento

Este apartado entero está en futuro y todos los valores son conocidos.

| # | Frase actual | Qué poner |
|---|---|---|
| 🟠 A | «el número de muestras de entrenamiento efectivo se sitúa **en torno a las dos mil**» | El dataset son **2.751 grafos**; con 10 folds expansivos el train del último ronda las 2.500. El capítulo 5 ya dice 2.751 |
| 🟠 B | «limita el tamaño práctico de la arquitectura a **la decena o cientos de miles** de parámetros» | Decir el número real. **Cuéntalo antes** con `sum(p.numel() for p in modelo.parameters() if p.requires_grad)`; mi estimación analítica da ~57.000 pero no pude ejecutarla |
| 🟠 C | «el modelo **se mantendrá** deliberadamente pequeño, con dimensión moderada (**entre 32 y 128**)» | **64** (`ConfigModelo.dim_oculta`) |
| 🟠 D | «un número limitado de capas de message passing (**dos o tres**)» | **2** |
| 🟠 E | «**se aplicará** regularización fuerte: dropout **entre el 30 % y el 50 %**, weight decay, y parada temprana basada en la métrica de validación» | dropout **0,3**; weight decay **1e-4**; parada temprana con **paciencia de 15 épocas** sobre una **validación interna** (el 15 % final del train de cada fold), nunca sobre el test. Ese matiz es anti-leakage y merece decirse explícitamente |
| 🟠 F | «la evaluación **se realizará** con múltiples semillas (**entre tres y cinco**)» | **3 semillas: (0, 1, 2)**. El capítulo 5 ya dice tres, así que ahora 4.2.5 se contradice con el 5 |

### 🟡 4.2.5-G · Falta el argumento que hace falta en 4.2.4

El apartado explica el régimen de datos limitado pero no lo conecta con la decisión de QuadClass. La implementación asigna **una operación de atención independiente con su propia matriz de pesos a cada tipo de arista**, de modo que pasar de 4 a 20 categorías quintuplicaría los parámetros de la rama país-país. Es el mismo razonamiento de este apartado aplicado allí, y encadenar los dos hace que el capítulo se sostenga mejor.

---

# 4. Apartado 4.3 — Arquitectura final

## 4.3.1 Visión general

### ⚪ 4.3.1-A · Coma entre sujeto y verbo

**DÓNDE:** «El sistema con el grafo del día t, produce directamente la predicción para el día t+1».

La coma separa el sujeto del verbo. Además la construcción es confusa: se entiende «a partir del grafo del día t».

## 4.3.2 Estructura del grafo heterogéneo

Es el apartado con más errores de hecho del capítulo.

### 🔴 4.3.2-A · La OPEP+ sigue aquí

**DÓNDE:** «entidades supranacionales (la Unión Europea y, **condicionalmente, la OPEP+**)».

**QUÉ PASA:** se quitó de §4.2.4 pero se quedó en §4.3.2. No está en el roster. Los 20 nodos son: USA, CHN, RUS, EUR, DEU, FRA, GBR, JPN, KOR, IND, TWN, CAN, MEX, BRA, SAU, IRN, ISR, TUR, PRK, AUS. La UE sí (códigos `EUR` y `EEC`).

### 🟠 4.3.2-B · El conjunto de nodos «no se cierra»

**DÓNDE:** «agrupa **aproximadamente** una veintena de actores» y «El número y la composición exacta de este conjunto **dependen del análisis exploratorio inicial y no se cierran a nivel arquitectónico**».

**QUÉ PONER:** veinte, cerrados, con la lista.

### 🟠 4.3.2-C · Cuarta vez que la granularidad «se determinará»

**DÓNDE:** «El nivel de granularidad de este tipado (las cuatro categorías de QuadClass o las veinte de EventRootCode) **se determinará empíricamente**».

**QUÉ PONER:** QuadClass, con remisión a §4.2.4 donde ahora sí está resuelto y con tabla.

### 🔴 4.3.2-D · No es el PIB, es el comercio bilateral

**DÓNDE:** «junto con posibles atributos económicos básicos como el peso del país en el **producto interior bruto mundial**».

**QUÉ PONER:** es el **peso de comercio bilateral con EE. UU.** Las once features reales del nodo país son: tono medio, Goldstein medio, log nº eventos, log NumMentions, peso comercio, log grado de entrada, log grado de salida, y las cuatro fracciones por QuadClass. Ya no hay que decir «previsiblemente incluirán»: están fijadas en [`grafo.py:51`](../src/datos/grafo.py#L51).

### 🔴 4.3.2-E · El nodo Estados Unidos no es un caso especial

**DÓNDE:** «El nodo correspondiente a Estados Unidos constituye **un caso especial**: por ser el país sobre cuyo mercado se predice, **se contempla enriquecerlo** con características macroeconómicas adicionales que el resto de países no tendrían, como la tasa de la Reserva Federal, los rendimientos de los bonos del Tesoro, la inflación o indicadores de actividad.»

**QUÉ PASA:** **no se hizo**. Todos los países llevan exactamente las mismas once features. Las macro (fed funds, Tesoro a 10 años) acabaron en el **nodo mercado**, posiciones 7 y 8 del vector — y en el experimento del capítulo 5 están a cero, porque el notebook se ejecutó con `USAR_MACRO = False` tras empeorar los resultados.

Este párrafo describe un modelo que no existe. Es el error más comprometido del capítulo porque un tribunal que abra el repositorio buscando esas features no las va a encontrar.

### 🔴 4.3.2-F · El índice del dólar nunca se rellena

**DÓNDE:** «El nodo de tipo mercado lleva características de naturaleza financiera: retornos a distintos horizontes temporales, medidas de volatilidad, volumen e indicadores de mercado como el VIX o **el índice del dólar**.»

**QUÉ PASA:** el vector tiene **nueve** componentes exactas: retorno 1d, retorno 5d, retorno 21d, volatilidad 21d, log volumen, VIX, log DXY, fed funds, Tesoro 10 años. Pero `TICKER_DXY` está definido en `descarga_financiero.py` y **no se llama desde ningún sitio**, así que la posición 6 es cero siempre. Con `USAR_MACRO = False` encima, las posiciones 7 y 8 también. **Solo 6 de las 9 llevan datos en el experimento presentado.**

**QUÉ HACER:** describir las nueve y declarar cuáles quedaron inactivas y por qué. Es más honesto y evita que alguien busque el DXY en los resultados.

### 🟠 4.3.2-G · La exposición «será» el comercio bilateral

**DÓNDE:** «Las aristas país-mercado incorporan una medida de exposición, cuya base **será** el comercio bilateral con Estados Unidos, **posiblemente complementada** con otras señales de relevancia económica.»

**QUÉ PONER:** una sola feature (`DIM_FEATURES_EDGE_CM = 1`), el peso de comercio bilateral, sin complementar.

### 🟡 4.3.2-H · Las features de arista país-país no se detallan

**DÓNDE:** «Las aristas país-país incorporan los atributos agregados de los eventos correspondientes (intensidad, tono y volumen de menciones)».

**QUÉ PONER:** son **siete**: peso con decay, tono ponderado, log nº eventos, y el *one-hot* de QuadClass (4 posiciones). Ese one-hot es justamente el tipado del que habla §4.2.4 y aquí no se ve.

### ⚪ 4.3.2-I · «En cuanto a artistas»

Errata por «aristas».

## 4.3.3 Evolución temporal

| # | Sev. | Frase actual | Qué poner |
|---|---|---|---|
| A | 🟠 | «Tanto la forma de medir la intensidad como la velocidad a la que decae **son aspectos que se ajustarán durante la experimentación**» | λ = **0,0693** (vida media 10 días), multiplicadores por QuadClass (1,5 / 1,0 / 0,7 / 0,4) y ventana de **60 días** |
| B | 🟠 | «La velocidad de decaimiento **se tratará como un hiperparámetro a explorar**… **Esta exploración constituye en sí misma un resultado de interés**» | Depende de **P1**. Si no se hizo el barrido, retirar o pasar a §7.2 |
| C | 🔴 | «el grafo se reconstruye para cada día a partir del **histórico de eventos acumulado hasta esa fecha**» | Ventana de **60 días**. Ver 4.2.1-E |

## 4.3.4 Modelo

| # | Sev. | Frase actual | Qué poner |
|---|---|---|---|
| A | 🟠 | «concretamente **HGT… o HeteroGAT**… **la elección final entre ambas se reserva como ajuste empírico**» | Cuarta aparición del HGT sin cerrar. GATv2 vía HeteroConv |
| B | 🟠 | «**se contempla** una dimensión moderada, un número reducido de capas (**previsiblemente dos o tres**), y **un número de cabezas de atención a determinar**… regularización **cuya intensidad se ajustará**» | 64 / 2 capas / **4 cabezas** / dropout 0,3 |
| C | 🔴 | «regularización (dropout y **normalización**)» | **No hay ninguna capa de normalización** en el modelo. Hay dropout y hay conexiones residuales, que no es lo mismo. Corregir o quitar |
| D | 🟡 | (ausencia) | El modelo lleva **conexión residual** (`x_nuevo = x_prev + h`) entre capas y una **cabeza MLP de dos capas** con dropout intermedio. Ninguna de las dos aparece, y la residual condiciona el diseño: obliga a que `dim_oculta` sea divisible por el número de cabezas |

## 4.3.5 Cabeza de predicción y objetivo

| # | Sev. | Frase actual | Qué poner |
|---|---|---|---|
| A | 🟠 | «El umbral concreto **se determinará**… **contemplándose opciones** como una fracción de la desviación típica **o** una división por terciles» | **Terciles**, con umbrales recalculados de forma independiente en cada fold usando solo su train. El capítulo 5 ya lo afirma: 4.3.5 lo deja abierto y se contradice con él |
| B | 🟠 | «**se contempla ponderar** la pérdida de forma inversamente proporcional a la frecuencia de cada clase» | No se ponderó: `usar_pesos_clase = False`, porque con terciles las clases ya están balanceadas. Decisión tomada |
| C | 🔴 | «El procedimiento exacto de corte temporal **se afinará durante la implementación**» | Ver **4.1-C**. Aquí no basta con cambiar el verbo: el mecanismo descrito no puede ejecutarse con GDELT 1.0 |

## 4.3.6 Entrenamiento y evaluación

| # | Sev. | Frase actual | Qué poner |
|---|---|---|---|
| A | 🟠 | «El número concreto de particiones y la longitud de cada ventana **se fijarán** en función del periodo total» | **10 folds**, ventana **expansiva**, medida en **muestras** (no en días de calendario), 250 sesiones de validación por fold, **embargo 0** |
| B | 🟡 | (ausencia) | Declarar el **embargo 0** explícitamente. Es defendible, pero es la clase de detalle que un tribunal pregunta en un esquema walk-forward |
| C | 🟠 | «la evaluación **se repetirá** con varias semillas aleatorias» | 3: (0, 1, 2) |
| D | 🟠 | «**se contempla evaluar** el modelo desde una perspectiva financiera… métricas como el ratio de Sharpe» | Se hizo. Está en §5.4 |
| E | 🔴 | «modelos de series temporales como **una LSTM alimentada únicamente con datos financieros**» | **No existe.** Ver X-1 |
| F | 🔴 | «Resulta particularmente relevante **un baseline que combine los datos financieros con una señal geopolítica agregada pero sin estructura de grafo**» | **No existe.** Ver X-1 |

---

# 5. Incoherencias entre capítulos

## 🔴 X-1 · El capítulo 4 promete baselines que el capítulo 6 admite no haber construido

**DÓNDE:** §4.3.6 último párrafo, frente a §5.3 y §6 segundo párrafo.

§4.3.6 anuncia cinco baselines: trivial, regresión logística, XGBoost, LSTM financiera, y el de señal geopolítica agregada sin grafo. §5.3 evalúa **tres**. Y §6 dice literalmente:

> «Aislar la contribución de cada uno requeriría modelos de referencia adicionales que no se han construido en este piloto debido a la simplificación del proyecto para poder encuadrarlo en la estructura de un trabajo de fin de máster.»

Es decir: el capítulo 6 ya reconoce la limitación con honestidad, y el capítulo 4 sigue prometiéndolos como si fueran parte del diseño ejecutado. **Un lector que vaya de 4.3.6 a 5.3 detecta el hueco antes de llegar al 6.**

**QUÉ HACER:** reescribir el párrafo de §4.3.6 para que enumere los tres baselines efectivamente construidos, y mencionar los otros dos **en el mismo sitio** como lo que son: los que habrían permitido aislar la aportación del grafo y que quedan identificados como línea de trabajo futuro. Así 4.3.6 y 6 dicen lo mismo y la limitación aparece asumida desde el principio en vez de descubierta al final.

Esto además afecta al **objetivo específico 4 del §3.2**: «alcanzando un F1-score superior al de un modelo de referencia sin información geopolítica». Ese modelo es exactamente el que no se construyó. Revisa la redacción del objetivo o declara en §7.1 en qué grado se cumplió.

## 🟠 X-2 · «Crecimiento exponencial de fuentes» frente a los datos propios

**DÓNDE:** §2.1.3 («el crecimiento exponencial de fuentes se debe a la inclusión de webs y otras fuentes contemporáneas, lo que crea una situación en la que en la actualidad se registran más eventos que en el pasado») y §5 («el número de fuentes y de eventos capturados crece de forma acusada con el tiempo… los años más recientes presentan una cobertura considerablemente más densa»).

**QUÉ PASA:** los eventos por año del propio dataset van **a la baja**:

| Año | Eventos | Año | Eventos |
|---|---:|---|---:|
| 2015 | 2.607.632 | 2021 | 1.452.911 |
| 2016 | 2.927.300 | 2022 | 1.344.322 |
| 2017 | 2.673.486 | 2023 | 1.721.325 |
| 2018 | 2.565.547 | 2024 | 1.589.822 |
| 2019 | 2.179.134 | 2025 | 1.396.372 |
| 2020 | 1.736.073 | | |

El máximo es 2016 y desde ahí cae. Es un problema de la fuente, no del trabajo: GDELT 1.0 dejó de ampliar cobertura cuando 2.0 tomó el relevo en 2015. Pero el capítulo 5 usa esa afirmación **para justificar el rango 2015-2025**, y con estos datos el argumento se invierte.

**QUÉ HACER:** corregir la afirmación en los dos sitios, y considerar meter el gráfico de eventos por año en §4.1. Convierte una contradicción en una limitación documentada de la fuente.

## 🟡 X-3 · El barrido de UMBRAL_SHORT se hace sobre el propio conjunto de test

**DÓNDE:** §5.4, tabla de umbrales 0,40 a 0,80.

**QUÉ PASA:** el umbral que maximiza la rentabilidad se elige mirando el resultado sobre las mismas predicciones fuera de muestra que se están evaluando. Es selección de hiperparámetro sobre el test. Ya has añadido el aviso correcto sobre la concatenación de folds solapados, que era el problema mayor; este es el que queda.

**QUÉ HACER:** una frase que aclare que la tabla es un análisis de sensibilidad y no una selección de configuración, y que el valor usado en §5.4 es el fijado a priori en la configuración (0,70).

---

# 6. Orden de trabajo recomendado

## Bloque 1 — Media hora, máximo impacto

1. **Buscar y reemplazar «HGT»** en todo el capítulo 4. Cuatro apariciones (4.2.2, 4.2.4, 4.3.4 ×2) presentándolo como el modelo usado. Es el error más visible y el más barato de arreglar.
2. **4.3.2-E**: quitar el párrafo de las macro en el nodo Estados Unidos, o reescribirlo diciendo dónde acabaron realmente.
3. **4.3.2-A**: quitar la OPEP+.
4. **4.3.2-D**: PIB → comercio bilateral.

## Bloque 2 — Los errores de hecho restantes

5. **4.3.2-F**: DXY inactivo y `USAR_MACRO = False`.
6. **4.2.4-A**: los ejemplos «militar / comercial / diplomático» no son posibles con QuadClass.
7. **4.2.3-B**: `to_hetero()` → `HeteroConv`.
8. **4.2.2-B / 4.3.2-H**: declarar la tercera relación `market→country` y las siete features de arista.
9. **4.3.4-C**: no hay normalización.
10. **4.2.1-A**: reescribir el rechazo de CTDG.

## Bloque 3 — El barrido de tiempo verbal

Los 19 puntos 🟠. Mecánico: cada «se determinará / se contempla / se ajustará / no se ha cerrado» pasa a pretérito con su valor. Están todos tabulados arriba, apartado por apartado.

## Bloque 4 — Lo que añade valor

11. **4.1-A**: la tabla exploración / producción. Es el cambio que más sube el nivel metodológico del capítulo por unidad de esfuerzo.
12. **4.1-B**: la tabla del embudo real.
13. **4.2.1-B**: subir la tabla de decay por QuadClass a 4.2.1.
14. **X-1**: alinear 4.3.6 con lo que dice el capítulo 6.
15. **4.1-E**: la tabla de las 13 columnas.

## Bloque 5 — Antes de entregar

16. **4.1-C / 4.3.5-C**: decidir cómo se declara el corte horario inerte.
17. **X-2**: corregir el crecimiento de fuentes en §2.1.3 y §5.
18. Contar los parámetros del modelo y poner la cifra real en 4.2.5.
19. Numerar todas las tablas y figuras de una pasada, y rehacer los dos índices.
20. Unificar el separador de millar en todo el documento.

---

# Anexo · Valores del código citados en este documento

Todos verificados contra HEAD.

| Concepto | Valor | Fuente |
|---|---|---|
| Roster | 20 países, sin OPEP+ | `src/utils/paises.py:45` |
| Filtro de cobertura | `NumMentions >= 5` | `config.py` · `MIN_NUM_MENTIONS` |
| Columnas cargadas | 13 de 58 | `descarga_gdelt.py` · `COLUMNAS_RELEVANTES` |
| λ base | 0,0693 (vida media 10 días) | `config.py:133` |
| Multiplicadores λ | 1,5 / 1,0 / 0,7 / 0,4 | `config.py:150` |
| Ventana de decay | 60 días | `config.py:159` |
| Features nodo país | 11 | `grafo.py:51` |
| Features nodo mercado | 9 (3 inactivas) | `grafo.py:57` |
| Features arista país-país | 7 (3 + one-hot QuadClass) | `grafo.py:62` |
| Features arista país-mercado | 1 | `grafo.py:66` |
| Capa de mensajes | `GATv2Conv` vía `HeteroConv` | `arquitectura.py:90` |
| Relaciones | 3 | `arquitectura.py:92-112` |
| Residual | `x_prev + h` | `arquitectura.py:182` |
| Cabeza | MLP 2 capas + dropout | `arquitectura.py:123` |
| dim_oculta / capas / cabezas / dropout | 64 / 2 / 4 / 0,3 | `config.py` · `ConfigModelo` |
| learning rate / weight decay | 1e-3 / 1e-4 | `config.py` · `ConfigEntrenamiento` |
| Épocas máx. / paciencia | 100 / 15 | `config.py` · `ConfigEntrenamiento` |
| Validación interna | 15 % final del train, mín. 20 muestras | `config.py` · `fraccion_val_interna` |
| Pesos de clase | `False` | `config.py` · `usar_pesos_clase` |
| Semillas | (0, 1, 2) | `config.py` · `semillas` |
| Folds / modo / embargo | 10 / expansiva / 0 | `config.py` · `ConfigWalkForward` |

## Datos medidos sobre el dataset

| Concepto | Valor |
|---|---|
| Embudo (6 días muestreados) | 1.029.338 → 550.331 (53,5 %) → 238.688 (23,2 %) |
| Eventos totales 2015-2025 | 22.193.924 |
| Aristas totales | 2.198.657 |
| QuadClass, eventos | 63,3 / 11,0 / 12,9 / 12,7 % |
| QuadClass, aristas | 39,2 / 21,0 / 20,5 / 19,3 % |
| Ficheros GDELT 1.0 descargados | 3.998 |
| Par dominante | USA→USA, 5.293.208 eventos (24 % del total) |

## Pendiente de medir

- Distribución por **EventRootCode** sobre el dataset filtrado. Reforzaría 4.2.4 pasando de «QuadClass tiene volumen» a «EventRootCode deja N de 20 categorías por debajo de X eventos».
- **Recuento exacto de parámetros** del modelo.
