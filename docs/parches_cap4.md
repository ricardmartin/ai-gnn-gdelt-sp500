# Parches de texto · Capítulo 4

Texto listo para pegar en `EntregaFINAL_TFM_Aguiló_Martín.docx`. Los identificadores son los de [checklist_capitulo4.md](checklist_capitulo4.md).

---

# §4.1 — reestructuración completa

## El diagnóstico

§4.1 tiene dos problemas de fondo, no de forma:

1. **Dedica seis páginas a técnicas que no están en el modelo.** Normalización de URL, texto sintético, vectores MiniLM, agrupamiento por coseno y LDA. El pipeline real (`src/datos/preprocesar.py`) no ejecuta ninguna.
2. **Nunca explica cómo se hace el filtrado de verdad.** No hay una descripción de principio a fin: de los CSV crudos a la tabla que alimenta el grafo. El lector sale del apartado sin saber qué hace realmente el sistema.

El segundo es el más grave, porque §4.1 se titula «Filtrado de datos» y es justo lo que no cuenta.

## La decisión: comprimir y reubicar, no borrar

La exploración **no se borra** por dos razones concretas del propio documento:

- **OE6 promete** «documentación explícita de las decisiones metodológicas **y de sus alternativas descartadas**». Borrarla convierte un fallo de encuadre en un objetivo incumplido.
- **§4.3 abre diciendo** «Tras justificar en el apartado anterior las decisiones técnicas **y las alternativas descartadas**». Si se borra, esa frase deja de ser cierta.

Además, sin ella queda sin respuesta la pregunta «¿por qué no deduplicasteis semánticamente?». Con ella, la respuesta es «lo hicimos, el 94,4 % salieron singletons, no servía», que es mucho más fuerte.

**Lo que sí se hace:** comprimir la exploración a un párrafo más una tabla de balance, y mover el detalle de laboratorio al **Anexo A**, que ahora mismo está vacío y ya figura como pendiente en el checklist.

## Estructura resultante

| | Bloque | Origen |
|---|---|---|
| 1 | Elección de GDELT 1.0 | existente, con arreglo |
| 2 | Esquema y columnas retenidas | existente + tabla nueva |
| 3 | Fase de exploración, resumida | **comprime 6 páginas a 1 párrafo** |
| 4 | Tabla de balance de la exploración | **nuevo** |
| 5 | El pipeline real, paso a paso | **nuevo — es el hueco principal** |
| 6 | Los dos filtros, bien descritos | reescribe los existentes |
| 7 | De eventos a insumo del grafo: las dos agregaciones | **nuevo** |
| 8 | Tabla del embudo | **nuevo** |
| 9 | Garantía temporal: el corte horario es inerte | **nuevo** |

De seis páginas a página y media, cumpliendo OE6 y contando por fin lo que se hace.

---

# Bloque 1 · Elección de GDELT 1.0

Se mantiene el texto actual con **un cambio**. La viñeta de los veinte años no se sostiene: el estudio va de 2015 a 2025 y GDELT 2.0 cubre ese rango entero, así que la profundidad histórica de 1.0 no es una ventaja *para este trabajo*.

**DICE:**
> GKG y 2.0 tienen noticias desde el 2013 y 2015, mientras que su versión 1.0 tiene más de 20 años de noticias.

**ESCRIBE:**
> La versión 1.0 cubre desde 1979, frente a 2013 de GKG y 2015 de la 2.0. Para el periodo de este estudio (2015-2025) las tres alternativas ofrecen cobertura suficiente, de modo que la profundidad histórica de 1.0 no resulta determinante aquí; sí lo sería para una eventual extensión del trabajo a periodos anteriores, que queda apuntada como línea futura.

---

# Bloque 2 · Esquema y columnas retenidas

Se mantiene el texto actual de las 58 columnas y las cinco numéricas. **AÑADIR** después de la lista de las cinco y antes de «El resto se conserva como cadena…»:

> De las 58 columnas del esquema, el pipeline retiene trece, que son las que alimentan la construcción del grafo:

| Grupo | Columnas |
|---|---|
| Identificación y fecha | `GLOBALEVENTID`, `SQLDATE`, `DATEADDED` |
| Actores | `Actor1CountryCode`, `Actor2CountryCode` |
| Codificación del evento | `EventCode`, `EventRootCode`, `QuadClass` |
| Intensidad y tono | `GoldsteinScale`, `AvgTone` |
| Cobertura mediática | `NumMentions`, `NumSources`, `NumArticles` |

> Las 45 restantes —geolocalización detallada, tipos y códigos religiosos o étnicos de los actores, URL de origen— se descartan en la carga.

---

# Bloque 3 · La exploración, resumida

**BORRAR** todo lo que va desde «Es necesario realizar una limpieza inicial para intentar minimizar la cantidad de repetidos…» hasta «…Esto cuantifica la composición temática del corpus filtrado.», es decir: normalización de URL, resultados de URLs repetidas, texto sintético con sus ejemplos, granularidad y modelo MiniLM, algoritmo de agrupamiento, top-3 de grupos, comprobación sobre tres días y todo el bloque de LDA con su tabla.

**ESCRIBE en su lugar:**

> Antes de fijar el procedimiento definitivo se abrió una fase de exploración sobre una muestra de un único día, con el objetivo de reducir el volumen de eventos sin perder señal. La hipótesis de partida era que buena parte de las filas de GDELT son cobertura repetida de un mismo suceso, y que identificar y colapsar esas repeticiones permitiría trabajar con un corpus mucho menor. Se evaluaron cuatro técnicas: normalización y deduplicación de URL, construcción de un texto sintético por evento a partir del *slug* de la URL y de los metadatos CAMEO, proyección de esos textos a un espacio vectorial denso mediante `all-MiniLM-L6-v2` con agrupamiento posterior por similitud coseno, y un modelo de tópicos LDA sobre el corpus resultante.
>
> Ninguna de las cuatro se incorporó al pipeline definitivo. El motivo común es que la repetición que GDELT introduce no es la que estas técnicas detectan: la deduplicación por URL captura la repetición exacta, que es la menos problemática, mientras que el agrupamiento semántico, con un umbral de 0,80 sobre la similitud coseno, dejó el 94,4 % de los elementos como grupos de un solo miembro y reunió los grandes por afinidad temática en lugar de por identidad de suceso. El LDA, aplicado sobre textos de mediana 18 tokens, produjo tópicos que recogen concurrencia de nombres de países y ciudades, sin un significado geopolítico que pudiera convertirse en característica del modelo. El detalle de los experimentos, con las cifras de cada paso y los ejemplos examinados, se recoge en el Anexo A.
>
> El balance de la exploración es el siguiente:

| Técnica evaluada | ¿En el pipeline final? | Motivo |
|---|---|---|
| Normalización y deduplicación de URL | No | Detecta la URL repetida exacta, pero no el mismo suceso cubierto por medios distintos, que es el caso relevante |
| Texto sintético y vectores densos (MiniLM) | No | El coste de calcular y almacenar los vectores para las 2.751 jornadas del estudio no se compensa con la reducción obtenida |
| Agrupamiento por similitud coseno (k-NN, umbral 0,80) | No | El 94,4 % de los grupos son singletons y los mayores agrupan por afinidad temática, no por suceso |
| Tópicos LDA sobre el corpus | No | Los tópicos recogen concurrencia de palabras, no temas con significado geopolítico aprovechable |
| Filtro de cobertura mediática (`NumMentions ≥ 5`) | **Sí** | Reduce el volumen a la mitad descartando ruido local, con un criterio simple y auditable |
| Filtro de roster geopolítico | **Sí** | Concentra la señal en los veinte actores relevantes para el mercado estadounidense (§4.2.4) |

> La conclusión de la fase exploratoria es, por tanto, que la reducción de volumen se resuelve mejor con dos filtros de criterio explícito que con deduplicación semántica. Las técnicas descartadas quedan documentadas como referencia para trabajo futuro, en particular ante una eventual migración a GDELT 2.0, cuya mayor densidad de eventos sí podría justificar su coste.

> ⚠️ El motivo que se da para MiniLM («el coste no compensa») es el único que **no** está respaldado por una cifra del texto original. Si el motivo real fue otro, sustitúyelo.

---

# Bloque 4 · El pipeline real, paso a paso — **el hueco principal**

Este bloque **no existe hoy en el documento**. Es lo que le falta a un apartado titulado «Filtrado de datos».

**AÑADIR** a continuación:

> Fijadas las conclusiones de la exploración, el procedimiento definitivo consta de cinco etapas que se aplican a cada uno de los 3.998 ficheros diarios del periodo.
>
> **Ingesta.** Se descarga el fichero comprimido de cada jornada desde el repositorio público de GDELT y se carga con el esquema fijo de 58 columnas, forzando el tipado numérico de las cinco variables continuas y conservando el resto como cadena para no destruir los códigos CAMEO y FIPS.
>
> **Filtro de relevancia geopolítica.** Se descartan los eventos en los que ninguno de los dos actores pertenece al roster de veinte países.
>
> **Filtro de cobertura mediática.** De los supervivientes se conservan los que alcanzan al menos cinco menciones en la jornada.
>
> **Descarte de incompletos.** Se eliminan las filas sin valor en `GoldsteinScale`, `AvgTone` o `QuadClass`, que son las tres variables que el grafo necesita para construir cualquier arista.
>
> **Agregación.** Los eventos supervivientes se resumen en dos tablas, una orientada a las aristas y otra a las características de los nodos, que son el insumo directo del grafo descrito en §4.3.
>
> El procesamiento se realiza por tramos y con volcado intermedio a disco, ya que el conjunto completo no cabe en memoria: cada tramo se preprocesa, se agrega y se persiste antes de liberar los datos brutos correspondientes.

---

# Bloque 5 · Los dos filtros, bien descritos — 🔴 4.1-G y un error de hecho

**BORRAR** los dos puntos actuales («Concurrencia de fenómenos…», «Relevancia geopolítica…») y el párrafo del umbral («Se han hecho pruebas para ver cuál es el umbral…»).

**Dos problemas que esto arregla:**

**Error de hecho.** El texto dice «Conservar noticias que mínimo aparezcan en **X medios distintos**». Eso describe `NumSources`. El filtro implementado opera sobre **`NumMentions`**, que son menciones, no medios: un evento con `NumMentions = 5` puede proceder de un solo medio que lo mencionó cinco veces. Es incómodo porque §2.1.3 distingue explícitamente las dos variables, de modo que el documento se contradice consigo mismo.

**Imprecisión.** «Al menos un actor de gran importancia» no dice que el filtro sea un **OR** sobre los dos actores, que es lo que hace `filtrar_roster` y lo que explica que entren eventos con un solo extremo relevante.

**ESCRIBE:**

> Ambos filtros merecen precisión, porque de su definición exacta depende qué eventos llegan al grafo.
>
> **Cobertura mediática.** Se conservan los eventos con `NumMentions ≥ 5`, es decir, los mencionados al menos cinco veces en la prensa monitorizada durante la jornada. Conviene subrayar que el criterio no exige cinco medios distintos sino cinco menciones: un mismo medio que cubre el suceso repetidamente ya lo satisface. El objetivo no es garantizar pluralidad de fuentes, sino descartar el ruido local, es decir, sucesos de alcance municipal o estatal que GDELT registra pero que no tienen efecto medible sobre el mercado estadounidense. El umbral se fijó en cinco tras comprobar que valores superiores empezaban a eliminar eventos con interés potencial para el grafo.
>
> **Relevancia geopolítica.** Se conservan los eventos en los que **al menos uno** de los dos actores pertenece al roster de veinte países definido en §4.2.4. El filtro es una disyunción sobre `Actor1` y `Actor2`, no una conjunción, y la diferencia importa: un evento CHN→SYR se conserva aunque Siria no pertenezca al roster, porque informa sobre el comportamiento de China, y lo mismo ocurre en sentido inverso con SYR→CHN. Exigir que ambos extremos fueran relevantes habría descartado toda la actividad de los veinte actores hacia el resto del mundo, que es precisamente donde se manifiesta buena parte de la tensión geopolítica.

---

# Bloque 6 · De eventos a insumo del grafo — **nuevo**

Este bloque documenta una decisión de diseño que **el código implementa pero la memoria no menciona en ningún sitio**, y que es la contrapartida natural del filtro OR.

**El hallazgo.** El filtro OR deja pasar eventos con un solo extremo en el roster, pero esos eventos **no pueden formar una arista** (falta un nodo). Si el pipeline se limitara a construir aristas, todo lo que el filtro OR pretendía capturar se perdería en el paso siguiente. El código resuelve esto con **dos agregaciones distintas**: `agregar_eventos_por_dia_y_par`, que exige ambos extremos y produce las aristas, y `agregar_participacion_por_dia_y_pais`, que despliega cada evento en una o dos filas de participación y alimenta las características de los nodos, incluidos los eventos de un solo actor.

Sin esto, el argumento del filtro OR queda cojo: se justifica conservar CHN→SYR y luego no se dice dónde acaba esa información.

**AÑADIR:**

> El último paso convierte los eventos supervivientes en las dos estructuras que consume el grafo, y aquí reaparece la consecuencia del filtro OR. Un evento como CHN→SYR se conserva porque China pertenece al roster, pero no puede constituir una arista país-país: uno de sus extremos no es un nodo del grafo. Si el preprocesado se limitase a construir aristas, toda la información que el filtro OR pretendía retener se perdería en este punto.
>
> Para evitarlo se producen dos agregaciones complementarias. La primera agrupa por fecha, país de origen, país de destino y QuadClass, y exige que ambos extremos pertenezcan al roster; cada fila resultante es una arista resumen entre dos actores en una jornada, con el número de eventos, la escala de Goldstein media, el tono medio y el total de menciones. La segunda agrupa por fecha, país, rol y QuadClass, desplegando cada evento en una o dos filas de participación según cuántos de sus actores estén en el roster; esta segunda tabla sí recoge los eventos de un solo actor y es la que alimenta las características de los nodos país descritas en §4.3.2.
>
> De este modo, un evento CHN→SYR no genera arista pero sí contribuye al recuento de actividad, al tono medio y a la distribución por QuadClass del nodo China, que es exactamente lo que el filtro OR perseguía.

---

# Bloque 7 · Tabla del embudo — 🔴 4.1-B

**AÑADIR** a continuación:

> El efecto acumulado de los filtros sobre una muestra de seis jornadas repartidas a lo largo del periodo es el siguiente:

| Etapa | Eventos | % sobre el bruto |
|---|---|---|
| Eventos brutos en los ficheros diarios | 701.373 | 100,0 % |
| Tras el filtro de roster (20 países, OR) | 373.774 | 53,3 % |
| Tras `NumMentions ≥ 5` | 157.908 | 22,5 % |
| Tras descartar incompletos | 157.908 | 22,5 % |

> Los dos filtros reducen el volumen a algo menos de una cuarta parte. El descarte de incompletos no elimina ninguna fila adicional, lo que indica que los eventos que superan los dos filtros anteriores vienen completos en los campos que el modelo necesita.

> ⚠️ **Cifras reproducidas el 2026-09-02** sobre `data/raw`, muestreando 2015-01-01, 2017-04-14, 2019-07-27, 2021-11-07, 2024-02-21 y 2026-06-23. La revisión daba 1.029.338 → 550.331 (53,5 %) → 238.688 (23,2 %) con otros seis días; **los porcentajes coinciden**, que es lo que importa. Usa unas u otras, pero **declara siempre sobre qué días se calculan**: presentarlo como el embudo del dataset completo sería incorrecto.

---

# Bloque 8 · Garantía temporal: el corte horario es inerte — 🔴 4.1-C

**AÑADIR** como cierre de §4.1:

> Queda por precisar cómo se garantiza que el grafo de una jornada no incorpore información posterior al momento en que la predicción debería emitirse. El pipeline conserva el campo `DATEADDED`, previsto para reasignar al día siguiente los eventos publicados después del cierre de mercado. En la práctica ese mecanismo no llega a activarse: GDELT 1.0 registra la fecha sin la hora, de modo que todos los eventos de una misma jornada comparten marca temporal y ninguno resulta reasignado. La separación queda garantizada por la propia cadencia diaria de la fuente, que publica un único fichero consolidado por jornada, y no por el corte horario. El campo se mantiene en el pipeline porque una eventual migración a GDELT 2.0, que sí registra la hora de cada evento, lo haría necesario de inmediato.

---

# Anexo A · Contenido a trasladar

El Anexo A está vacío y figura como pendiente en el checklist. Recibe **todo el material que sale de §4.1**, que ya está escrito y solo hay que mover bajo estos epígrafes:

**A.1 · Normalización de URL.** Las cinco reglas, los recuentos (118.201 filas, 24.412 URLs únicas), las tres URLs más repetidas y el análisis de las dos genéricas.

**A.2 · Construcción del texto sintético.** Las tres fuentes (slug, metadatos, etiquetas CAMEO), el filtro de menos de tres tokens con sus porcentajes, la estadística de longitud y los dos ejemplos.

**A.3 · Agrupamiento semántico.** Granularidad, modelo MiniLM, el algoritmo k-NN con umbral 0,80, el resultado (22.572 puntos, 19.423 grupos, 94,4 % singletons), el top-3 de grupos y el análisis del umbral.

**A.4 · Validación sobre tres jornadas.** El párrafo de estabilidad de los porcentajes.

**A.5 · Tópicos LDA.** La tabla de cinco tópicos y su interpretación.

Al trasladarlo, **corregir de paso estas erratas**, que viajan con el texto:

| Dice | Escribe |
|---|---|
| «las **siguiente** reglas» | **siguientes** |
| «118 201» · «24 412» · «107 248» · «10 953» · «22 572» · «19 423» | **118.201** · **24.412** · **107.248** · **10.953** · **22.572** · **19.423** |
| «…farewell **118x**» | **118 veces** |
| «muestran **webs de que no se ha encontrado noticias**» | «muestran **páginas de error sin noticia asociada**» |
| «el **9.3 %** de las **filas(10 953)**» | «el **9,3 %** de las **filas (10.953)**» |
| «Se calcula **un representaciones vectoriales** por URL única» | **una representación vectorial** |
| «**0.80**», «**94.4 %**», «**5.6 %**», «**1.16**» | **0,80** · **94,4 %** · **5,6 %** · **1,16** |
| «**Grupo137**» | **Grupo 137** |
| «se ha seleccionado tres días… **se ha puesto** a prueba» | «se **han seleccionado**… se **han puesto**» |
| «**lo cuál** son datos muy elevados» | **lo cual** |
| «complementar **el grupos** y descubrir» | **los grupos** |
| Cabecera LDA «**Document**» | **Documentos** |
| «3,306» · «3,794» · «2,003» · «4,434» · «2,865» | **3.306** · **3.794** · **2.003** · **4.434** · **2.865** |

La lista de los tres grupos mayores tiene además la numeración rota: el primero sin número, los otros como «2.» y «3.».

**La figura de reducción** cuya barra remite a «(§4.7)», apartado inexistente, se va también al anexo. Corregir la referencia al epígrafe que le corresponda.
