# Checklist de correcciones · Capítulo 4

Lista accionable de [revision_capitulo4.md](revision_capitulo4.md). Los identificadores coinciden: si algo no se entiende, el detalle completo con la frase literal está allí.

**Progreso:** 13 / 71 · **4.2.1 y 4.2.3 cerrados** ✅

🔴 error de hecho · 🟠 tiempo verbal · 🟡 mejora · ⚪ forma

---

## 0 · Decisiones previas

Sin estas respuestas, tres puntos de abajo quedan en el aire.

- [ ] **P1** · ¿Se hizo el barrido de λ? De ello depende 4.3.3-B
- [ ] **P2** · ¿Se implementa algún baseline más? De ello dependen 4.3.6-E, 4.3.6-F y X-1
- [ ] **P3** · Localizar de qué ejecución salen las cifras del capítulo 5 y guardar su `resultados.json`

---

## 1 · Bloque exprés (media hora, máximo impacto)

- [ ] 🔴 Buscar y reemplazar **«HGT»** en todo el capítulo 4 → **GATv2**. Cuatro apariciones: 4.2.2, 4.2.4, 4.3.4 (×2)
- [ ] 🔴 **4.3.2-E** · Quitar el párrafo de las macro en el nodo Estados Unidos. No se hizo: todos los países llevan las mismas 11 features
- [ ] 🔴 **4.3.2-A** · Quitar la OPEP+ de 4.3.2 (ya la quitaste de 4.2.4)
- [ ] 🔴 **4.3.2-D** · «producto interior bruto mundial» → **peso de comercio bilateral con EE. UU.**

---

## 2 · Apartado 4.1 — Filtrado de datos

- [ ] 🔴 **4.1-A** · Reencuadrar URL / embeddings / clustering / LDA como **exploración descartada**. Frase de encuadre al principio + tabla «técnica evaluada / incorporada al pipeline final» (5 filas; solo `NumMentions ≥ 5` es un sí)
- [ ] 🔴 **4.1-B** · Añadir la tabla del **embudo real**: 1.029.338 → 550.331 (53,5 %) → 238.688 (23,2 %) → 238.688
- [ ] 🔴 **4.1-C** · Declarar que el corte horario es inerte, enmarcándolo como consecuencia coherente de elegir 1.0 (la cadencia diaria ya garantiza la separación temporal)
- [ ] 🟡 **4.1-D** · Retirar o reformular la viñeta de «más de 20 años»: el estudio es 2015-2025 y 2.0 cubre ese rango entero
- [ ] 🟡 **4.1-E** · Tabla de las **13 columnas** cargadas (ahora solo se nombran 5)
- [ ] 🟡 **4.1-F** · Justificar el «un único día de datos como muestra» + falta el punto final
- [ ] 🟡 **4.1-G** · Precisar el filtro de roster: **OR** sobre Actor1/Actor2, con el ejemplo CHN→SYR
- [ ] ⚪ «Puntuacioón» → Puntuación
- [ ] ⚪ «notícia» → noticia
- [ ] ⚪ «cuando llega al 2005 **són** anuales» → son · y falta el sujeto (GDELT empaqueta…)
- [ ] ⚪ «Latent **Drichlet** Allocation» → Dirichlet
- [ ] ⚪ «el **grupoing**» → el agrupamiento
- [ ] ⚪ «complementar el **gruposy** descubrir» → los grupos y descubrir
- [ ] ⚪ «para ver **cual** es el umbral» → cuál
- [ ] ⚪ «100000 a 300000» → 100.000 a 300.000
- [ ] ⚪ Figura de reducción: la barra dice «(§4.7)», apartado que no existe
- [ ] ⚪ Tabla LDA: cabecera «Document» → «Documentos»; «3,306» → 3.306

---

## 3 · Apartado 4.2 — Decisiones técnicas

### 4.2.1 Modelado temporal

- [x] 🔴 **4.2.1-A** · Rechazo de CTDG reescrito ✅ *(resuelto el 2026-09-02)*
- [x] 🔴 **4.2.1-B** · Subir la **tabla de decay por QuadClass**: multiplicadores 1,5 / 1,0 / 0,7 / 0,4 → vidas medias 6,7 / 10 / 14,3 / 25 días
- [x] 🔴 **4.2.1-C** · Citadas Hawkes (1971) y Bacry et al. (2015) en el texto, y las dos entradas en §8 ✅ *(queda verificar los DOI)*
- [x] 🟡 **4.2.1-D** · «precedente y validación» → «precedente», más la frase que precisa que el modelo no ajusta un proceso de Hawkes ✅
- [x] 🟡 **4.2.1-E** · Ventana de 60 días declarada, con el 2 % / 19 % ✅
- [x] 🟡 **4.2.1-F** · λ, vida media y ventana, en el texto y en la tabla ✅
- [x] ⚪ **4.2.1-G** · «Adicionalmente» → «Además» ✅

> **Pendiente en el párrafo del decay:** partir en dos la frase de los sesenta días y devolver el acotador «En las categorías de decaimiento rápido», que sin él hace que el 2 % y el 19 % se contradigan. Más `memoría` → memoria, «con **más de** sesenta días», y el espacio antes del %.

### 4.2.2 Integración del SP500

- [x] 🔴 **4.2.2-A** · «el mecanismo de atención del HGT» → GATv2 ✅
- [ ] 🔴 **4.2.2-B** · Declarar la **tercera relación** `market→country`. Es la que hace verdad el argumento de la interacción bidireccional
- [X] 🔴 **4.2.2-C** · **La interpretabilidad prometida no se entrega.** El apartado justifica la arquitectura con los coeficientes de atención y pone un ejemplo concreto («la atención hacia Rusia se dispara durante la invasión de Ucrania»), pero **nada del repositorio extrae pesos de atención**: no hay un solo `return_attention_weights` en `src/` ni en los notebooks, y el capítulo 5 no recoge ningún análisis de ese tipo. O se hace, o se rebaja a capacidad de la arquitectura y se manda a §7.2

### 4.2.3 Arquitectura del modelo

- [x] 🟠 **4.2.3-A** · Decisión cerrada: HeteroGAT con GATv2 ✅
- [x] 🔴 **4.2.3-B** · `to_hetero()` fuera; `HeteroConv` con un `GATv2Conv` por relación ✅
- [x] ⚪ **4.2.3-C** · Añadir **Brody, Alon & Yahav (2022)** a §8. Ya está citado en el texto, así que la entrada es obligatoria *(ver el bloque §8 al final)*
- [x] 🔴 **4.2.3-D** · **Contradicción entre los dos párrafos:** el primero dice que HGT y HeteroGAT «ambas incorporan atención específica por tipo de nodo y arista», y el segundo dice que HGT es más expresivo *precisamente* por aplicarla por tipo de nodo. Correcto es el segundo → quitar «por tipo de nodo y» en el primero

### 4.2.4 Diseño topológico

- [ ] 🔴 **4.2.4-A** · Los ejemplos «militar / comercial / diplomático / legislativo» **no son posibles con QuadClass**. Reescribirlos en el eje cooperación-conflicto / verbal-material (afecta también a 4.3.2)
- [ ] 🔴 **4.2.4-B** · Tercera aparición del HGT → GATv2
- [ ] 🟡 **4.2.4-C** · Declarar que los pesos de comercio bilateral son estimaciones propias, no una fuente citada
- [ ] ⚪ **4.2.4-D** · Maquetar la tabla de QuadClass: cabecera partida, «2.198.6 / 57» roto, falta la nota de redondeo y «Fuente: Elaboración propia»

### 4.2.5 Régimen de datos

- [ ] 🟠 **A** · «en torno a las dos mil» → **2.751 grafos**
- [ ] 🟠 **B** · «decena o cientos de miles de parámetros» → cifra real (contarla antes)
- [ ] 🟠 **C** · «entre 32 y 128» → **64**
- [ ] 🟠 **D** · «dos o tres capas» → **2**
- [ ] 🟠 **E** · «dropout entre 30 % y 50 %» → **0,3** · weight decay **1e-4** · paciencia **15** sobre **validación interna** (15 % final del train)
- [ ] 🟠 **F** · «entre tres y cinco semillas» → **3: (0, 1, 2)**
- [ ] 🟡 **G** · Conectar el régimen de datos con la elección de QuadClass: una operación de atención por tipo de arista, ×5 tipos = ×5 parámetros

---

## 4 · Apartado 4.3 — Arquitectura final

### 4.3.1 Visión general

- [X] ⚪ **4.3.1-A** · «El sistema con el grafo del día t, produce» → coma entre sujeto y verbo

### 4.3.2 Estructura del grafo

- [ ] 🔴 **4.3.2-A** · OPEP+ *(ya en el bloque exprés)*
- [ ] 🟠 **4.3.2-B** · «aproximadamente una veintena» y «no se cierran a nivel arquitectónico» → **20 cerrados**, con la lista
- [ ] 🟠 **4.3.2-C** · Cuarta vez que la granularidad «se determinará» → QuadClass, remitiendo a 4.2.4
- [ ] 🔴 **4.3.2-D** · PIB → comercio bilateral *(ya en el bloque exprés)*
- [ ] 🔴 **4.3.2-E** · Macro en el nodo USA *(ya en el bloque exprés)*
- [ ] 🔴 **4.3.2-F** · Declarar las **9 features** del nodo mercado y que **3 están inactivas** (DXY nunca se rellena; `USAR_MACRO = False`)
- [ ] 🟠 **4.3.2-G** · «cuya base será el comercio bilateral, posiblemente complementada» → 1 feature, sin complementar
- [ ] 🟡 **4.3.2-H** · Detallar las **7 features** de arista país-país (3 + one-hot QuadClass)
- [ ] ⚪ **4.3.2-I** · «En cuanto a **artistas**» → aristas

### 4.3.3 Evolución temporal

- [ ] 🟠 **4.3.3-A** · «se ajustarán durante la experimentación» → λ, multiplicadores y ventana
- [ ] 🟠 **4.3.3-B** · La promesa del barrido de λ → según **P1**, retirar o pasar a §7.2
- [ ] 🔴 **4.3.3-C** · «histórico de eventos acumulado» → **ventana de 60 días**

### 4.3.4 Modelo

- [ ] 🟠 **4.3.4-A** · «HGT o HeteroGAT… se reserva como ajuste empírico» → GATv2 vía HeteroConv
- [ ] 🟠 **4.3.4-B** · «dimensión moderada / dos o tres capas / cabezas a determinar» → **64 / 2 / 4 / dropout 0,3**
- [ ] 🔴 **4.3.4-C** · «dropout y **normalización**» → **no hay ninguna capa de normalización**
- [ ] 🟡 **4.3.4-D** · Añadir la **conexión residual** y la **cabeza MLP de 2 capas**

### 4.3.5 Cabeza de predicción

- [ ] 🟠 **4.3.5-A** · «se determinará… contemplándose opciones» → **terciles**, recalculados por fold sobre su train
- [ ] 🟠 **4.3.5-B** · «se contempla ponderar la pérdida» → no se ponderó (`usar_pesos_clase = False`)
- [ ] 🔴 **4.3.5-C** · «el procedimiento exacto de corte temporal se afinará» → ver **4.1-C**

### 4.3.6 Entrenamiento y evaluación

- [ ] 🟠 **4.3.6-A** · «se fijarán en función del periodo» → **10 folds**, expansiva, en muestras, 250 sesiones de validación
- [ ] 🟡 **4.3.6-B** · Declarar el **embargo 0**
- [ ] 🟠 **4.3.6-C** · «varias semillas» → 3
- [ ] 🟠 **4.3.6-D** · «se contempla evaluar desde una perspectiva financiera» → se hizo, está en §5.4
- [ ] 🔴 **4.3.6-E** · La **LSTM financiera** no existe
- [ ] 🔴 **4.3.6-F** · El **baseline geopolítico sin grafo** no existe

---

## 5 · Incoherencias entre capítulos

- [ ] 🔴 **X-1** · Alinear §4.3.6 con lo que ya admite el capítulo 6: enumerar los **tres** baselines construidos y dejar los otros dos como línea futura. Revisar también el **objetivo específico 4 del §3.2**, que exige superar un modelo sin información geopolítica
- [ ] 🟠 **X-2** · «Crecimiento exponencial de fuentes» en §2.1.3 y §5 contradice los datos: los eventos por año **caen** desde 2016. Considerar el gráfico de eventos por año en §4.1
- [ ] 🟡 **X-3** · Aclarar que la tabla de umbrales de §5.4 es análisis de sensibilidad, no selección de configuración (el valor usado es el 0,70 fijado a priori)

---

## 6 · Pasadas finales sobre todo el documento

- [ ] ⚪ **«representación vectoriales»** — concordancia rota por un buscar-y-reemplazar de *embedding*. En singular es «representación vectorial». Ocho apariciones: §2.2.3, §4.2.2 (×4, una de ellas «enriquecidos» → enriquecidas), §4.2.4, §4.3.1 y §4.3.5 (×2)
- [ ] ⚪ **Nombres de las clases**: §4.3.1 dice «subida, bajada o **neutro**» (adjetivo entre sustantivos); §4.3.5 y el capítulo 5 usan «neutralidad». Unificar
- [ ] ⚪ **Catalanismos**. Ctrl+F uno por uno: **sinó** → sino · **peró** → pero · **són** → son · **és** → es · **notícia** → noticia. Localizados en §2.1.3, §2.2.3, §2.2.4 y §4.1
- [ ] ⚪ **Haber impersonal en singular**: «habían demasiadas incertidumbres» → había · «han habido modificaciones» → ha habido (§2.2.3)
- [ ] ⚪ **Separador de millar** unificado: punto en todo el documento. Ahora conviven «118 201», «288.925» y «100000»
- [ ] ⚪ **período / periodo**: elegir uno. El capítulo 5 usa «periodo»
- [ ] ⚪ **Numerar tablas y figuras** de una sola pasada, en orden de lectura, y rehacer los dos índices (ahora solo listan Tabla 1 y Figura 1)
- [ ] ⚪ **Sustituir todos los «Tabla X» y «Figura X»** por su número definitivo
- [ ] ⚪ **DOI de Niu et al.**: sobra una «l» al final (`…irfa.2023.102545l`)
- [ ] ⚪ Rellenar **Resumen**, **Abstract**, **§1.2**, **§1.3**, **§7.1**, **§7.2** y el **Anexo A**

---

## 6 bis · Bibliografía (§8)

Repasada la lista contra las citas del texto. Todo esto es error de citación, que es lo que más rápido detecta un director.

**Citas en el texto sin entrada en §8** — las cuatro están en §2.2.3:

- [ ] ⚪ **Veličković et al. (2018)** — el GAT original. Hace falta también porque 4.2.3 lo contrapone a GATv2
- [ ] ⚪ **van den Oord et al. (2016)** — convolución causal
- [ ] ⚪ **Hogan et al. (2021)** — *knowledge graphs*
- [ ] ⚪ **Vrandečić & Krötzsch (2014)** — WikiData

**Entradas a añadir:**

- [ ] ⚪ **Brody, Alon & Yahav (2022)** *(= 4.2.3-C)*
  > Brody, S., Alon, U., & Yahav, E. (2022). How attentive are graph attention networks? En *International Conference on Learning Representations*. arXiv:2105.14491

**Errores en las que ya existen:**

- [ ] ⚪ **Plakandaras**: §2.2.1 y §2.3 citan «Gogas & Papadimitriou», pero §8 dice «Gupta, R., & Wong, W. K.». La correcta es la de §8 → corregir las dos menciones del texto
- [ ] ⚪ **DOI de Niu et al.**: sobra una «l» al final (`…irfa.2023.102545l`)
- [ ] ⚪ **Verificar los DOI** de Hawkes (1971) y Bacry et al. (2015)

**Formato:**

- [ ] ⚪ Ordenar toda la lista **alfabéticamente** por primer apellido (ahora va en orden de incorporación)
- [ ] ⚪ Quitar las etiquetas de las seis últimas entradas («SVM:», «Random Forest:», «LSTM:», «GRU:», «Transformers:», «TFT:»)

---

## 7 · Mediciones pendientes

- [ ] Contar los parámetros entrenables: `sum(p.numel() for p in modelo.parameters() if p.requires_grad)`
- [ ] Distribución por **EventRootCode** sobre el dataset filtrado, para rematar el argumento de 4.2.4
- [ ] Gráfico de **eventos por año** (para 4.1 y para resolver X-2)
- [ ] Gráfico de **top 10 pares origen-destino** (USA→USA es el 24 % del total)
