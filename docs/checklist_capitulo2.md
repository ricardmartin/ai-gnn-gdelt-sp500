# Checklist de correcciones · Capítulo 2

Lista accionable de [revision_capitulo2.md](revision_capitulo2.md). Los identificadores coinciden: si algo no se entiende, el detalle completo con la frase literal está allí.

**Progreso:** 0 / 36

🔴 error de hecho · 🟠 alineación con caps. 4-6 · 🟡 mejora · ⚪ forma

---

## 1 · Bloque exprés (media hora, máximo impacto)

- [x] 🔴 **2.1.3-A** · Corregir «crecimiento exponencial de fuentes» en §2.1.3 (§5 fuera de alcance)
- [x] 🔴 **2.1.3-B** · Distinguir versiones 1.0 (diaria, desde 1979) y 2.0 (15 minutos, desde 2015) al presentar GDELT. Sin eso, §4.1 aterriza sin contexto
- [x] 🔴 **2.3-A** · «cuatro cuestiones» pero solo tres viñetas. Añadir la cuarta (integración target en grafo, ver §4.2.2) o cambiar a «tres». Además «Qué son los siguientes:» → «Que son los siguientes:»
- [x] 🔴 **2.2.1-A** · Autores de Plakandaras: texto dice «Gogas & Papadimitriou», §8 dice «Gupta, R., & Wong, W. K.». Unificar (probablemente la buena es la de §8)
- [x] 🔴 **2.2.1-B** · «Estos tres trabajos» pero solo se describen dos → «Estos dos trabajos» o «Los trabajos revisados»

---

## 2 · Apartado 2.1 — Contexto del problema

### 2.1.1 Predicción de mercados financieros

- [ ] 🟡 **2.1.1-A** · El enfoque mixto propuesto queda huérfano. Adelantar Niu et al. (2023) o Chen et al. (2023) como ejemplos de esa dirección
- [ ] 🟡 **2.1.1-B** · Cerrar el párrafo de eficiencia de mercado enlazando con la aproximación del trabajo (opera sobre eficiencia débil/semifuerte, no la niega)
- [ ] ⚪ **2.1.1-C** · Prefijos «SVM:», «LSTM:», «GRU:», «Transformers:», «TFT:», «Random Forest:» en §8 → quitar. *(ya en el checklist §8 del capítulo 4)*

### 2.1.2 Riesgo geopolítico

- [ ] ⚪ **2.1.2-A** · Falta el punto final del párrafo de las tres fases («podría anticipar dichas respuestas»)
- [ ] 🟡 **2.1.2-B** · Cerrar §2.1.2 diciendo qué canales cubre el grafo (incertidumbre, sentimiento, comercio internacional) y cuáles no (energía, flujos de capital)
- [ ] 🟡 **2.1.2-C** · Anclar la cita de Knight: los eventos GDELT operan sobre el eje incertidumbre, no el eje riesgo cuantificable
- [ ] 🟡 **2.1.2-D** · Justificar por qué no se usa GPR directamente (es escalar; el trabajo requiere estructura relacional)

### 2.1.3 Bases de datos de eventos geopolíticos

- [x] 🔴 **2.1.3-A** · *(en el bloque exprés)*
- [x] 🔴 **2.1.3-B** · *(en el bloque exprés)*
- [x] 🟡 **2.1.3-C** · Añadir cita formal `(Leetaru & Schrodt, 2013)` en el párrafo que los nombra
- [x] 🟡 **2.1.3-D** · Introducir **QuadClass** al final de la lista CAMEO. Sin esto, §4.2.4 aterriza sin apoyo
- [x] 🟡 **2.1.3-E** · Cuantificar la redundancia («cada evento se replica en media cinco veces por múltiples fuentes»). Enlaza con el embudo de §4.1
- [x] ⚪ **2.1.3-F** · «és la cobertura» → **es**
- [x] ⚪ **2.1.3-G** · Reescribir «Datos desde 1979, és la cobertura…» → «Cobertura temporal desde 1979, la más amplia entre las plataformas comparables»

### 2.1.4 Redes neuronales de grafos

- [ ] 🟡 **2.1.4-A** · Añadir párrafo final que introduzca las **Heterogeneous GNN** como extensión del message passing. Sin esto, §4.2.3 aterriza directamente con HGT/HeteroGAT sin apoyo
- [ ] 🟡 **2.1.4-B** · Añadir cita de Kipf & Welling (2017) o Scarselli et al. (2009) al describir el message passing
- [ ] 🟡 **2.1.4-C** · O se elimina la formalización `G = (V, E)` o se aprovecha para introducir la extensión heterogénea (que sí se usa en §4.2.3)

### 2.1.5 Síntesis

Sin hallazgos.

---

## 3 · Apartado 2.2 — Estado del arte

### 2.2.1 Machine learning aplicado al riesgo geopolítico

- [x] 🔴 **2.2.1-A** · *(en el bloque exprés)*
- [x] 🔴 **2.2.1-B** · *(en el bloque exprés)*
- [ ] ⚪ **2.2.1-C** · DOI de Niu: sobra la «l» final. *(ya en el checklist §6-bis del capítulo 4)*

### 2.2.2 GDELT como fuente de datos

- [x] 🟡 **2.2.2-A** · Marcar Fallahi (2017) como **tesis de máster** en el texto, no como «estudio»
- [ ] 🟡 **2.2.2-B** · Ampliar la comparación con Myers et al. (2025): mismo dato, distinto artefacto (base consultable por LLM vs estructura entrenable para predicción). Refuerza el gap de §2.3

### 2.2.3 GNN en predicción bursátil

- [ ] ⚪ **2.2.3-A** · Cuatro citas en el texto sin entrada en §8. Todas en §2.2.3:
  - Hogan et al. (2021) — *knowledge graphs*
  - Vrandečić & Krötzsch (2014) — WikiData
  - van den Oord et al. (2016) — convolución causal
  - Veličković et al. (2018) — GAT original (imprescindible por §4.2.3)
- [ ] 🟠 **2.2.3-B** · Marcar qué hereda el trabajo: variante de GAT sobre grafo dinámico (FSTGAT) + construcción diaria del grafo desde fuentes externas (Chen et al. 2023), sustituyendo noticias corporativas por eventos geopolíticos
- [ ] ⚪ **2.2.3-C** · Catalanismos y haber impersonal:
  - «habían demasiadas incertidumbres» → **había**
  - «sinó como agentes individuales» → **sino**
  - «peró ninguno de ellos» → **pero**
  - «són siempre del pasado» → **son**
- [ ] ⚪ **2.2.3-D** · Concordancia rota: «una representaciones vectoriales por empresa» → **una representación vectorial**
- [ ] 🟡 **2.2.3-E** · Cerrar el catálogo de tres métodos con la posición del trabajo: se aproxima al segundo (relaciones predefinidas) pero rehúye su rigidez con decay temporal (§4.2.1)

### 2.2.4 Grafos temporales y dinámicos

- [ ] 🟠 **2.2.4-A** · Reescribir el cierre. La decisión de §4.2.1 no es DTDG puro sino un **único grafo persistente con memoria decaimiento-refuerzo**. Añadir esta cuarta variante y remitir a §4.2.1
- [ ] 🟡 **2.2.4-B** · Añadir al menos una cita de TGNN: Rossi et al. (2020), Kazemi et al. (2020) o Xu et al. (2020)
- [ ] ⚪ **2.2.4-C** · «són» → **son**

---

## 4 · Apartado 2.3 — Conclusiones del capítulo

- [x] 🔴 **2.3-A** · *(en el bloque exprés)*
- [x] 🟠 **2.3-B** · Añadir el argumento de *late fusion* frente a Chen et al. (grafo y target no interactúan dentro del mismo modelo). Refuerza §4.2.2
- [x] 🟡 **2.3-C** · Subrayar que HATS es el precedente directo del target elegido (dirección del S&P 500). Coincide en target, difiere en arquitectura (empresas vs países como nodo)

---

## 5 · Pasadas globales que también tocan §2

Casi todo esto está consolidado en el checklist del capítulo 4 (§5 y §6-bis). Se recopilan aquí solo por ubicación in situ.

- [ ] ⚪ Concordancia «representación vectorial»: 1 ocurrencia en §2.2.3
- [ ] ⚪ Catalanismos: §2.1.3, §2.2.3 (×4), §2.2.4
- [ ] ⚪ Índice de acrónimos: añadir **SHAP** (§2.2.1), **DTDG**, **CTDG**, **TGNN** (§2.2.4)
- [ ] ⚪ Separador de millar y unificación «S&P 500» / «SP500»

---

## 6 · Incoherencias con otros capítulos

- [~] 🟠 **X-Cap2-1** · «Crecimiento exponencial de fuentes» — §2.1.3 corregido; §5 fuera de alcance
- [x] 🟠 **X-Cap2-2** · Cadencia GDELT sin distinguir versiones en §2.1.3 vs elección de 1.0 en §4.1. Ver 2.1.3-B

---

## 7 · Referencias huérfanas en §8

Entradas en §8 sin cita en el texto de §2 (verificar si se usan en otro capítulo antes de retirar):

- [x] ⚪ Leetaru & Schrodt (2013) — se nombra en §2.1.3 pero sin cita formal → añadir cita (=2.1.3-C)
- [ ] ⚪ Bao et al. (2025) — no detectada en §2. Verificar si se usa en otro capítulo o retirar

---

## 8 · Mediciones/comprobaciones pendientes

- [x] Verificar la referencia correcta de **Plakandaras** (Google Scholar): con Gupta & Wong (Algorithms, 2019) o con Gogas & Papadimitriou. La disponible en §8 apunta a la primera; hay que confirmar y unificar
- [ ] Buscar en el resto del documento el uso de **Bao et al. (2025)**: si no se usa, retirar de §8
