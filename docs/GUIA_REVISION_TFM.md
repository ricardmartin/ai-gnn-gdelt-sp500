# Guía de la revisión del TFM

Punto de entrada. Explica qué es cada fichero de `docs/`, cómo se trabaja con ellos y en qué estado está la memoria. Escrito para poder retomarse sin contexto previo.

**Última actualización:** 2026-09-03
**Documento revisado:** `docs/EntregaFINAL_TFM_Aguiló_Martín.docx (2).pdf`

---

## 1 · Los ficheros y para qué sirve cada uno

| Fichero | Qué es | ¿Se modifica? |
|---|---|---|
| `revision_capitulo2.md`<br>`revision_capitulo3.md`<br>`revision_capitulo4.md`<br>`revision_cruzada_cap2_3_4.md` | **Los informes originales.** Cada hallazgo con su identificador, la frase literal donde está y qué habría que poner. Son la fuente de verdad del diagnóstico. | **No.** Se consultan cuando un ítem del checklist no se entiende. |
| `checklist_capitulo2.md`<br>`checklist_capitulo3.md`<br>`checklist_capitulo4.md` | **Lo que queda por hacer.** Una línea por tarea, con el mismo identificador que la revisión. | **Sí.** Ver el método en §2. |
| `parches_cap2.md`<br>`parches_cap4.md` | **Texto ya redactado**, listo para copiar y pegar en el `.docx`. Cada parche dice qué buscar, qué borrar y qué escribir. | Se vacían a medida que se aplican. |
| `_entrega_v3.txt` | Volcado en texto plano del PDF, para poder buscar frases con `grep`. Se regenera con el script de §5. | Se regenera al sacar un PDF nuevo. |
| `GUIA_REVISION_TFM.md` | Este fichero. | Al cambiar el estado general. |

---

## 2 · El método de trabajo

**Las tareas resueltas se BORRAN del checklist, no se marcan `[x]`.** La lista debe contener exclusivamente lo pendiente. El historial de lo hecho está en git, así que marcar no aporta y estorba: con decenas de `[x]` acumulados cuesta ver lo que falta.

Al borrar una tarea:
1. Eliminar su línea y sus sub-viñetas.
2. Si su sección se queda vacía, eliminar también el encabezado.
3. Renumerar los encabezados para que no queden huecos.
4. Actualizar el contador de la cabecera.

**Verificar contra el PDF antes de borrar.** En la pasada del 2026-09-02 aparecieron dos ítems marcados como hechos que nunca se habían aplicado al documento (2.1.3-C y 2.1.3-E). Marcar sin comprobar es peor que no marcar.

**Verificar contra el código y los datos antes de escribir una cifra.** Ver §4.

---

## 3 · Estado a 2026-09-03

| Capítulo | Tareas | Estado |
|---|---|---|
| **2 · Contexto y estado del arte** | 4 | ✅ **Contenido cerrado.** No queda ningún hallazgo propio de §2.1, §2.2 ni §2.3. Las 4 líneas restantes son pasadas de forma sobre todo el documento |
| **3 · Objetivos y metodología** | 16 | ⚠️ Tiene el **pendiente más grave del documento**. Ver abajo |
| **4 · Descripción del experimento** | 17 | 🔧 En curso. §4.1 tiene texto redactado; §4.2 y §4.3 casi cerrados |

### Lo más urgente, en orden

**1. §3.2 se contradice consigo mismo en la misma página.** Conviven las cuatro viñetas antiguas de objetivos específicos y los nuevos OE1-OE6, uno detrás de otro. Las viejas prometen «periodos geopolíticamente relevantes», «revisión manual», «señal antes de la apertura» y «superar a un modelo sin información geopolítica» — exactamente las cuatro cosas que OE1-OE6 corrigen. El texto nuevo se pegó y el viejo no se borró. **Es borrar cuatro líneas** y es lo primero que hay que hacer.

**2. §4.1 completo.** Reestructuración en 8 bloques, con todo el texto ya escrito en `parches_cap4.md`. Es el trabajo más largo que queda.

**3. Metodología del capítulo 3** (3.M1-A a 3.M5-A). Las cinco fases describen un trabajo distinto del ejecutado, igual que les pasaba a los OE antiguos.

---

## 4 · Principios de verificación

Tres reglas que han evitado meter errores en la memoria durante esta revisión:

**No dar por buena una cifra de la revisión sin reproducirla.** `revision_capitulo2.md` proponía escribir que «cada evento se replica en media cinco veces». Medido sobre `data/raw`, la media real de `NumMentions` es **13,1** y la mediana **4**. El «cinco» procedía de otra cosa: del cociente filas/URL de §4.1 (118.201 / 24.412 = 4,8), que mide algo distinto.

**No describir el sistema sin abrir el código.** §4.1 afirmaba que el filtro conserva noticias «que aparezcan en X medios distintos». El filtro implementado opera sobre `NumMentions` (menciones), no sobre `NumSources` (medios). Y el apartado entero describía técnicas —URL, embeddings, clustering, LDA— que no están en `src/datos/preprocesar.py`.

**Declarar siempre el alcance de una medición.** El embudo de filtrado se calcula sobre una muestra de días, no sobre el dataset completo. Presentarlo sin decirlo sería incorrecto.

### Comandos útiles

```bash
# Regenerar el volcado de texto tras exportar un PDF nuevo
python -c "import fitz; d=fitz.open('docs/EntregaFINAL_TFM_Aguiló_Martín.docx (2).pdf'); open('docs/_entrega_v3.txt','w',encoding='utf-8').write('\n'.join(p.get_text() for p in d))"

# Buscar una frase en el documento (las frases parten líneas: usar tr)
grep -n "frase" docs/_entrega_v3.txt
tr '\n' ' ' < docs/_entrega_v3.txt | grep -o "frase que parte .\{0,40\}"

# Hitos reales para el cronograma
git log --pretty=format:"%ad %s" --date=short --reverse
```

---

## 5 · Decisiones tomadas en esta revisión

Quedan aquí porque no son obvias al leer el documento y condicionan lo que falta.

### Reparto entre capítulos

**El estado del arte cataloga y señala el hueco; el capítulo 4 decide.** Se detectó que §2.2.4 y §4.2.1 contaban lo mismo dos veces, y que §2.2.4 además recomendaba DTDG, que es justo lo que §4.2.1 descarta. Se repartió: §2.2.4 describe las dos familias TGNN y termina enunciando lo que les falta; §4.2.1 remite a §2.2.4 y argumenta la decisión. **Aplicar este criterio a cualquier solapamiento que aparezca.**

### La formulación propia no es una familia del campo

§4.2.1 decía que existen «tres familias principales» de TGNN y que la tercera es el grafo persistente con decay. **Es incorrecto:** la taxonomía habitual distingue dos (DTDG y CTDG), y el grafo persistente con refuerzo y decaimiento **es la formulación propia de este trabajo**. Se corrigió a «La solución adoptada no pertenece a ninguna de las dos familias anteriores». Esto refuerza el trabajo: convierte una elección de menú en una aportación.

### La exploración de §4.1 se comprime, no se borra

Se planteó eliminar las seis páginas de URL, embeddings, clustering y LDA por no estar en el pipeline. **No se borra**, por dos frases del propio documento: OE6 promete documentar «las decisiones metodológicas **y sus alternativas descartadas**», y §4.3 abre diciendo «Tras justificar en el apartado anterior las decisiones técnicas **y las alternativas descartadas**». Borrarlas convertiría un fallo de encuadre en un objetivo incumplido. Se comprimen a un párrafo más una tabla de balance, y el detalle se traslada al **Anexo A**, que está vacío.

### Decay sin optimizar (P1, resuelta)

**El barrido de λ no se hizo.** `LAMBDA_DECAY = 0.0693` es un valor único fijo en `config.py:133` que los notebooks solo leen; el comentario del propio código lo admite («AJUSTAR: valores iniciales razonables; pueden explorarse experimentalmente»). Los únicos barridos existentes son de umbrales de etiquetado en nb03/nb04. Hay que declararlo como limitación (ítem 4.2.1-I).

### Baselines (P2, resuelta)

Se documenta lo que hay: tres baselines reales (naive de clase mayoritaria, regresión logística, XGBoost). El baseline sin información geopolítica **no se construyó** y queda como línea futura, que es lo que ya declara OE4.

### No existe predicción en vivo (verificada)

No hay script ni notebook que, dado un día, produzca la predicción del siguiente. OE3 hace bien en hablar de flujo reproducible offline; **no reintroducir la promesa de «señal antes de la apertura»** en la metodología del capítulo 3.

---

## 6 · Cronograma a partir del historial real

Para 3.CRON-A. El repositorio cubre de junio a septiembre de 2026; las fases de diseño previas hay que fecharlas por otra vía (la primera entrega es de mayo de 2026 y `acta_decisiones_tfm.md` del 20 de mayo).

| Periodo | Hitos según el historial |
|---|---|
| Mayo 2026 | Primera entrega. Acta de decisiones del proyecto |
| 17-20 jun | Estructura del repositorio, primeros datos, primer entrenamiento en Colab |
| 20-24 jun | Matriz de confusión, métricas, corrección del filtro AND→OR, fugas de memoria, procesamiento por tramos, corrección del uso de folds |
| 30 jun - 2 jul | Nuevas métricas, correcciones de arquitectura, versión estable, mejoras de evaluación |
| 22 ago | Consolidación de rama, dependencias |
| 31 ago | Etiquetado por terciles |
| 2-3 sep | Revisión y redacción de la memoria |

Comando para regenerarlo: `git log --pretty=format:"%ad %s" --date=short --reverse`

---

## 7 · Lo que ya se resolvió (para no rehacerlo)

Del capítulo 2, los 36 hallazgos originales están cerrados. Lo sustancial:

- §2.1.3 dejó de contradecir a los datos del propio trabajo sobre el volumen de eventos, y ahora distingue GDELT 1.0 de 2.0.
- §2.1.4 introduce las Heterogeneous GNN, de modo que §4.2.3 ya no aterriza en HeteroGAT sin apoyo teórico.
- §2.2.4 dejó de recomendar DTDG y §4.2.1 dejó de contarse como familia establecida.
- §2.2.3 declara qué hereda el trabajo de FSTGAT y de Chen et al.
- §2.3 incorpora el argumento de *late fusion* y HATS como precedente del target.
- §8 se quedó **sin citas huérfanas**: entraron ocho entradas nuevas (Scarselli, Kipf & Welling, Hu, Veličković, van den Oord, Vrandečić & Krötzsch, Hogan, Kazemi) y se corrigió el DOI de Niu.
- El documento se quedó **sin catalanismos** ni errores de concordancia en el capítulo 2.

Del capítulo 4: §4.2.3 cerrado, §4.2.1 casi cerrado, y los objetivos específicos reescritos como OE1-OE6.
