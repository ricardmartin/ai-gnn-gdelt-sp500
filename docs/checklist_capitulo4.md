# Checklist de correcciones · Capítulo 4

Lista accionable de [revision_capitulo4.md](revision_capitulo4.md). El texto ya redactado está en [parches_cap4.md](parches_cap4.md). Los identificadores coinciden: si algo no se entiende, el detalle completo con la frase literal está allí.

**Quedan 17 tareas.** Las resueltas se han retirado; el historial está en git y el detalle de cada hallazgo en la revisión enlazada arriba.

🔴 error de hecho · 🟠 tiempo verbal · 🟡 mejora · ⚪ forma

> 📍 **Cómo se trabaja con este fichero, estado general y decisiones ya tomadas: [GUIA_REVISION_TFM.md](GUIA_REVISION_TFM.md).**

---

## 0 · Decisiones previas

Sin estas respuestas, tres puntos de abajo quedan en el aire.

- [ ] **P3** · Localizar de qué ejecución salen las cifras del capítulo 5 y guardar su `resultados.json`. Sin esto, cualquier cifra de §5 es irreproducible: hay que poder decir qué ejecución la generó. Mirar `resultados_local/` (subcarpetas `terciles`, `sigma05`, `produccion`, `hgnn_v2`) y los `.html` de los notebooks, que conservan la salida ejecutada

**Resueltas:** *P1* — el barrido de λ **no se hizo**: `LAMBDA_DECAY = 0.0693` es un valor único fijo en `config.py:133` que los notebooks solo leen, y el propio comentario del código lo admite («AJUSTAR: valores iniciales razonables; pueden explorarse experimentalmente»). Los únicos barridos existentes son de umbrales de etiquetado en nb03/nb04. → ver 4.2.1-I.
*P2* — se documenta lo que hay: tres baselines reales (naive, regresión logística, XGBoost) y el baseline sin geopolítica como línea futura, que es lo que ya declara OE4.

---

## 1 · Apartado 4.1 — Filtrado de datos

- [ ] 🔴 **§4.1 completo** · Reestructuración en 8 bloques + traslado al Anexo A. Todo el texto en [parches_cap4.md](parches_cap4.md). Absorbe 4.1-A, 4.1-B, 4.1-C, 4.1-D, 4.1-E, 4.1-F, 4.1-G y las erratas del apartado
  - Comprime la exploración de 6 páginas a 1 párrafo + tabla de balance; el detalle va al Anexo A (que estaba vacío)
  - **Añade el pipeline real paso a paso**, que no existía en el documento pese a titularse el apartado «Filtrado de datos»
  - **Añade las dos agregaciones** (aristas vs participación): decisión implementada en `preprocesar.py:171` y `:217` que la memoria no mencionaba y sin la cual el filtro OR queda sin justificar
  - Corrige un error de hecho: el filtro es sobre `NumMentions`, no sobre «medios distintos» (`NumSources`)
  - Rellena parte del **Anexo A**, que figura aparte como pendiente

---

## 2 · Apartado 4.2 — Decisiones técnicas

### 4.2.1 Modelado temporal

- [ ] ⚪ **4.2.1-G** · «Adicionalmente» → «Además», en el párrafo que introduce a Bacry et al. dentro de §4.2.1
- [ ] 🟡 **4.2.1-I** · Declarar que los valores de decay **no se optimizaron**. Se fijaron a priori por el razonamiento de las tres fases y nunca se barrieron (P1). El texto ya lo insinúa («se han fijado con anterioridad siguiendo el razonamiento…»); falta decirlo como limitación y remitirla a §7.2

> **Pendiente en el párrafo del decay:** partir en dos la frase de los sesenta días y devolver el acotador «En las categorías de decaimiento rápido», que sin él hace que el 2 % y el 19 % se contradigan. Más `memoría` → memoria, «con **más de** sesenta días», y el espacio antes del %.

### 4.2.3 Arquitectura del modelo

- [ ] ⚪ **4.2.3-E** · Citar **(Hu et al., 2020)** la primera vez que se nombra HGT. La entrada ya está en §8 desde el parche de §2.1.4; aquí HGT sigue apareciendo sin referencia

## 3 · Incoherencias entre capítulos

- [~] 🟡 **X-3** · Aclarar que la tabla de umbrales de §5.4 es análisis de sensibilidad, no selección de configuración (el valor usado es el 0,70 fijado a priori) — *fuera de alcance: capítulo 5 no se toca*

---

## 4 · Pasadas finales sobre todo el documento

- [ ] ⚪ **«representación vectoriales»** — concordancia rota por un buscar-y-reemplazar de *embedding*. En singular es «representación vectorial». Quedan **siete**: §4.2.2 (×4, una de ellas «enriquecidos» → enriquecidas), §4.2.4, §4.3.1 y §4.3.5 (×2). La de §2.2.3 ya está corregida
- [ ] ⚪ **Nombres de las clases**: §4.3.1 dice «subida, bajada o **neutro**» (adjetivo entre sustantivos); §4.3.5 y el capítulo 5 usan «neutralidad». Unificar
- [ ] ⚪ **Separador de millar** unificado: punto en todo el documento. Ahora conviven «118 201», «288.925» y «100000»
- [ ] ⚪ **Numerar tablas y figuras** de una sola pasada, en orden de lectura, y rehacer los dos índices (ahora solo listan Tabla 1 y Figura 1)
- [ ] ⚪ **Sustituir todos los «Tabla X» y «Figura X»** por su número definitivo
- [ ] ⚪ Rellenar **Resumen**, **Abstract**, **§1.2**, **§1.3**, **§7.1**, **§7.2** y el **Anexo A**

---

## 5 · Bibliografía (§8)

Ya no quedan citas huérfanas: las cuatro de §2.2.3 se resolvieron con el capítulo 2, junto con ocho entradas nuevas. Queda verificar identificadores y ordenar.

- [ ] ⚪ **Verificar identificadores** de las entradas añadidas o no comprobadas: Hawkes (1971), Bacry et al. (2015), Scarselli (2009), Kipf & Welling (2017), Hu et al. (2020), Veličković (2018), van den Oord (2016), Vrandečić & Krötzsch (2014), Hogan et al. (2021) y Kazemi et al. (2020)

**Formato:**

- [ ] ⚪ Ordenar toda la lista **alfabéticamente** por primer apellido (ahora va en orden de incorporación)

---

## 6 · Mediciones pendientes

- [ ] Distribución por **EventRootCode** sobre el dataset filtrado. §4.2.5 afirma que las 20 categorías de EventRootCode «fragmentarían el volumen hasta dejar sin masa apreciable a las de cola», pero no lo demuestra con cifras. Se calcula igual que la tabla de QuadClass: agrupar el dataset filtrado por EventRootCode y contar eventos y aristas
- [ ] Gráfico de **eventos por año**. Respalda visualmente el párrafo de §2.1.3 sobre el máximo de 2016 (≈2,9 M) y la caída a 1,4 M en 2025. Se obtiene contando filas por año sobre `data/raw/*.export.CSV`
- [ ] Gráfico de **top 10 pares origen-destino** (USA→USA es el 24 % del total). Es la validación cuantitativa del grafo que promete OE2, junto con la distribución de grados y la de QuadClass

---

*Método: cuando una tarea se resuelve se **borra** de esta lista, no se marca. Lo que aparece aquí es exactamente lo que queda por hacer. El historial vive en git.*
