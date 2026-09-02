# Revisión del capítulo 2 de la memoria

**Fecha:** 2026-09-02
**Documento revisado:** `EntregaFINAL_TFM_Aguiló_Martín.docx`
**Contrastado contra:** capítulo 4 y §8 del propio documento, y el código del repositorio en HEAD para verificar coherencia con las decisiones ya tomadas.
**Alcance:** capítulo 2 completo (2.1.1–2.1.5, 2.2.1–2.2.4 y 2.3 Conclusiones).

## Cómo leer este documento

Cada hallazgo lleva identificador, severidad, **DÓNDE** está (apartado + frase literal) y **QUÉ** hay que poner.

| Severidad | Significado |
|---|---|
| 🔴 **ERROR** | La memoria afirma algo que los datos o la fuente no sostienen. |
| 🟠 **ALINEACIÓN** | Incoherencia con capítulos 4-6 o con el resto de §2. |
| 🟡 **MEJORA** | Hueco argumental, cita omitida o argumento reforzable. |
| ⚪ **FORMA** | Errata, formato, catalanismo, concordancia. |

**Recuento:** 5 errores · 4 alineaciones · 12 mejoras · 15 formas = **36 puntos**.

Este capítulo es de contexto y estado del arte, por lo que casi todo el peso son 🟡 y ⚪. Los pocos 🔴 son de hecho o cita cruzada. Los 🟠 nacen de la decisión de arquitectura de §4.2.1 (grafo persistente con decay), que §2.2.4 aún describe como decisión abierta entre DTDG y CTDG.

## Ya corregido desde la versión anterior

Para no volver sobre ello: `Fama(1907)` → `Fama(1970)`, «tres aspectos» → «dos» en §2.1, el párrafo introductorio de §2.1 y la mención a Hawkes (1971) trasladada al capítulo 4. Todo esto está anotado en `revision_capitulo4.md` y no se repite aquí.

---

# 1. Apartado 2.1 — Contexto del problema

## 2.1.1 Predicción de mercados financieros

Sección sólida en su estructura (no linealidad → volatilidad → interacción de variables → Fama → clásicos → ML → DL → transformers). Los problemas son de cita y forma, no de contenido.

### 🟡 2.1.1-A · El enfoque mixto propuesto no cita ningún precedente

**DÓNDE:** «Es en estos enfoques mixtos donde se fundamenta nuestro proyecto, añadiendo una capa de geopolítica a la capa financiera estándar.»

**QUÉ PASA:** el párrafo cierra la sección apuntando al eje del trabajo, pero sin un solo trabajo previo que use un enfoque mixto financiero + no-financiero. La transición hacia §2.1.2 queda huérfana.

**QUÉ HACER:** una frase que anticipe el enfoque de Niu et al. (2023) o de Chen et al. (2023) como ejemplos de esa dirección, con la promesa de desarrollarlos en §2.2. No requiere párrafo nuevo: basta con nombrarlos.

### 🟡 2.1.1-B · La hipótesis del mercado eficiente merece una frase de cierre

**DÓNDE:** «Es precisamente en ese retardo entre la aparición de la información y su plena incorporación al precio donde los modelos predictivos buscan operar.»

**QUÉ PASA:** la frase es correcta y encaja con el trabajo (predecir con retardo geopolítico), pero se queda sin conectar con lo que sigue. Un lector benévolo lo enlaza solo; uno riguroso ve un salto brusco al análisis fundamental/técnico.

**QUÉ HACER:** una línea que declare explícitamente que la aproximación del trabajo se apoya en esa forma débil/semifuerte de eficiencia, no la niega.

### ⚪ 2.1.1-C · Bibliografía §8 con prefijos («SVM:», «LSTM:»…)

Ya está en el checklist del capítulo 4 (§8, bloque «formato»). Se cita aquí porque afecta a todas las referencias que aparecen en §2.1.1.

## 2.1.2 Riesgo geopolítico

### ⚪ 2.1.2-A · Falta el punto final del párrafo

**DÓNDE:** «podría anticipar dichas respuestas» (final de la viñeta que describe las tres fases).

**QUÉ HACER:** añadir el punto. La misma errata aparece en §4.1-F.

### 🟡 2.1.2-B · Los canales de transmisión se listan sin jerarquizar

**DÓNDE:** «existencia de ciertos canales principales… La incertidumbre, los precios de la energía y materias primas, el comercio internacional, los flujos de capital y el sentimiento inversor entre otros».

**QUÉ PASA:** cinco canales enumerados en una línea, cada uno con un párrafo propio después. En la enumeración inicial queda demasiado seco. Y el trabajo, en la práctica, no distingue canales al construir el grafo: los eventos entran indiferenciados por QuadClass. Nombrar los canales sin decir cuáles son los que la arquitectura pretende capturar deja al lector sin puntero.

**QUÉ HACER:** dos frases más al final del apartado que digan qué canales quedan cubiertos por la señal GDELT (incertidumbre, sentimiento inversor, comercio internacional vía eventos económicos) y cuáles no (precios de energía y flujos de capital, salvo por reflejo indirecto). Refuerza §4.2.4.

### 🟡 2.1.2-C · La cita de Knight es correcta pero está aislada

**DÓNDE:** «Según Frank H. Knight (1921), la incertidumbre es aquella situación en la que…»

**QUÉ PASA:** Knight aparece una única vez y no se vuelve a nombrar. La cita cumple con lo que se le pide, pero conviene indicar que la distinción riesgo/incertidumbre importa al trabajo porque los eventos GDELT operan sobre el eje incertidumbre, no el eje riesgo cuantificable.

**QUÉ HACER:** una frase de anclaje: la señal GDELT no ofrece probabilidades condicionales al estilo Knight-riesgo, sino patrones de intensidad de eventos.

### 🟡 2.1.2-D · GPR se describe pero no se compara con el trabajo

**DÓNDE:** «El índice GPR (Geopolitical Risk)… los picos de este índice coinciden con eventos geopolíticos conocidos desde la guerra del golfo hasta la guerra de Rusia y Ucrania.»

**QUÉ PASA:** al lector le queda la duda de por qué no se usa GPR directamente y sí GDELT. La respuesta implícita es «porque GPR es escalar y no admite topología de grafo», pero no se dice.

**QUÉ HACER:** una línea que diga que GPR es un índice unidimensional y que el enfoque de este trabajo requiere señales relacionales (par de actores, tipo de interacción), imposibles de derivar de GPR.

## 2.1.3 Bases de datos de eventos geopolíticos

Es la sección más comprometida del apartado 2.1, porque contiene una afirmación que los propios datos del trabajo contradicen.

### 🔴 2.1.3-A · «Crecimiento exponencial de fuentes» contradice el dataset propio

**DÓNDE:** «el crecimiento exponencial de fuentes se debe a la inclusión de webs y otras fuentes contemporáneas, lo que crea una situación en la que en la actualidad se registran más eventos que en el pasado al haber más fuentes disponibles».

**QUÉ PASA:** los eventos por año del propio dataset del trabajo **caen** desde 2016. El máximo son 2.927.300 eventos en 2016; 2025 baja a 1.396.372. Es el mismo hallazgo que aparece como **X-2** en `revision_capitulo4.md`, y afecta también a §5 del capítulo 5.

**QUÉ HACER:** corregir la afirmación en los dos sitios. Es un rasgo de la fuente (GDELT 1.0 dejó de ampliar cobertura cuando 2.0 tomó el relevo en 2015), no del trabajo, y decirlo así convierte una contradicción en una limitación documentada. Considerar meter el gráfico de eventos por año en §4.1 y remitir a él desde §2.1.3.

### 🔴 2.1.3-B · GDELT 15 minutos aquí, GDELT diario en §4.1

**DÓNDE:** «actualmente se actualiza cada 15 minutos», sin distinguir versión.

**QUÉ PASA:** los 15 minutos son **GDELT 2.0**. GDELT 1.0, que es la versión que se usa en el trabajo, es **diaria**. La sección presenta GDELT como un todo, y el lector no sabe que la cadencia intradía no es aprovechable con la versión elegida. Cuando llega a §4.1 y ve la elección de 1.0, no tiene el contexto para entender por qué la cadencia de 15 minutos que se destacó como ventaja aquí no se aprovechó.

**QUÉ HACER:** distinguir versiones. Una frase que diga «GDELT publica dos versiones: 1.0 (cadencia diaria, cobertura desde 1979) y 2.0 (cadencia de 15 minutos, cobertura desde 2015)», y luego, al enumerar las características, atribuir cada rasgo a su versión. Así §4.1 aterriza sin sorpresa.

### 🟡 2.1.3-C · Leetaru & Schrodt (2013) está en §8 pero no se cita

**DÓNDE:** «GDELT (Global Database of Events, Language, and Tone) es una base de datos abierta y gratuita creada por Kalev Leetaru y Philip Schrodt».

**QUÉ PASA:** nombra a los autores pero no cita el paper de presentación de GDELT, que sí está en la bibliografía. Es una cita huérfana en §8.

**QUÉ HACER:** añadir la cita en el texto: «(Leetaru & Schrodt, 2013)».

### 🟡 2.1.3-D · CAMEO se nombra pero QuadClass no

**DÓNDE:** «El sistema de codificación usado es CAMEO (Gerner et al., 2002)… EventRootCode / EventBaseCode / EventCode».

**QUÉ PASA:** en §4.2.4 la granularidad de aristas se resuelve en QuadClass, no en EventRootCode. QuadClass no aparece en §2.1.3 en ningún momento, y sin embargo es el eje sobre el que se hace la decisión más original del trabajo (tabla de decay por QuadClass en §4.2.1).

**QUÉ HACER:** añadir una línea al final de la lista CAMEO: «Además, CAMEO agrupa los eventos en cuatro categorías de alto nivel (QuadClass): cooperación verbal, cooperación material, conflicto verbal, conflicto material. Este agrupamiento se emplea en §4.2.4.» Con esa frase, el capítulo 4 puede aterrizar sin explicar QuadClass desde cero.

### 🟡 2.1.3-E · Redundancia en GDELT se enuncia pero no se cuantifica

**DÓNDE:** «también existe una cierta redundancia en los eventos que ocurren ya que cuanto más importante sea, más medios hablan de él».

**QUÉ PASA:** la afirmación es correcta y el trabajo la explota (usa `NumMentions ≥ 5` como filtro en §4.1). Aquí queda en abstracto. Un lector que llegue a §4.1 no tiene forma de saber cuánta redundancia hay antes de leer el 53,5 % del embudo.

**QUÉ HACER:** una frase que anticipe el orden de magnitud: «en la práctica, cada evento se replica en media cinco veces por múltiples fuentes» (dato del propio §4.1). Enlaza los dos apartados y da al lector una intuición numérica desde el marco teórico.

### ⚪ 2.1.3-F · Catalanismo

«és la cobertura temporal más amplia» → «es».

### ⚪ 2.1.3-G · Coma innecesaria en «Datos desde 1979, és la cobertura…»

Además de la «és», la coma une dos oraciones sin nexo. Reescribir como «Cobertura temporal desde 1979, la más amplia entre las plataformas comparables».

## 2.1.4 Redes neuronales de grafos

### 🟡 2.1.4-A · Salto brusco entre grafo homogéneo y grafo del trabajo

**DÓNDE:** «al final del proceso, la representación de cada nodo incorpora no solo sus propios atributos sino también la información de su entorno relacional…»

**QUÉ PASA:** la explicación termina en el caso homogéneo. El grafo del trabajo es **heterogéneo** (dos tipos de nodo, tres tipos de relación). La sección no menciona ni una vez el concepto de grafo heterogéneo, y §4.2.3 aterriza directamente con HGT/HeteroGAT como si el lector ya supiera qué son las HGNN.

**QUÉ HACER:** un párrafo breve (cuatro o cinco líneas) al final de §2.1.4 que introduzca las Heterogeneous GNN como extensión del message passing cuando hay más de un tipo de nodo o de arista. Basta con nombrar la idea; la justificación técnica pertenece a §4.2.3.

### 🟡 2.1.4-B · Falta la cita de Kipf & Welling para GCN

**DÓNDE:** el apartado describe el mecanismo de message passing sin citar el paper fundacional.

**QUÉ HACER:** añadir Kipf & Welling (2017) o Scarselli et al. (2009) como referencia del origen del message passing. No es imprescindible pero refuerza la sección y encaja con el nivel de citación del resto.

### 🟡 2.1.4-C · La formalización G = (V, E) no vuelve a usarse

**DÓNDE:** «Un grafo se define formalmente como G = (V, E), donde V es un conjunto de vértices y E un conjunto de aristas (Wilson, 1996)».

**QUÉ PASA:** se introduce la notación matemática y no se vuelve a mencionar. El capítulo 4 tampoco la usa. Es un adorno.

**QUÉ HACER:** o se elimina, o se aprovecha para introducir la extensión heterogénea (V dividido por tipos, E dividido por relaciones), que es lo que sí se usa en §4.2.3.

## 2.1.5 Síntesis

Sección breve y correcta. Sin hallazgos.

---

# 2. Apartado 2.2 — Estado del arte

## 2.2.1 Machine learning aplicado al riesgo geopolítico

### 🔴 2.2.1-A · Autores de Plakandaras: mismatch texto vs §8

**DÓNDE:** el texto cita «Plakandaras, Gogas & Papadimitriou (2019)». §8 tiene «Plakandaras, V., Gupta, R., & Wong, W. K.». Es el mismo hallazgo del checklist de capítulo 4 (§6-bis: bibliografía).

**QUÉ HACER:** verificar cuál es correcta y unificar. Si la buena es la de §8 (que es la que da la revisión), corregir las dos menciones en el texto de §2.2.1 y también §2.3.

### 🔴 2.2.1-B · «Estos tres trabajos» cuando solo se describen dos

**DÓNDE:** «Estos tres trabajos confirman que el riesgo geopolítico tiene capacidad predictiva sobre los mercados financieros».

**QUÉ PASA:** el apartado describe **dos** trabajos (Niu et al. 2023 y Plakandaras et al. 2019). Que la frase de cierre hable de tres es una errata de cardinalidad, y la clase de detalle que un tribunal cuenta con los dedos.

**QUÉ HACER:** «Estos dos trabajos» o, si se quiere incluir la referencia implícita a Caldara e Iacoviello (2022) del apartado 2.1.2, «Los trabajos revisados» y dejar el cardinal sin fijar.

### ⚪ 2.2.1-C · DOI de Niu con «l» sobrante

Ya en el checklist del capítulo 4 (§6-bis).

## 2.2.2 GDELT como fuente de datos para predicción financiera

### 🟡 2.2.2-A · Fallahi (2017) es una tesis de máster, conviene decirlo

**DÓNDE:** «Estudios como el de Fallahi (2017)».

**QUÉ PASA:** en §8 sí figura como «[Tesis de máster, Southern Illinois University Carbondale]», pero el texto la enuncia como «estudio», elevando su peso frente a las otras publicaciones revisadas por pares.

**QUÉ HACER:** decir en el texto que se trata de una tesis de máster. Sigue siendo una referencia legítima pero honesta.

### 🟡 2.2.2-B · La cita a Myers et al. (2025) es la más cercana al trabajo y merece más peso

**DÓNDE:** «La investigación más reciente es la de Myers et al. (2025)… aunque a veces devuelve resúmenes que carecen de consistencia.»

**QUÉ PASA:** Myers construye knowledge graphs sobre GDELT, exactamente lo que hace este trabajo aunque con distinto uso final. La sección apenas dedica cinco líneas y remata con una crítica menor.

**QUÉ HACER:** ampliar la comparación explícita: Myers usa GDELT como base de conocimiento consultable por LLM; este trabajo usa GDELT como estructura relacional entrenable para predicción cuantitativa. Ambas son transformaciones del mismo dato en distintos artefactos. Formulado así, sostiene mejor el gap del apartado 2.3.

## 2.2.3 GNN en predicción bursátil

Es el apartado más denso del capítulo y también el que más pierde por citas rotas.

### ⚪ 2.2.3-A · Cuatro citas en el texto sin entrada en §8

Todas están en este apartado y ya aparecen en el checklist del capítulo 4 (§6-bis). Se recopilan aquí en su ubicación exacta:

- **Hogan et al. (2021)** — para los *knowledge graphs* (párrafo del método basado en KG).
- **Vrandečić & Krötzsch (2014)** — para WikiData (mismo párrafo).
- **van den Oord et al. (2016)** — para la convolución causal (párrafo de FSTGAT).
- **Veličković et al. (2018)** — para el GAT original (párrafo de FSTGAT), imprescindible además por §4.2.3 (contraposición con GATv2).

Sin estas cuatro entradas, este apartado tiene cuatro citas huérfanas en once párrafos.

### 🟠 2.2.3-B · La descripción de FSTGAT no marca lo que hereda el trabajo

**DÓNDE:** «FSTGAT propuso… una versión mejorada del GAT (Veličković et al., 2018), que incorpora más información sobre el mercado y permite que haya modificaciones en las aristas ya implementadas.»

**QUÉ PASA:** el trabajo también usa una versión mejorada del GAT (GATv2, Brody et al. 2022, ver §4.2.3). Pero el apartado no marca que la elección de arquitectura hereda directamente de esta línea. El estado del arte queda como catálogo de trabajos sin apropiar ninguno.

**QUÉ HACER:** una línea al final del párrafo o al final del apartado: «Este trabajo hereda de FSTGAT el uso de una variante de GAT sobre grafo dinámico y de Chen et al. (2023) la construcción diaria del grafo a partir de fuentes externas, sustituyendo noticias corporativas por eventos geopolíticos de GDELT». Cierra la sección y prepara §2.3.

### ⚪ 2.2.3-C · Catalanismos y haber impersonal

En este apartado, en cadena:

- «habían demasiadas incertidumbres» → **había** (haber impersonal en singular).
- «sinó como agentes individuales» → **sino**.
- «peró ninguno de ellos» → **pero**.
- «son siempre del pasado» actualmente escrito «són» → **son**.

Ya recogidos en la pasada global del capítulo 4 (§5), pero conviene arreglarlos in situ para no acumular sobre §2.

### ⚪ 2.2.3-D · Concordancia «representación vectorial»

Ocho apariciones en el capítulo con la concordancia rota por un buscar-y-reemplazar de *embedding*. En §2.2.3: «un GNN procesa ese grafo para generar una representaciones vectoriales por empresa» → **una representación vectorial**. Ya en el checklist del capítulo 4 (§5).

### 🟡 2.2.3-E · Los tres métodos de construcción se listan sin decir por dónde va el trabajo

**DÓNDE:** al final del párrafo del grafo automático: «Esto puede generar predicciones erróneas a la larga.»

**QUÉ PASA:** el apartado enumera tres métodos (correlación histórica, knowledge graphs y grafo automático) con virtudes y defectos, pero no cierra con la posición del trabajo. Un tribunal pregunta «¿cuál de los tres tomáis vosotros?».

**QUÉ HACER:** cerrar con una línea: «El grafo de este trabajo se aproxima al segundo método (relaciones predefinidas entre entidades del mundo real), pero rehúye su rigidez introduciendo temporalidad vía decay (§4.2.1)». Enlaza directamente con la decisión ya tomada.

## 2.2.4 Grafos temporales y dinámicos

### 🟠 2.2.4-A · La sección presenta tres familias como abiertas, cuando §4.2.1 ya cerró la decisión

**DÓNDE:** «En la predicción diaria quizás es más adecuado utilizar grafos dinámicos discretos basados en momentos temporales.»

**QUÉ PASA:** «quizás es más adecuado» deja abierta una decisión que el capítulo 4 ya cerró, y ni siquiera en los términos del párrafo. La elección de §4.2.1 no es DTDG puro (un grafo nuevo cada día): es **un único grafo persistente cuyas aristas se refuerzan y decaen exponencialmente**. Esto no encaja exactamente en ninguna de las tres familias tal como las describe el apartado.

**QUÉ HACER:** reescribir el cierre del apartado para introducir la cuarta opción que efectivamente adopta el trabajo. Puede ser una frase: «Existe además una variante intermedia menos formalizada en la literatura, en la que se mantiene un único grafo persistente con memoria decaimiento-refuerzo, y es la que este trabajo adopta (§4.2.1).» Sin ese puente, el capítulo 4 aterriza sin apoyo teórico previo.

### 🟡 2.2.4-B · Sin citas concretas

**DÓNDE:** el apartado explica DTDG, CTDG y estáticos sin citar ningún trabajo de referencia.

**QUÉ HACER:** al menos una cita general de TGNN. Rossi et al. (2020) para TGN, Kazemi et al. (2020) para la revisión canónica, o Xu et al. (2020) para JODIE. Cualquiera de las tres da respaldo bibliográfico a lo que ahora mismo son afirmaciones sin fuente.

### ⚪ 2.2.4-C · Catalanismo

«los datos són siempre del pasado» → «son». Ya recogido en 2.2.3-C.

## 2.3 Conclusiones del capítulo

### 🔴 2.3-A · «Cuatro cuestiones» y solo hay tres viñetas

**DÓNDE:** «De la revisión de estas tres líneas, emergen cuatro cuestiones que no se han resuelto de forma simultánea. Qué son los siguientes:» seguido de tres viñetas.

**QUÉ PASA:** o falta una cuarta viñeta, o la cifra es incorrecta. Es un error de cardinalidad como el de 2.2.1-B pero más visible porque va al cierre del capítulo.

**QUÉ HACER:** revisar. La cuarta cuestión natural, dado el capítulo 4, es «Integración profunda del target financiero dentro del grafo (nodo mercado) frente a los enfoques de late fusion / concatenación posterior». Enlaza directamente con §4.2.2. Si se añade, además, se refuerza la posición del trabajo en el estado del arte.

Y la frase «Qué son los siguientes:» debería ser «Que son los siguientes:» sin acento.

### 🟠 2.3-B · La conclusión sobre Chen et al. (2023) es más suave que la del capítulo 4

**DÓNDE:** «se ha demostrado con HATS (2019), Chen et al. (2023) y FSTGAT (2025) que modelar el mercado como un grafo complejo permite la predicción de volatilidad, aunque se haya utilizado de forma muy centrada en un país, priorizando las relaciones entre las empresas en vez de los vínculos de los países.»

**QUÉ PASA:** el capítulo 4 (§4.2.2) argumenta contra Chen et al. porque su esquema GNN-LSTM equivale a *late fusion*. §2.3 solo apunta el limite de granularidad geográfica. Los dos argumentos son distintos y ambos son válidos, pero el que sostiene la decisión de arquitectura es el segundo (integración vs late fusion), y no aparece.

**QUÉ HACER:** añadir a la frase la limitación de *late fusion* (grafo y target no interactúan dentro del mismo modelo) como segundo gap. Refuerza §4.2.2.

### 🟡 2.3-C · La conclusión sobre HATS no menciona que se evalúa sobre el S&P 500

**DÓNDE:** «HATS trató el índice como un grafo completo y cada nodo era una empresa» (esto en §2.2.3, ya recogido) y luego en §2.3 se cita HATS sin detalle.

**QUÉ PASA:** HATS es el precedente directo de la elección de target (dirección del S&P 500). Merece que §2.3 lo recoja.

**QUÉ HACER:** una línea en la conclusión que subraye la coincidencia de target y el desacople de arquitectura (empresas como nodo vs países como nodo).

---

# 3. Pasadas globales que también tocan al capítulo 2

Todos estos están consolidados en el bloque §5-§6 del checklist del capítulo 4, y se recopilan aquí solo para que quien haga la pasada por §2 pueda encontrarlos in situ.

- **Concordancia** «representación vectorial»: §2.2.3 tiene una ocurrencia («generar una representaciones vectoriales»).
- **Catalanismos**: §2.1.3 («és»), §2.2.3 («habían», «sinó», «peró», «són»), §2.2.4 («són»).
- **Separador de millar**: revisar que todos los porcentajes usen coma («45,3 %») y todos los miles usen punto («1.594.822»).
- **«S&P500» / «S&P 500» / «SP500»**: unificar. §2.1.1 usa «S&P500», §2.2.1 «S&P500», §2.2.3 «S&P500». Consistente dentro de §2, pero conviene alinear con el capítulo 5 (que suele usar «SP500» sin espacio).
- **Índice de acrónimos**: añadir SHAP (aparece en §2.2.1), DTDG, CTDG y TGNN (aparecen en §2.2.4).

---

# 4. Cross-referencias con otros capítulos

## 🟠 X-Cap2-1 · «Crecimiento exponencial de fuentes» aparece en §2.1.3 y en §5

Ya descrito como **X-2** en `revision_capitulo4.md`. La afirmación se hace en dos capítulos y ambos hay que corregir en el mismo movimiento.

## 🟠 X-Cap2-2 · La granularidad temporal de GDELT se presenta en §2.1.3 sin distinguir versiones, y §4.1 elige 1.0

Ver 2.1.3-B. Es un problema de arquitectura del capítulo 2, no solo del capítulo 4.

---

# 5. Orden de trabajo recomendado

## Bloque 1 — Media hora, máximo impacto

1. **2.1.3-A** · Corregir «crecimiento exponencial» en §2.1.3 y en §5. Ambos en el mismo commit.
2. **2.1.3-B** · Distinguir versiones 1.0 y 2.0 al presentar GDELT, para que §4.1 aterrice con contexto.
3. **2.3-A** · Cuatro → tres, o añadir la cuarta viñeta (integración target en grafo).
4. **2.2.1-A** · Plakandaras: elegir la buena y corregir texto y §8 a la vez.
5. **2.2.1-B** · «tres trabajos» → «dos trabajos» (o reformular).

## Bloque 2 — Citas huérfanas

6. Cuatro entradas nuevas en §8: Hogan et al. (2021), Vrandečić & Krötzsch (2014), van den Oord et al. (2016), Veličković et al. (2018).
7. Cita explícita a Leetaru & Schrodt (2013) en §2.1.3.

## Bloque 3 — Alineación con capítulo 4

8. **2.1.3-D** · Introducir QuadClass en §2.1.3.
9. **2.1.4-A** · Introducir HGNN al final de §2.1.4.
10. **2.2.4-A** · Reescribir el cierre de §2.2.4 para introducir la opción «grafo persistente con decay».
11. **2.2.3-B** · Marcar qué hereda el trabajo de FSTGAT y de Chen et al.
12. **2.3-B** · Añadir el argumento de late fusion frente a Chen et al.

## Bloque 4 — Argumento y refuerzo

13. **2.1.1-A** y **2.1.1-B** · Cierres de párrafo.
14. **2.1.2-B**, **2.1.2-C**, **2.1.2-D** · Refuerzos sobre GPR, Knight y canales.
15. **2.2.2-B** · Ampliar la comparación con Myers et al.
16. **2.2.3-E** · Cerrar el catálogo de tres métodos con la posición del trabajo.

## Bloque 5 — Formas

17. Pasadas de catalanismos, concordancia, comas.
18. Índice de acrónimos: SHAP, DTDG, CTDG, TGNN.
19. Separador de millar y unificación S&P 500 / SP500.

---

# Anexo · Referencias detectadas en el texto de §2 sin entrada en §8

| Cita en texto | Apartado | Faltan datos en §8 |
|---|---|---|
| Hogan et al. (2021) | 2.2.3 | Sí, añadir |
| Vrandečić & Krötzsch (2014) | 2.2.3 | Sí, añadir |
| van den Oord et al. (2016) | 2.2.3 | Sí, añadir |
| Veličković et al. (2018) | 2.2.3 | Sí, añadir |

# Anexo · Referencias en §8 sin cita en el texto de §2

| Entrada en §8 | Se usa en §2 |
|---|---|
| Leetaru & Schrodt (2013) | No, aunque sí se nombra a los autores en §2.1.3. Añadir cita formal. |
| Bao et al. (2025) | No detectada. Verificar si se usa en otro capítulo, y si no, retirar. |
