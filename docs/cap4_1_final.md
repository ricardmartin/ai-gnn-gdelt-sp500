# 4.1 Filtrado de datos

*Versión final consolidada. Reemplaza íntegramente el §4.1 actual de `EntregaFINAL_TFM_Aguiló_Martín.docx`. El material desplazado al Anexo A aparece al final de este fichero.*

---

## 4.1.1 Elección de GDELT 1.0

La fuente de datos que se ha escogido para el proyecto es GDELT 1.0 Events. La elección se ha tomado tras descartar su versión 2.0 y GKG, y se sustenta en dos aspectos:

- Aunque la versión 2.0 ofrece una granularidad de quince minutos, la predicción de este trabajo se emite una vez por sesión bursátil, por lo que todo el contenido tendría que reagruparse a escala diaria. La cadencia de 1.0 se ajusta a esa unidad de decisión y reduce el coste de ingesta: 3.998 ficheros frente a unos 381.000 para el mismo periodo.
- La versión 1.0 cubre desde 1979, frente a 2013 de GKG y 2015 de la 2.0. Para el periodo de este estudio (2015-2025) las tres alternativas ofrecen cobertura suficiente, de modo que la profundidad histórica de 1.0 no resulta determinante aquí; sí lo sería para una eventual extensión del trabajo a periodos anteriores, que queda apuntada como línea futura.

Cada fichero diario en formato CSV contiene entre 100.000 y 300.000 eventos. Para fechas anteriores al 1 de abril de 2013, GDELT empaqueta los CSV en ficheros mensuales, y anuales antes de 2005.

## 4.1.2 Esquema y columnas retenidas

GDELT 1.0 define un esquema fijo de 58 columnas sin cabecera. Para cargarlo con los tipos correctos se reproduce la lista de nombres y se identifican las siguientes columnas numéricas:

- `GoldsteinScale`: puntuación del posible impacto de un evento sobre la estabilidad de un país. Escala fija de -10 (máximo conflicto) a +10 (máximo beneficio).
- `NumMentions`: veces que se nombra el evento durante el día.
- `NumSources`: número de fuentes de información distintas que informan del evento.
- `NumArticles`: número de artículos distintos que han nombrado la noticia.
- `AvgTone`: tono medio de los documentos que mencionan el evento.

De las 58 columnas del esquema, el pipeline retiene trece, que son las que alimentan la construcción del grafo:

| Grupo | Columnas |
|---|---|
| Identificación y fecha | `GLOBALEVENTID`, `SQLDATE`, `DATEADDED` |
| Actores | `Actor1CountryCode`, `Actor2CountryCode` |
| Codificación del evento | `EventCode`, `EventRootCode`, `QuadClass` |
| Intensidad y tono | `GoldsteinScale`, `AvgTone` |
| Cobertura mediática | `NumMentions`, `NumSources`, `NumArticles` |

Las 45 restantes —geolocalización detallada, tipos y códigos religiosos o étnicos de los actores, URL de origen— se descartan en la carga. El resto se conserva como cadena para mantener compatibilidad con los códigos CAMEO (Conflict and Mediation Event Observations) y FIPS (Federal Information Processing Standards), que aunque sean numéricos en apariencia (01, 02...) deben tratarse como categóricos.

GDELT codifica los eventos mediante el sistema CAMEO, que define tres niveles de granularidad:

- `EventRootCode`: grandes categorías de comportamiento, ordenadas de máxima cooperación a máximo conflicto.
- `EventBaseCode`: subdivide cada raíz en subtipos.
- `EventCode`: detalle fino sobre el subtipo.

## 4.1.3 Fase de exploración

Antes de fijar el procedimiento definitivo se abrió una fase de exploración sobre una muestra de un único día, con el objetivo de reducir el volumen de eventos sin perder señal. La hipótesis de partida era que buena parte de las filas de GDELT son cobertura repetida de un mismo suceso, y que identificar y colapsar esas repeticiones permitiría trabajar con un corpus mucho menor. Se evaluaron cuatro técnicas: normalización y deduplicación de URL, construcción de un texto sintético por evento a partir del *slug* de la URL y de los metadatos CAMEO, proyección de esos textos a un espacio vectorial denso mediante `all-MiniLM-L6-v2` con agrupamiento posterior por similitud coseno, y un modelo de tópicos LDA sobre el corpus resultante.

Ninguna de las cuatro se incorporó al pipeline definitivo. El motivo común es que la repetición que GDELT introduce no es la que estas técnicas detectan: la deduplicación por URL captura la repetición exacta, que es la menos problemática, mientras que el agrupamiento semántico, con un umbral de 0,80 sobre la similitud coseno, dejó el 94,4 % de los elementos como grupos de un solo miembro y reunió los grandes por afinidad temática en lugar de por identidad de suceso. El LDA, aplicado sobre textos de mediana 18 tokens, produjo tópicos que recogen concurrencia de nombres de países y ciudades, sin un significado geopolítico que pudiera convertirse en característica del modelo. El detalle de los experimentos, con las cifras de cada paso y los ejemplos examinados, se recoge en el Anexo A.

El balance de la exploración es el siguiente:

| Técnica evaluada | ¿En el pipeline final? | Motivo |
|---|---|---|
| Normalización y deduplicación de URL | No | Detecta la URL repetida exacta, pero no el mismo suceso cubierto por medios distintos, que es el caso relevante |
| Texto sintético y vectores densos (MiniLM) | No | El coste de calcular y almacenar los vectores para las 2.751 jornadas del estudio no se compensa con la reducción obtenida |
| Agrupamiento por similitud coseno (k-NN, umbral 0,80) | No | El 94,4 % de los grupos son singletons y los mayores agrupan por afinidad temática, no por suceso |
| Tópicos LDA sobre el corpus | No | Los tópicos recogen concurrencia de palabras, no temas con significado geopolítico aprovechable |
| Filtro de cobertura mediática (`NumMentions ≥ 5`) | **Sí** | Reduce el volumen a la mitad descartando ruido local, con un criterio simple y auditable |
| Filtro de roster geopolítico | **Sí** | Concentra la señal en los veinte actores relevantes para el mercado estadounidense (§4.2.4) |

La conclusión de la fase exploratoria es, por tanto, que la reducción de volumen se resuelve mejor con dos filtros de criterio explícito que con deduplicación semántica. Las técnicas descartadas quedan documentadas como referencia para trabajo futuro, en particular ante una eventual migración a GDELT 2.0, cuya mayor densidad de eventos sí podría justificar su coste.

## 4.1.4 Pipeline definitivo

Fijadas las conclusiones de la exploración, el procedimiento definitivo consta de cinco etapas que se aplican a cada uno de los 3.998 ficheros diarios del periodo.

**Ingesta.** Se descarga el fichero comprimido de cada jornada desde el repositorio público de GDELT y se carga con el esquema fijo de 58 columnas, forzando el tipado numérico de las cinco variables continuas y conservando el resto como cadena para no destruir los códigos CAMEO y FIPS.

**Filtro de relevancia geopolítica.** Se descartan los eventos en los que ninguno de los dos actores pertenece al roster de veinte países.

**Filtro de cobertura mediática.** De los supervivientes se conservan los que alcanzan al menos cinco menciones en la jornada.

**Descarte de incompletos.** Se eliminan las filas sin valor en `GoldsteinScale`, `AvgTone` o `QuadClass`, que son las tres variables que el grafo necesita para construir cualquier arista.

**Agregación.** Los eventos supervivientes se resumen en dos tablas, una orientada a las aristas y otra a las características de los nodos, que son el insumo directo del grafo descrito en §4.3.

El procesamiento se realiza por tramos y con volcado intermedio a disco, ya que el conjunto completo no cabe en memoria: cada tramo se preprocesa, se agrega y se persiste antes de liberar los datos brutos correspondientes.

## 4.1.5 Los dos filtros

Ambos filtros merecen precisión, porque de su definición exacta depende qué eventos llegan al grafo.

**Cobertura mediática.** Se conservan los eventos con `NumMentions ≥ 5`, es decir, los mencionados al menos cinco veces en la prensa monitorizada durante la jornada. Conviene subrayar que el criterio no exige cinco medios distintos sino cinco menciones: un mismo medio que cubre el suceso repetidamente ya lo satisface. El objetivo no es garantizar pluralidad de fuentes, sino descartar el ruido local, es decir, sucesos de alcance municipal o estatal que GDELT registra pero que no tienen efecto medible sobre el mercado estadounidense. El umbral se fijó en cinco tras comprobar que valores superiores empezaban a eliminar eventos con interés potencial para el grafo.

**Relevancia geopolítica.** Se conservan los eventos en los que **al menos uno** de los dos actores pertenece al roster de veinte países definido en §4.2.4. El filtro es una disyunción sobre `Actor1` y `Actor2`, no una conjunción, y la diferencia importa: un evento CHN→SYR se conserva aunque Siria no pertenezca al roster, porque informa sobre el comportamiento de China, y lo mismo ocurre en sentido inverso con SYR→CHN. Exigir que ambos extremos fueran relevantes habría descartado toda la actividad de los veinte actores hacia el resto del mundo, que es precisamente donde se manifiesta buena parte de la tensión geopolítica.

## 4.1.6 De eventos a insumo del grafo: las dos agregaciones

El último paso convierte los eventos supervivientes en las dos estructuras que consume el grafo, y aquí reaparece la consecuencia del filtro OR. Un evento como CHN→SYR se conserva porque China pertenece al roster, pero no puede constituir una arista país-país: uno de sus extremos no es un nodo del grafo. Si el preprocesado se limitase a construir aristas, toda la información que el filtro OR pretendía retener se perdería en este punto.

Para evitarlo se producen dos agregaciones complementarias. La primera agrupa por fecha, país de origen, país de destino y QuadClass, y exige que ambos extremos pertenezcan al roster; cada fila resultante es una arista resumen entre dos actores en una jornada, con el número de eventos, la escala de Goldstein media, el tono medio y el total de menciones. La segunda agrupa por fecha, país, rol y QuadClass, desplegando cada evento en una o dos filas de participación según cuántos de sus actores estén en el roster; esta segunda tabla sí recoge los eventos de un solo actor y es la que alimenta las características de los nodos país descritas en §4.3.2.

De este modo, un evento CHN→SYR no genera arista pero sí contribuye al recuento de actividad, al tono medio y a la distribución por QuadClass del nodo China, que es exactamente lo que el filtro OR perseguía.

## 4.1.7 Efecto acumulado de los filtros

El efecto acumulado de los filtros sobre una muestra de seis jornadas repartidas a lo largo del periodo (2015-01-01, 2017-04-14, 2019-07-27, 2021-11-07, 2024-02-21 y 2026-06-23) es el siguiente:

| Etapa | Eventos | % sobre el bruto |
|---|---|---|
| Eventos brutos en los ficheros diarios | 701.373 | 100,0 % |
| Tras el filtro de roster (20 países, OR) | 373.774 | 53,3 % |
| Tras `NumMentions ≥ 5` | 157.908 | 22,5 % |
| Tras descartar incompletos | 157.908 | 22,5 % |

Los dos filtros reducen el volumen a algo menos de una cuarta parte. El descarte de incompletos no elimina ninguna fila adicional, lo que indica que los eventos que superan los dos filtros anteriores vienen completos en los campos que el modelo necesita.

## 4.1.8 Garantía temporal: el corte horario es inerte

Queda por precisar cómo se garantiza que el grafo de una jornada no incorpore información posterior al momento en que la predicción debería emitirse. El pipeline conserva el campo `DATEADDED`, previsto para reasignar al día siguiente los eventos publicados después del cierre de mercado. En la práctica ese mecanismo no llega a activarse: GDELT 1.0 registra la fecha sin la hora, de modo que todos los eventos de una misma jornada comparten marca temporal y ninguno resulta reasignado. La separación queda garantizada por la propia cadencia diaria de la fuente, que publica un único fichero consolidado por jornada, y no por el corte horario. El campo se mantiene en el pipeline porque una eventual migración a GDELT 2.0, que sí registra la hora de cada evento, lo haría necesario de inmediato.

---

# Anexo A · Fase de exploración sobre una jornada

*Material desplazado desde §4.1. Documenta las técnicas evaluadas y descartadas durante la exploración inicial, conservado como referencia metodológica (OE6).*

## A.1 · Normalización de URL

Para reducir la cantidad de filas repetidas —una noticia actualizada varias veces al día, o varios medios cubriendo el mismo hecho— se aplicó en primer lugar una normalización de la URL, único campo que aporta información directa sobre el hecho cubierto. Las reglas fueron las siguientes:

- Conversión a minúsculas (`Example.com` y `example.com` apuntan al mismo recurso).
- Eliminación de los puertos por defecto `:80` y `:443`.
- Eliminación de parámetros de traza (`?utm_source=...`, `?ref=...`), que no afectan al contenido.
- Eliminación de fragmentos (`#section`), que tampoco modifican el recurso.
- Supresión de la barra final, que señala que la URL apunta a un directorio en lugar de a un archivo.

Los resultados fueron:

- Filas antes: 118.201
- Descartadas por URL no interpretable: 0
- Filas tras normalización: 118.201
- URLs únicas: 24.412

Es decir, cada artículo genera de media casi cinco filas en GDELT, y solo poco más de una cuarta parte aparece una única vez.

Las URLs más utilizadas fueron: `https://targetednews.com/pr_disp.php` (158 repeticiones), `https://freerepublic.com/tag/*/` (125) y `https://ismatimes.com/gttci-ethiopian-coffee-evening-farewell` (118 veces).

Las dos más repetidas (158 y 125 ocurrencias) corresponden a URLs genéricas sin contenido específico: al investigarlas muestran páginas de error sin noticia asociada o menús principales. Se descartan también para que no distorsionen el recuento de las métricas con eventos sin sentido.

## A.2 · Construcción del texto sintético

Para detectar contenido equivalente y para los pasos posteriores de representaciones vectoriales y LDA (Latent Dirichlet Allocation), se construyó por evento un texto sintético a partir de tres fuentes complementarias:

1. **Texto identificador de la URL.** En muchas cabeceras actuales el titular va embebido en la URL (`/news/elon-musk-jets-off-to-china`, `/politics/israel-lebanon-ceasefire-extended`). Se extraen los tokens de la ruta y se descartan los de longitud inferior a tres caracteres, los que contienen dígitos (típicos de identificadores), los hexadecimales (UUIDs) y un conjunto cerrado de stopwords específicas de URLs (`news`, `article`, `html`, `index`, ...).
2. **Metadatos estructurados del propio evento.** `Actor1Name`, `Actor2Name` y `ActionGeo_FullName`, todos en minúsculas.
3. **Etiquetas textuales de la codificación CAMEO.** Descripción del `EventRootCode` (`appeal`, `protest`, `fight`, ...) y del `QuadClass` (`verbal cooperation`, `material conflict`, ...). Aportan el «qué tipo de evento» en lenguaje natural.

Tras aplicar el filtro que descarta las URLs cuyo slug contiene menos de tres tokens, se parte de 118.201 filas y se conservan 107.248 (90,7 %), descartándose 10.953 (9,3 %) por no disponer de texto suficiente para el análisis.

El texto sintético obtenido a partir de cada URL presenta una longitud media de 18 tokens (mediana de 18), con un mínimo de 7 y un máximo de 43. Se trata, por tanto, de fragmentos breves y homogéneos, adecuados para el procesamiento posterior.

A modo ilustrativo, dos filas tomadas al azar muestran cómo cada URL se reduce a una secuencia compacta de palabras clave que conserva los actores, la acción y el tipo de evento:

- Una noticia sobre la cancelación de un despliegue militar en Polonia se transforma en «your military army leaders hot seat over poland deployment cancellation european publication iran reject verbal conflict».
- Una noticia sobre la prórroga del alto el fuego entre Israel y Líbano queda como «israel lebanon ceasefire extended days israeli washington district of columbia united states reject verbal conflict».

En ambos casos, el texto resultante captura la esencia geopolítica del evento (actores implicados, naturaleza de la acción y clasificación del conflicto) en una representación reducida y normalizada.

El filtro descarta el 9,3 % de las filas (10.953), exactamente las que tenían URL genérica sin titular embebido. El texto resultante tiene una mediana de 18 tokens, suficiente para alimentar las representaciones vectoriales y para un LDA de baja resolución temática.

## A.3 · Agrupamiento semántico

El conteo por URL detecta la misma URL repetida, pero no captura el caso de mayor interés para este trabajo: un mismo evento cubierto por medios distintos, con URLs diferentes pero contenido equivalente. Para abordarlo se proyectan los textos sintéticos a un espacio vectorial denso y se agrupan los vectores cercanos por similitud coseno.

**Granularidad.** Se calcula una representación vectorial por URL única. Esta decisión se basa en que todas las filas asociadas a una misma URL comparten el slug, por lo que sus textos sintéticos son prácticamente idénticos. La reducción es de aproximadamente 107.248 filas a 22.572 URLs únicas.

**Modelo.** `sentence-transformers/all-MiniLM-L6-v2`.

**Algoritmo de agrupamiento.** Se construye un grafo dirigido de k-vecinos más próximos sobre las representaciones vectoriales (`k = 15`, métrica coseno). Se filtran las aristas cuya similitud coseno sea inferior a 0,80 y se calculan las componentes conexas del grafo resultante. Cada componente es un grupo de noticias relacionadas.

**Resultado.** Sobre el fichero analizado, los 22.572 puntos se agrupan en 19.423 grupos, de los cuales el 94,4 % son singletons (un único punto sin vecinos suficientemente próximos) y el 5,6 % son grupos de dos o más. El grupo más grande contiene 318 URLs. El tamaño medio de grupo es 1,16.

**Top 3 grupos por tamaño.**

1. **Grupo 130 (318 URLs):** `http://www.bgnes.com/politics/trump-warns-taiwan-not-to-move-toward-independence` — texto: *trump warns taiwan not move toward independence taiwan beijing, beijing, china threaten verbal conflict*.
2. **Grupo 143 (107 URLs):** `https://13wham.com/news/local/suspected-hantavirus-case-in-ontario-county-involves-...` — texto: *suspected hantavirus case ontario county involves geneva high school student*.
3. **Grupo 137 (93 URLs):** `http://www.heraldglobe.com/news/.../amid-spiralling-relations-cuban-government-meets-cia` — texto: *amid spiralling relations cuban government meets cia director ratcliffe havana*.

El umbral coseno de 0,80 elegido produce grupos de naturaleza temática más que de «misma noticia exacta». El mayor grupo, al examinarlo, agrupa noticias diplomáticas heterogéneas (advertencias EE.UU.-Taiwán, prórroga del alto el fuego Israel-Líbano, etc.) que comparten vocabulario y estructura (*threaten*, *verbal conflict*, nombres de países en tensión). Los grupos de tamaño intermedio (decenas de URLs), en cambio, sí corresponden a un único evento cubierto por muchos medios: el grupo de 85 URLs sobre el juicio a Harvey Weinstein o el de 107 URLs sobre el brote de hantavirus tras un crucero. Para una deduplicación estricta tipo «mismo artículo reescrito» habría que subir el umbral, aceptando que muchas reescrituras se quedan sin agrupar.

## A.4 · Validación sobre tres jornadas

Para comprobar la estabilidad del procedimiento se han seleccionado tres días diferentes y se han puesto a prueba las etapas anteriores. El porcentaje de descarte por filtro de slug, el factor de inflación y el porcentaje de singletons del agrupamiento varían dentro de márgenes de unas pocas décimas.

Aun así, el volumen resultante sigue siendo elevado para alimentar el grafo: sumando los tres días de ejemplo aparecen 288.925 filas y 51.294 grupos semánticos, lo cual son datos muy elevados. Este resultado es el que motiva la introducción de los dos filtros del pipeline definitivo (cobertura mediática y roster geopolítico) documentados en §4.1.

## A.5 · Tópicos LDA

Tras la limpieza y reducción del contenido, se aplicó un LDA sobre el corpus de textos. El objetivo era complementar los grupos y descubrir temas dentro de estos textos para poder agruparlos. Como no se trabaja con textos complejos sino con URLs, el LDA detecta patrones de palabras.

Los tópicos no representan temas argumentales, sino patrones de concurrencia de palabras, que pueden ser desde países, ciudades o eventos. La siguiente tabla recoge cinco tópicos resultantes junto con el número de documentos asignados a cada uno.

| ID | Documentos | Palabras representativas |
|---|---|---|
| 1 | 3.306 | israel general media bank chief west gaza lebanon british arab israeli emirates |
| 2 | 3.794 | india delhi new pradesh minist governor senate colorado federal global michigan ece |
| 3 | 2.003 | business university day cuba administration oklahoma singapore travel kansas arrest tax hawaii |
| 4 | 4.434 | states united columbia district washington government house illinois american spain home pennsylvania |
| 5 | 2.865 | france italy general nation philippines college death malaysia worker manila karnataka meeting |

Se asigna a cada noticia el tema de su documento representativo, lo que cuantifica la composición temática del corpus filtrado. Como se argumenta en §4.1, los tópicos obtenidos no encapsulan un significado geopolítico aprovechable como característica del modelo, y por eso el LDA no se incorpora al pipeline definitivo.
