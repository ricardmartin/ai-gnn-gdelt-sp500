# Capítulo X. Desarrollo

> Borrador para el capítulo de *Desarrollo* del TFM, generado a partir del notebook `desarrollo.ipynb` (estado a 20-may-2026). Pensado para copiar y pegar a Word, ajustando estilos de párrafo y numeración a la plantilla del trabajo.

Este capítulo describe la implementación del pipeline de obtención y preparación de datos sobre el que se sustenta el resto del trabajo. La justificación de la elección de GDELT como fuente, así como su comparación con alternativas, queda en el capítulo de *Marco teórico*; aquí se asume ya decidida y se documentan únicamente las decisiones de implementación y los hallazgos empíricos sobre los datos.

El desarrollo se organiza en cuatro bloques: descripción de la fuente (§X.1), descarga (§X.2), carga y esquema (§X.3) y limpieza por contenido (§X.4). El análisis exploratorio y el filtrado final orientados al modelo se tratan en capítulos posteriores.

> **Convenciones para la maquetación en Word.**
>
> Cada bloque rodeado por la marca `📊 INSERTAR FIGURA X.N` debe sustituirse en el documento final por la captura del gráfico correspondiente del notebook `desarrollo.ipynb`. Para exportar las figuras como PNG basta con añadir antes de `plt.show()` en cada celda gráfica:
>
> ```python
> plt.savefig("figuras/figX_N.png", dpi=150, bbox_inches="tight")
> ```
>
> Cada bloque rodeado por la marca `📄 LISTADO X.N` contiene el código que debe ir maquetado como listado numerado (Word: estilo "Code" o cuadro de texto con fuente monoespaciada). El código se referencia en el cuerpo del texto como "ver Listado X.N".
>
> El total de figuras y listados del capítulo es: **6 figuras** y **11 listados**.

---

## X.1 Fuente de datos: GDELT 1.0 Events

La fuente seleccionada para el componente geopolítico del trabajo es **GDELT 1.0 Events**. La elección se tomó tras descartar GDELT 2.0 Events y GDELT GKG. Los argumentos completos se desarrollan en el marco teórico; en términos operativos, la decisión se sustenta en tres aspectos: la cadencia diaria de 1.0 coincide con la granularidad del problema (predicción del S&P 500 a t+1 antes de apertura), su serie histórica diaria comienza dos años antes que la de 2.0 (abril de 2013 frente a febrero de 2015) y su volumen de almacenamiento es aproximadamente un orden de magnitud inferior. La cobertura translingual exclusiva de 2.0 no aporta señal incremental relevante porque el sujeto receptor de la predicción —los mercados estadounidenses— consume mayoritariamente prensa anglófona.

Cada fichero diario de GDELT 1.0 Events tiene la estructura física siguiente:

| Aspecto | Valor |
|---|---|
| URL canónica | `http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip` |
| Compresión | ZIP que contiene un único miembro `YYYYMMDD.export.CSV` |
| Formato del fichero interno | TSV (separado por tabulador), sin cabecera |
| Codificación | ASCII / UTF-8 |
| Columnas | 58 fijas, documentadas en el *codebook* oficial |
| Tamaño descomprimido típico | 20–60 MB por día |
| Volumen | 100 000 – 300 000 eventos por día |
| Latencia | el día `D` se publica con `DATEADDED = D` al día siguiente |

Para fechas anteriores al 1 de abril de 2013, GDELT empaqueta los eventos en ficheros mensuales (2006-03 → 2013-03) o anuales (1979 → 2005) con un esquema y nomenclatura distintos. El presente trabajo se limita al formato diario; la cobertura pre-2013 queda fuera de alcance.

---

## X.2 Descarga de los ficheros diarios

La descarga se implementa en dos niveles. La función `descargar_dia` recupera el fichero correspondiente a una fecha y lo descomprime en memoria, escribiendo en disco únicamente el CSV interno. La función `descargar_rango` itera por todos los días del intervalo `[inicio, fin]` invocando a la anterior.

La operación es **idempotente**: si el fichero ya existe en `data/raw/` se omite, lo que permite reanudar rangos parcialmente descargados sin coste adicional. El código se ha mantenido deliberadamente conciso: no se implementa una capa de gestión de errores defensiva ni reintentos automáticos; cualquier fallo (red, ZIP corrupto, fechas inexistentes) propaga la excepción original al usuario, que decide cómo proceder. Esta decisión es consistente con el espíritu del notebook como artefacto pedagógico y reproducible, en el que cualquier comportamiento anómalo debe ser visible y diagnosticable, no enmascarado.

Para el desarrollo del pipeline se trabaja inicialmente con tres días (14 a 16 de mayo de 2026). La extensión al rango histórico definitivo se hará en una pasada final una vez estabilizada la cadena de transformaciones; el rango concreto a utilizar depende de consideraciones de cobertura de régimenes de mercado y se cierra en una sección posterior del trabajo.

📄 **LISTADO X.1 — Funciones de descarga.** Implementación de `descargar_dia` y `descargar_rango` (notebook `desarrollo.ipynb`, §2.2 y §2.3).

```python
import io, os, urllib.request, zipfile
from datetime import date, timedelta

def descargar_dia(fecha, destino_dir="data/raw"):
    os.makedirs(destino_dir, exist_ok=True)
    nombre = f"{fecha:%Y%m%d}.export.CSV"
    destino = os.path.join(destino_dir, nombre)

    if os.path.exists(destino):
        print(f"  {fecha:%Y%m%d}  ya existe")
        return destino

    url = f"http://data.gdeltproject.org/events/{nombre}.zip"
    with urllib.request.urlopen(url) as r:
        contenido = r.read()
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        with z.open(z.namelist()[0]) as f, open(destino, "wb") as o:
            o.write(f.read())

    print(f"  {fecha:%Y%m%d}  descargado")
    return destino


def descargar_rango(inicio, fin, destino_dir="data/raw"):
    d = inicio
    while d <= fin:
        descargar_dia(d, destino_dir)
        d += timedelta(days=1)
```

**Salida ilustrativa** al re-invocar la descarga sobre los tres días ya presentes en `data/raw/`:

```text
>>> descargar_rango(date(2026, 5, 14), date(2026, 5, 16))
  20260514  ya existe
  20260515  ya existe
  20260516  ya existe
```

La idempotencia se evidencia: ninguna descarga efectiva se ejecuta porque los ficheros ya están en disco. Al pasar un rango de fechas no descargadas previamente, la salida sería análoga sustituyendo `ya existe` por `descargado`.

---

## X.3 Carga y esquema

### X.3.1 Esquema de las 58 columnas

El *codebook* oficial de GDELT 1.0 define un esquema fijo de 58 columnas sin cabecera. Para que `pandas` lo cargue con tipos correctos, se reproduce la lista de nombres y se identifican las columnas numéricas (`GoldsteinScale`, `NumMentions`, `NumSources`, `NumArticles`, `AvgTone`), que se convierten con `pd.to_numeric` en la propia función de carga. El resto se conserva como cadena para mantener compatibilidad con los códigos CAMEO y FIPS, que aunque sean numéricos en apariencia (`"01"`, `"02"`...) deben tratarse como categóricos.

Las 58 columnas se agrupan en nueve bloques funcionales:

| Bloque | Función |
|---|---|
| Identificación (5) | Clave primaria y fechas |
| Actor 1 (10) | Identidad del agente emisor |
| Actor 2 (10) | Identidad del agente receptor |
| Evento (5) | Codificación CAMEO |
| Intensidad y volumen (5) | Métricas cuantitativas |
| Geo Actor 1, 2 y Acción (7 × 3) | Localizaciones |
| Origen (2) | Día de publicación (`DATEADDED`) y URL (`SOURCEURL`) |

Dos detalles del codebook merecen explícita atención porque condicionan todo lo que sigue: los códigos de país en `Actor1CountryCode` y `Actor2CountryCode` utilizan **CAMEO 3-letter** (`USA`, `CHN`, `GBR`, ...), mientras que los códigos en `Actor1Geo_CountryCode`, `Actor2Geo_CountryCode` y `ActionGeo_CountryCode` utilizan **FIPS 10-4 2-letter** (`US`, `CH`, `UK`, ...). Ambos sistemas no son intercambiables y mezclarlos es una fuente frecuente de errores en trabajos basados en GDELT.

De las 58 columnas, las decisiones de modelado del proyecto (ver acta de decisiones, §2.1, revisión 2026-05-20) seleccionan trece como relevantes: `GLOBALEVENTID`, `SQLDATE`, `DATEADDED`, `Actor1CountryCode`, `Actor2CountryCode`, `EventCode`, `EventRootCode`, `QuadClass`, `GoldsteinScale`, `AvgTone`, `NumMentions`, `NumSources` y `NumArticles`. El resto se descarta. La selección añade dos columnas respecto a la formulación inicial del acta: `GLOBALEVENTID` (clave primaria, necesaria para deduplicar) y `DATEADDED` (fecha de publicación efectiva, relevante para evitar *look-ahead* en la predicción financiera).

### X.3.2 Codificación CAMEO

GDELT codifica los eventos mediante el sistema **CAMEO** (*Conflict and Mediation Event Observations*), que define tres niveles de granularidad:

- `EventRootCode` (20 valores, `01`–`20`): grandes categorías de comportamiento, ordenadas de máxima cooperación a máximo conflicto.
- `EventBaseCode` (~80 valores): subdivide cada raíz en subtipos.
- `EventCode` (~300 valores): detalle fino sobre el subtipo.

`QuadClass` agrupa las veinte raíces en cuatro cuadrantes según los ejes cooperación↔conflicto y verbal↔material: cooperación verbal, cooperación material, conflicto verbal y conflicto material. La elección final entre `QuadClass` (4 categorías) y `EventRootCode` (20) como tipado de aristas en el grafo se posterga al análisis exploratorio orientado a modelo. La variable `GoldsteinScale` complementa estas codificaciones con un valor continuo en `[-10, +10]` cuya asignación es **fija por subtipo CAMEO**: dado un `EventCode`, su `GoldsteinScale` no varía entre filas.

### X.3.3 Carga inicial

Para el desarrollo del pipeline se opta por trabajar con **un único día** de datos (`20260515.export.CSV`, 15 de mayo de 2026) como muestra representativa, con la intención de afinar las transformaciones sobre un fichero y aplicarlas posteriormente al rango histórico completo. La elección de ese día se justifica por dos razones: es el fichero que da nombre al repositorio del proyecto y, en la verificación inicial, su volumen (118 201 eventos) está dentro del rango típico de un día completo, frente a otros ficheros del mismo periodo con volumen sensiblemente inferior, indicativos de descargas parciales.

Al cargar el fichero se obtienen 118 201 filas × 58 columnas, sin errores de parseo en ninguna columna numérica.

📄 **LISTADO X.2 — Función `cargar_dia`.** Lectura del TSV con tipado de columnas numéricas (notebook §3.1).

```python
import pandas as pd

COLUMNAS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", ...  # 58 nombres
    "DATEADDED", "SOURCEURL",
]
COLS_NUMERICAS = [
    "GoldsteinScale", "NumMentions", "NumSources",
    "NumArticles", "AvgTone",
]

def cargar_dia(path):
    df = pd.read_csv(
        path, sep="\t", header=None, names=COLUMNAS,
        dtype=str, na_values=[""], keep_default_na=False,
        quoting=3,  # csv.QUOTE_NONE: GDELT no usa comillas
    )
    for c in COLS_NUMERICAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

df = cargar_dia("data/raw/20260515.export.CSV")
```

**Salida ilustrativa** sobre `data/raw/20260515.export.CSV`:

```text
>>> df.shape
(118201, 58)

>>> df.dtypes.value_counts()
object     53
int64       3
float64     2

>>> df[["GLOBALEVENTID","SQLDATE","Actor1CountryCode","Actor2CountryCode",
        "EventRootCode","QuadClass","GoldsteinScale","NumMentions"]].head(3)
GLOBALEVENTID  SQLDATE Actor1CountryCode Actor2CountryCode EventRootCode QuadClass  GoldsteinScale  NumMentions
   1304165771 20250515               NaN               NaN            04         1             1.9          162
   1304165772 20250515               NaN               NaN            04         1             1.9            6
   1304165773 20250515               NaN               NaN            04         1             2.8          162

>>> df[COLS_NUMERICAS].describe().round(2)
       GoldsteinScale  NumMentions  NumSources  NumArticles    AvgTone
count       118201.00    118201.00   118201.00    118201.00  118201.00
mean             0.66        12.49        2.42        12.03      -1.83
std              4.51        72.83        8.30        67.39       4.21
min            -10.00         1.00        1.00         1.00     -26.09
25%             -2.00         2.00        1.00         2.00      -4.54
50%              1.90         4.00        1.00         4.00      -1.71
75%              3.40        10.00        1.00        10.00       1.03
max             10.00      6066.00      379.00      5760.00      22.81
```

La carga produce un *DataFrame* de **118 201 filas × 58 columnas**. De las 58 columnas, 53 permanecen como `object` (cadenas), las tres columnas de volumen (`NumMentions`, `NumSources`, `NumArticles`) se interpretan como `int64` y las dos métricas continuas (`GoldsteinScale`, `AvgTone`) como `float64`. Las primeras filas muestran códigos `Actor*CountryCode` vacíos (`NaN`), comportamiento esperado: GDELT no siempre identifica el país asociado a un actor. La función `describe()` aporta una primera lectura estadística de las variables cuantitativas y permite verificar que los rangos respetan los del *codebook*: `GoldsteinScale` confinado a `[-10, +10]`, `NumMentions/Sources/Articles ≥ 1`, `AvgTone` aproximadamente en `[-30, +30]`.

---

## X.4 Limpieza por contenido

El esquema de GDELT 1.0 tiene una característica que condiciona toda limpieza posterior: **no incluye el texto del artículo**. Solo se proporciona la URL fuente (`SOURCEURL`) y los metadatos estructurados (actores, evento codificado en CAMEO, ubicación, métricas). Esto excluye los enfoques clásicos de PNL sobre el cuerpo de la noticia (clasificación temática supervisada, reconocimiento de entidades sobre el artículo, análisis de sentimiento textual) y obliga a reconstruir una **huella textual sintética** por evento, combinando lo que GDELT sí trae.

El bloque de limpieza por contenido aborda tres preguntas en cascada, cada una con su correspondiente subsección:

1. **¿Cuántas veces aparece la misma noticia en el fichero?** Cada artículo puede generar varias filas en GDELT si menciona múltiples actores o ubicaciones; conviene estimar este factor de inflación (§X.4.1 y §X.4.2).
2. **¿Hay noticias semánticamente equivalentes con URLs distintas?** Mismo evento cubierto por medios diferentes que producen URLs distintas pero contenido equivalente (§X.4.3 y §X.4.4).
3. **¿El criterio aplicado a un día se generaliza a otros?** Una limpieza sólida no es la que funciona en un día concreto, sino la que produce resultados consistentes entre días (§X.4.5).

Se renuncia deliberadamente a una limpieza puramente "mecánica" basada únicamente en las restricciones del *codebook* (validación de rangos, deduplicación por clave primaria, parsing de fechas). Esas operaciones, aunque correctas, no responden a las preguntas anteriores, que son las verdaderamente determinantes para la calidad de la señal que llegará al grafo. Los pasos mecánicos podrán incorporarse en una etapa posterior si algún módulo del pipeline lo requiere.

### X.4.1 Normalización de URL

La columna `SOURCEURL` constituye la única vía hacia el contenido del artículo. Antes de cualquier operación de conteo o comparación, se **canonicalizan** URLs equivalentes para que no queden separadas por diferencias triviales. La función `normalizar_url` aplica cinco reglas:

1. Conversión del *host* a minúsculas (`Example.com` y `example.com` apuntan al mismo recurso).
2. Eliminación de los puertos por defecto `:80` y `:443`.
3. Eliminación de parámetros de tracking en la *query string* (`?utm_source=...`, `?ref=...`), que no afectan al contenido.
4. Eliminación de fragmentos (`#section`), que tampoco modifican el recurso.
5. Supresión de la barra final.

Las URLs no parseables o vacías se reducen a `None` y las filas correspondientes se descartan: sin URL no es posible analizar contenido. Sobre el fichero del 15-may-2026 esta operación no descartó ninguna fila, lo que indica que `SOURCEURL` viene íntegro en GDELT.

Tras la normalización, las 118 201 filas se distribuyen en **24 412 URLs únicas**.

📄 **LISTADO X.3 — Normalización de URL** (notebook §4.1).

```python
import re

_RE_PUERTO = re.compile(r":(80|443)(?=/|$)")
_RE_QUERY  = re.compile(r"[?#].*$")

def normalizar_url(u):
    """URL canónica: host en minúsculas, sin puerto estándar ni query/fragment."""
    if not isinstance(u, str) or not u.strip():
        return None
    s = u.strip()
    s = _RE_QUERY.sub("", s)
    s = _RE_PUERTO.sub("", s)
    s = s.rstrip("/")
    m = re.match(r"^(https?://)([^/]+)(.*)$", s, re.I)
    if m:
        s = m.group(1).lower() + m.group(2).lower() + m.group(3)
    return s or None

df["url_norm"] = df["SOURCEURL"].map(normalizar_url)
df = df[df["url_norm"].notna()].reset_index(drop=True)
```

**Salida ilustrativa** sobre el día del 15 de mayo:

```text
Filas antes:                         118 201
Descartadas por URL no parseable:          0
Filas tras normalización:            118 201
URLs únicas:                          24 412
```

Ninguna fila se descarta por URL no parseable, lo que indica que `SOURCEURL` se rellena de manera consistente en GDELT 1.0. La aparición de **24 412 URLs únicas** frente a las 118 201 filas iniciales adelanta ya el factor de inflación que se cuantifica formalmente en X.4.2.

### X.4.2 Conteo de ocurrencias por URL

Agrupando por `url_norm` se mide el factor real de duplicación del fichero. Los estadísticos resultantes sobre el día analizado son:

- Media de ocurrencias por URL: **4.84**.
- Mediana: **3**.
- Máximo: **158**.
- Porcentaje de URLs que aparecen una sola vez: **27.3 %**.

Es decir, cada artículo genera de media casi cinco filas en GDELT, y solo poco más de una cuarta parte aparece una única vez. Este factor de inflación es un dato fundamental: contar eventos sin colapsar por URL sobreestima sistemáticamente el volumen de noticias.

La distribución es claramente sesgada a la derecha, con una cola larga. El examen de las URLs en el extremo superior reveló un hallazgo relevante: las dos más repetidas (158 y 125 ocurrencias) corresponden a **URLs genéricas** sin contenido específico:

- `targetednews.com/pr_disp.php` (158): formulario de envío de notas de prensa, no un artículo concreto.
- `freerepublic.com/tag/*/index` (125): página de índice por etiqueta, no una noticia.

GDELT está adjuntando estas URLs comodín a múltiples eventos distintos sin que correspondan en realidad a una sola noticia. Su presencia en el recuento inflaría artificialmente las métricas y, en el grafo, generaría "super-eventos" espurios. Esto justifica el paso siguiente, que las filtrará automáticamente.

> 📊 **INSERTAR FIGURA X.1 — Distribución de ocurrencias por URL.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.2 (celda inmediatamente posterior a la del conteo). Histograma de barras del número de URLs por nivel de ocurrencias, truncado a 30, con escala logarítmica en el eje Y. Se aprecia la **caída tipo ley de potencias** característica de la distribución de cobertura: la mayoría de URLs aparece pocas veces y unas pocas (las URLs basura) ocupan el extremo de la cola.

📄 **LISTADO X.4 — Conteo de ocurrencias por URL** (notebook §4.2).

```python
oc = (df.groupby("url_norm")
        .size()
        .reset_index(name="ocurrencias")
        .sort_values("ocurrencias", ascending=False)
        .reset_index(drop=True))

print(f"URLs únicas:             {len(oc):,}")
print(f"Media ocurrencias/URL:   {oc['ocurrencias'].mean():.2f}")
print(f"Mediana:                 {oc['ocurrencias'].median():.0f}")
print(f"Máximo:                  {oc['ocurrencias'].max()}")
```

**Salida ilustrativa:**

```text
URLs únicas:             24 412
Media ocurrencias/URL:     4.84
Mediana:                      3
Máximo:                     158
% URLs con 1 ocurrencia:  27.3%

Top 10 URLs más repetidas:
   158x  https://targetednews.com/pr_disp.php
   125x  https://freerepublic.com/tag/*/index
   118x  https://ismatimes.com/gttci-ethiopian-coffee-evening-farewell
   117x  https://www.dailysabah.com/politics/diplomacy/turkiyes-fidan-attends-ots-ministers-meeting-in-turkistan
   104x  https://www.livemint.com/news/india/pm-modi-embarks-on-high-stakes-uae-and-europe-today
    ...
```

El **factor medio de inflación es 4.84×** y la mediana es 3, lo que confirma la naturaleza repetitiva del dataset. El examen de las URLs en el extremo superior pone de manifiesto el problema central de este paso: las dos URLs más repetidas (`targetednews.com/pr_disp.php` y `freerepublic.com/tag/*/index`) son **páginas genéricas** —formulario de press release y un índice de etiquetas— que GDELT está adjuntando a múltiples eventos distintos sin que correspondan a una sola noticia. Estas URLs justifican el filtro del paso siguiente.

### X.4.3 Texto sintético por evento

Para detectar contenido equivalente y para los pasos de embeddings y LDA posteriores se construye, por evento, un **texto sintético** a partir de tres fuentes complementarias:

1. **Slug del path de la URL.** En muchas cabeceras actuales el titular va embebido en la URL (`/news/elon-musk-jets-off-to-china`, `/politics/israel-lebanon-ceasefire-extended`). Se extraen los tokens del *path*, se descartan los de longitud inferior a tres caracteres, los que contienen dígitos (típicos de identificadores), los hexadecimales (UUIDs) y un conjunto cerrado de *stopwords* específicas de URLs (`news`, `article`, `html`, `index`, ...).
2. **Metadatos estructurados** del propio evento: `Actor1Name`, `Actor2Name` y `ActionGeo_FullName`, todos en minúsculas.
3. **Etiquetas textuales de la codificación CAMEO**: descripción del `EventRootCode` (`appeal`, `protest`, `fight`, ...) y del `QuadClass` (`verbal cooperation`, `material conflict`, ...). Aportan el "qué tipo de evento" en lenguaje natural.

El texto sintético resultante tiene, en el día analizado, una media de **18 tokens** (mediana 18, mínimo 7, máximo 43). No es prosa, pero es suficientemente informativo para los modelos densos del paso siguiente.

Se impone un filtro adicional sobre el slug: si tras eliminar *stopwords* y tokens espurios el slug resultante tiene menos de **tres tokens significativos**, la fila se descarta. Este umbral filtra automáticamente las URLs basura detectadas en X.4.2 (sus paths son `pr_disp.php` o `tag/*/index`, sin contenido legible). El resultado sobre el día analizado es que de **118 201 filas se conservan 107 248** (90.7 %), descartándose 10 953 (9.3 %), y se verifica que las dos URLs basura identificadas previamente caen al 100 %.

📄 **LISTADO X.5 — Construcción del texto sintético** (notebook §4.3).

```python
CAMEO_ROOT = {
    "01": "make public statement", "02": "appeal",
    "03": "express intent to cooperate", "04": "consult",
    "05": "engage in diplomatic cooperation",
    "06": "engage in material cooperation", "07": "provide aid",
    "08": "yield", "09": "investigate", "10": "demand",
    "11": "disapprove", "12": "reject", "13": "threaten",
    "14": "protest", "15": "exhibit force posture",
    "16": "reduce relations", "17": "coerce", "18": "assault",
    "19": "fight", "20": "use unconventional mass violence",
}
QUAD_CLASS = {
    "1": "verbal cooperation",  "2": "material cooperation",
    "3": "verbal conflict",     "4": "material conflict",
}
_STOP_SLUG = {"news", "article", "story", "post", "index", "html",
              "php", "www", "the", "and", "for", "with", "from",
              "world", "local", "video", "live", "breaking", ...}
_RE_HEX = re.compile(r"^[0-9a-f]{6,}$", re.I)
_RE_TIENE_DIGITO = re.compile(r"\d")
_RE_HOST = re.compile(r"^https?://([^/]+)(.*)$", re.I)

def slug_tokens(url):
    if not url: return ""
    m = _RE_HOST.match(url)
    path = m.group(2) if m else url
    crudos = re.split(r"[/\-_.]+", path.lower())
    return " ".join(
        t for t in crudos
        if len(t) >= 3
        and t not in _STOP_SLUG
        and not _RE_TIENE_DIGITO.search(t)
        and not _RE_HEX.match(t)
    )

def metadatos_evento(row):
    partes = []
    for c in ("Actor1Name", "Actor2Name", "ActionGeo_FullName"):
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            partes.append(v.lower())
    root = str(row.get("EventRootCode") or "").zfill(2)
    partes.append(CAMEO_ROOT.get(root, ""))
    partes.append(QUAD_CLASS.get(str(row.get("QuadClass") or ""), ""))
    return " ".join(p for p in partes if p)

MIN_PALABRAS_SLUG = 3
df["slug"] = df["url_norm"].map(slug_tokens)
df["n_slug"] = df["slug"].str.split().map(len)
df = df[df["n_slug"] >= MIN_PALABRAS_SLUG].copy()
df["meta"] = df.apply(metadatos_evento, axis=1)
df["texto"] = (df["slug"] + " " + df["meta"]).str.replace(
    r"\s+", " ", regex=True).str.strip()
```

**Salida ilustrativa:**

```text
Filas antes del filtro slug: 118 201
Filas tras filtro slug ≥ 3:  107 248  (90.7 %)
Descartadas:                  10 953  ( 9.3 %)

Tokens por texto sintético:
  media:   18.0
  mediana: 18
  min/max: 7 / 43

Ejemplos (filas al azar):
  URL:   https://www.marinecorpstimes.com/news/your-military/2026/05/15/army-leaders-in-hot-seat-...
  texto: your military army leaders hot seat over poland deployment cancellation european publication
         iran reject verbal conflict

  URL:   https://www.thenationalnews.com/news/us/2026/05/15/israel-lebanon-ceasefire-extended-by-45...
  texto: israel lebanon ceasefire extended days israeli washington washington, district of columbia,
         united states reject verbal conflict
```

El filtro descarta **el 9.3 % de las filas** (10 953), exactamente las que tenían URL genérica sin titular embebido. Se verifica además que las dos URLs basura del extremo superior de X.4.2 (`pr_disp.php`, `tag/*/index`) caen al 100 %. El texto resultante tiene una mediana de **18 tokens**, suficiente para alimentar los embeddings densos del paso siguiente y para un LDA de baja resolución temática.

### X.4.4 Embeddings semánticos y clustering

El conteo por URL canónica de X.4.2 detecta exactamente la misma URL repetida, pero no captura el caso de mayor interés para este trabajo: **un mismo evento cubierto por medios distintos** (Reuters, Bloomberg, AP), con URLs diferentes pero contenido equivalente. Para abordar este caso se proyectan los textos sintéticos a un espacio vectorial denso mediante embeddings, y se agrupan los vectores cercanos por similitud coseno.

**Granularidad.** Se calcula un embedding por **URL única**, no por fila. Esta decisión se basa en que todas las filas asociadas a una misma URL comparten el slug, por lo que sus textos sintéticos son prácticamente idénticos. Calcular embeddings por fila multiplicaría el coste sin aportar información incremental. La reducción es de aproximadamente 107 248 filas a 22 572 URLs únicas (tras el filtro de slug de X.4.3).

**Modelo.** Se utiliza `sentence-transformers/all-MiniLM-L6-v2`, un modelo Transformer ligero de 22 millones de parámetros y 384 dimensiones de salida, considerado en la literatura como una referencia estándar para "embeddings densos ligeros" en tareas de retrieval y similitud sobre texto corto en inglés. La inferencia sobre 22 572 textos cortos en CPU completa en aproximadamente **80 segundos** con un *batch size* de 128. La matriz resultante (22 572 × 384, ~34 MB en `float32`) se almacena en disco como caché reproducible, evitando recalcular en ejecuciones sucesivas.

**Algoritmo de clustering.** Se construye un grafo dirigido de k-vecinos más próximos sobre los embeddings (k = 15, métrica coseno). Se filtran las aristas cuya similitud coseno sea inferior a **0.80**, y se calculan las **componentes conexas** del grafo resultante. Cada componente es un cluster de noticias relacionadas. Esta formulación tiene tres ventajas frente a alternativas más sofisticadas (DBSCAN, HDBSCAN, *agglomerative*): no impone una cantidad fija de clusters, escala linealmente con el número de vectores y produce agrupaciones interpretables sin hiperparámetros opacos.

**Resultado.** Sobre el fichero analizado, los 22 572 puntos se agrupan en **19 423 clusters**, de los cuales el **94.4 %** son singletons (un único punto sin vecinos suficientemente próximos) y el **5.6 %** son grupos de dos o más. El cluster más grande contiene 318 URLs. El tamaño medio de cluster es 1.16.

> 📊 **INSERTAR FIGURA X.2 — Distribución de tamaños de cluster.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.4 (celda inmediatamente posterior a la del clustering). Histograma de barras del número de clusters por tamaño (URLs únicas agrupadas), truncado a 50, con escala logarítmica en el eje Y. Confirma visualmente el resultado cuantitativo: la mayoría de los clusters son singletons (~94 %) y existe una cola larga de clusters grandes que concentran la cobertura mediática del día.

📄 **LISTADO X.6 — Embeddings con MiniLM y clustering por componentes conexas** (notebook §4.4).

```python
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

# 1) Un texto representativo por URL única
texto_por_url = df.groupby("url_norm", as_index=False)["texto"].first()

# 2) Embeddings densos con caché en disco
CACHE_EMB = Path("data/embeddings_url_20260515.npy")
if CACHE_EMB.exists():
    emb = np.load(CACHE_EMB)
else:
    st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    emb = st.encode(
        texto_por_url["texto"].tolist(),
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=128,
    )
    emb = np.asarray(emb, dtype="float32")
    np.save(CACHE_EMB, emb)

# 3) Clustering por componentes conexas sobre grafo kNN coseno
UMBRAL_SIMILITUD = 0.80
N_VECINOS = 15

n = len(emb)
nn = NearestNeighbors(n_neighbors=min(N_VECINOS, n),
                      metric="cosine").fit(emb)
dist, idx = nn.kneighbors(emb)

filas, cols = [], []
lim = 1.0 - UMBRAL_SIMILITUD
for i in range(n):
    for d, j in zip(dist[i], idx[i]):
        if i != j and d <= lim:
            filas.append(i); cols.append(j)

if filas:
    g = csr_matrix((np.ones(len(filas)), (filas, cols)),
                   shape=(n, n))
    _, etiquetas = connected_components(g, directed=False)
else:
    etiquetas = np.arange(n)

texto_por_url["cluster"] = etiquetas
```

**Salida ilustrativa:**

```text
Embeddings calculados:    (22 572, 384)   — 384 dims, ~80 s en CPU
Número de clusters:       19 423
Singletons (1 URL):       18 326  (94.4 %)
Clusters con ≥ 2 URLs:     1 097
Tamaño máximo:               318
Tamaño medio:               1.16

Top 5 clusters por tamaño:
  Cluster 130 (318 URLs):
    URL:   http://www.bgnes.com/politics/trump-warns-taiwan-not-to-move-toward-independence
    texto: trump warns taiwan not move toward independence taiwan beijing, beijing, china threaten
           verbal conflict

  Cluster 143 (107 URLs):
    URL:   https://13wham.com/news/local/suspected-hantavirus-case-in-ontario-county-involves-...
    texto: suspected hantavirus case ontario county involves geneva high school student

  Cluster 137 (93 URLs):
    URL:   http://www.heraldglobe.com/news/.../amid-spiralling-relations-cuban-government-meets-cia
    texto: amid spiralling relations cuban government meets cia director ratcliffe havana
```

El **94.4 % de los puntos quedan como singletons** y solo un 5.6 % forma clusters de dos o más URLs. La interpretación, ya señalada en el texto, es que el umbral 0.80 produce **clusters de naturaleza temática**. El cluster más grande (318 URLs) agrupa noticias diplomáticas heterogéneas; los clusters de tamaño medio (decenas de URLs) sí corresponden cada uno a un único evento ampliamente cubierto (juicio Weinstein, brote hantavirus, reunión CIA–Cuba, etc.).

**Interpretación de los clusters resultantes.** El umbral coseno de 0.80 elegido produce **clusters de naturaleza temática** más que clusters de "misma noticia exacta". El cluster mayor, al examinarlo, agrupa noticias diplomáticas heterogéneas (advertencias EE.UU.-Taiwán, prórroga del alto el fuego Israel-Líbano, etc.) que comparten vocabulario y estructura (*"threaten"*, *"verbal conflict"*, nombres de países en tensión). Los clusters de tamaño intermedio (decenas de URLs), en cambio, sí corresponden a un único evento cubierto por muchos medios: el cluster de 85 URLs sobre el juicio a Harvey Weinstein, el de 107 URLs sobre el brote de hantavirus tras un crucero, el de 64 URLs sobre el brote de ébola en la R. D. del Congo, el de 93 URLs sobre la reunión de la CIA con La Habana. Para una deduplicación estricta tipo "mismo artículo reescrito" habría que subir el umbral por encima de 0.90, aceptando que muchas reescrituras se quedasen sin agrupar. La elección de 0.80 se mantiene deliberadamente: para el TFM interesa más detectar **temas con mucha cobertura**, susceptibles de generar señal en mercados, que deduplicar artículos individualmente. Una iteración futura podría revisitar este umbral o estratificar el clustering en dos pasos.

### X.4.5 Validación cruzada entre días

El criterio último de calidad de la limpieza no es el comportamiento sobre un día concreto, sino la **estabilidad de las métricas entre días**. Si la regla de filtrado de slug descarta el 9 % en un día y el 30 % en otro, la regla no generaliza. Si la lista de países activos cambia drásticamente día a día, la lista de nodos del grafo no puede fijarse con seguridad.

Se aplica la cadena completa (X.4.1 a X.4.4) a los tres días disponibles (14, 15 y 16 de mayo de 2026) y se comparan métricas robustas. El código se encapsula en una función `procesar_dia(path)` que devuelve el DataFrame procesado, la tabla de URLs únicas con su cluster y un diccionario con las métricas agregadas del día.

**Resultados.** La tabla siguiente recoge los valores obtenidos sobre los tres días procesados:

| Métrica | 14-may | 15-may | 16-may |
|---|---:|---:|---:|
| Filas iniciales | 127 851 | 118 201 | 73 293 |
| URLs no parseables | 0 | 0 | 0 |
| Filas tras filtro slug | 115 987 | 107 248 | 65 690 |
| % descarte slug | **9.3 %** | **9.3 %** | **10.4 %** |
| URLs únicas (post slug) | 24 048 | 22 572 | 13 543 |
| Factor de inflación | **4.82** | **4.75** | **4.85** |
| Número de clusters | 20 471 | 19 423 | 11 400 |
| % singletons | **93.6 %** | **94.4 %** | **94.6 %** |
| Tamaño máximo de cluster | 459 | 318 | 192 |

La estabilidad es marcada: el porcentaje de descarte por filtro de slug, el factor de inflación y el porcentaje de singletons del clustering varían dentro de márgenes de unas pocas décimas porcentuales o décimas unitarias. La única peculiaridad es el menor volumen absoluto del 16 de mayo (73 k filas frente a ~120 k de los otros días), atribuible a una publicación parcial del fichero diario; los porcentajes derivados no se ven afectados.

> 📊 **INSERTAR FIGURA X.3 — Estabilidad de las métricas entre días.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.6 (celda situada justo tras la tabla comparativa). Tres paneles de barras verticales que muestran, día a día, el porcentaje de descarte por slug, el factor de inflación y el porcentaje de singletons del clustering. Las barras son prácticamente iguales en altura entre los tres días, evidencia visual directa de la estabilidad del pipeline entre días distintos.

**Índice de Jaccard entre pares de días.** Se calcula el índice de Jaccard entre los conjuntos de URLs canónicas y entre las listas de los 20 países más frecuentes en `Actor1CountryCode` y `Actor2CountryCode`:

| Comparación | URLs | Actor1 (top 20) | Actor2 (top 20) |
|---|---:|---:|---:|
| 14 vs 15 | 0.000 | 0.739 | 0.905 |
| 14 vs 16 | 0.000 | 0.818 | 0.905 |
| 15 vs 16 | 0.000 | 0.818 | 0.818 |

La lectura es la esperada y refuerza la validez del pipeline:

- **Jaccard URLs nulo en los tres pares**: ninguna URL canónica se repite entre dos días distintos. Esto confirma que GDELT no re-publica los eventos en ficheros consecutivos y que cada día representa noticias genuinamente nuevas.
- **Jaccard de Actor1/Actor2 top 20 entre 0.74 y 0.91**: los países más activos coinciden mayoritariamente entre días. Esta estabilidad es la base que permite fijar la lista de ~20 nodos del grafo a partir de un periodo de calibración sin temor a que cambie significativamente en periodos cercanos.

**Conclusión.** El pipeline de limpieza por contenido es estable entre días: los umbrales actuales pueden mantenerse sin necesidad de calibración por día, y la selección final de nodos del grafo puede realizarse sobre un periodo de calibración con la expectativa razonable de que generalice al resto del rango histórico que se descargará para el entrenamiento del modelo.

> 📊 **INSERTAR FIGURA X.4 — Heatmaps de Jaccard entre días.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.6 (celda inmediatamente posterior a la del cálculo de Jaccards). Tres heatmaps cuadrados (3×3) con los índices de Jaccard entre pares de días para tres conjuntos: URLs canónicas, top 20 de `Actor1CountryCode` y top 20 de `Actor2CountryCode`. El primer heatmap es uniformemente cero fuera de la diagonal (no hay solape de URLs entre días); los otros dos son verdes intensos fuera de la diagonal (los mismos países son protagonistas cada día).

📄 **LISTADO X.7 — Función `procesar_dia` y validación cruzada** (notebook §4.5).

```python
def procesar_dia(path, modelo_st, umbral=0.80, vecinos=15):
    """Aplica §4.1-§4.4 y devuelve (df, texto_por_url, métricas)."""
    fecha = Path(path).name[:8]
    df_d = cargar_dia(path)
    n_inicial = len(df_d)

    # X.4.1 normalización
    df_d["url_norm"] = df_d["SOURCEURL"].map(normalizar_url)
    df_d = df_d[df_d["url_norm"].notna()].reset_index(drop=True)

    # X.4.3 texto sintético + filtro slug ≥ 3 tokens
    df_d["slug"] = df_d["url_norm"].map(slug_tokens)
    df_d["n_slug"] = df_d["slug"].str.split().map(len)
    df_d = df_d[df_d["n_slug"] >= 3].copy()
    df_d["meta"] = df_d.apply(metadatos_evento, axis=1)
    df_d["texto"] = (df_d["slug"] + " " + df_d["meta"]).str.replace(
        r"\s+", " ", regex=True).str.strip()
    df_d = df_d.drop(columns=["n_slug"]).reset_index(drop=True)

    # X.4.4 embeddings + clustering, con caché por día
    tpu = df_d.groupby("url_norm", as_index=False)["texto"].first()
    cache = Path(f"data/embeddings_url_{fecha}.npy")
    if cache.exists():
        emb_d = np.load(cache)
    else:
        emb_d = np.asarray(modelo_st.encode(
            tpu["texto"].tolist(),
            normalize_embeddings=True,
            batch_size=128), dtype="float32")
        np.save(cache, emb_d)

    # (clustering kNN + componentes conexas; ver Listado X.6)
    # ...

    return df_d, tpu, metricas


# Aplicación a los 3 días y tabla comparativa
for path_dia in sorted(Path("data/raw").glob("*.export.CSV")):
    fecha_d = path_dia.name[:8]
    resultados[fecha_d] = procesar_dia(path_dia, st_modelo)


# Jaccard entre pares de días
def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 0.0
```

**Salida ilustrativa** sobre los tres días procesados:

```text
TABLA COMPARATIVA ENTRE DÍAS
métrica                          20260514       20260515       20260516
Filas iniciales                   127 851        118 201         73 293
% descarte slug                      9.3 %          9.3 %         10.4 %
Factor inflación                    4.82           4.75           4.85
URLs únicas (post slug)            24 048         22 572         13 543
N clusters                        20 471         19 423         11 400
% singletons                       93.6 %         94.4 %         94.6 %
Máx tamaño cluster                   459            318            192

JACCARD ENTRE PARES DE DÍAS
comparación                URLs    Actor1 top20    Actor2 top20
20260514 vs 20260515:     0.000        0.739           0.905
20260514 vs 20260516:     0.000        0.818           0.905
20260515 vs 20260516:     0.000        0.818           0.818
```

La estabilidad de las métricas entre los tres días es marcada: el porcentaje de descarte por slug, el factor de inflación y el porcentaje de singletons del clustering varían apenas unas décimas. Los Jaccards confirman la lectura esperada: nula superposición de URLs entre días (GDELT no re-publica entre ficheros consecutivos) frente a alta superposición de los países más activos (los mismos protagonistas geopolíticos aparecen cada día).

### X.4.6 Filtrado dirigido al grafo

El cierre del bloque de tratamiento de datos consiste en una **reducción agresiva** del conjunto destinada a alimentar el modelo. La limpieza previa ha dejado 288 925 filas y 51 294 clusters semánticos en los tres días procesados, lo cual sigue siendo excesivo para un grafo de aproximadamente 20 nodos en el que cada arista debe corresponder a una **señal informativa relevante** y no a una noticia local aislada.

Se aplican dos filtros con justificación independiente:

- **Filtro A — concurrencia de fenómeno (`tamaño de cluster ≥ K_min`).** Conservar únicamente las noticias cubiertas por al menos `K_min` medios distintos. Esta es la traducción operativa de "concurrencia de fenómeno": si varios medios independientes cubren el mismo evento, hay señal real susceptible de mover mercados; un *singleton* (una sola URL) es probablemente ruido local sin impacto financiero. El filtro se aplica sobre el `cluster_global` (identificador de cluster combinado con la fecha).

- **Filtro B — relevancia geopolítica (`Actor1 ∈ N ∨ Actor2 ∈ N`).** Conservar solo eventos en los que al menos uno de los actores pertenece al conjunto `N` de los ~20 nodos país del grafo (acta §2.3). Los eventos entre países fuera de esta lista no aportan aristas al grafo y solo añaden ruido.

Se deja deliberadamente fuera de esta primera pasada cualquier filtro sobre `NumMentions`, `EventRootCode` o `QuadClass`, para no acumular umbrales sin justificación empírica. Quedan disponibles como ablaciones para la fase experimental del modelo.

**Barrido del umbral `K_min`.** La tabla siguiente muestra el efecto de varios valores sobre el conjunto combinado de tres días, manteniendo el filtro B activo:

| `K_min` | Filas | Clusters | Noticias/día |
|---:|---:|---:|---:|
| 2 | 40 433 | 2 388 | ~796 |
| 3 | (intermedio) | ~1 200 | ~400 |
| 5 | **23 247** | **375** | **~125** |
| 10 | 18 061 | 138 | ~46 |
| 20 | (muy reducido) | <50 | ~15 |

**Configuración elegida.** Se fija `K_min = 5` como compromiso entre señal y diversidad. Valores K<5 dejan demasiada cola (miles de clusters de cobertura media que arrastran ruido), mientras que valores K>10 reducen excesivamente la diversidad y empobrecen los días con menor volumen mediático (típicamente fines de semana y festivos). El umbral elegido produce ~125 noticias significativas por día, orden de magnitud adecuado para alimentar un grafo dinámico de 20 nodos.

**Resultado final.** Tras la aplicación de ambos filtros, el conjunto de trabajo final `df_grafo` contiene **~23 250 filas** y **~375 clusters semánticos** en los tres días. Cada fila representa un evento GDELT (potencial arista dirigida `Actor1 → Actor2`) etiquetado con su cluster de noticia, y cada cluster cuantifica la intensidad de cobertura mediática del evento subyacente.

Las decisiones específicas de modelado —cómo agregar las filas a aristas del grafo dinámico, cómo ponderar las aristas por tamaño de cluster, cómo incorporar `GoldsteinScale` y `AvgTone` como atributos— son objeto del capítulo siguiente. Con esto se cierra la fase de tratamiento de datos.

> 📊 **INSERTAR FIGURA X.5 — Barrido del umbral K_min y embudo de reducción.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.6 (celda situada tras la aplicación del filtro). Dos paneles:
>
> - *Izquierda:* curva del número de clusters resultantes en función de `K_min` (escala logarítmica en Y, valores 2 a 20). Línea vertical roja discontinua en K = 5 que marca el umbral elegido. Cada punto etiquetado con su cuenta exacta. - *Derecha:* embudo horizontal con cuatro barras que representan, en escala logarítmica, el tamaño del corpus en cada etapa del pipeline (inicial, post-slug, post-clustering, post-filtrado dirigido). Permite visualizar la reducción acumulada de tres órdenes de magnitud entre el corpus bruto y el conjunto final para el grafo.

📄 **LISTADO X.8 — Filtrado dirigido al grafo** (notebook §4.6).

```python
NODOS_ACTA = {
    "USA","CAN","MEX","BRA","EUR",
    "DEU","FRA","GBR",
    "CHN","JPN","KOR","IND","TWN",
    "RUS","SAU","IRN","ISR","TUR",
    "AUS","PRK",
}
K_MIN = 5

# Concatenar los 3 dias con merge de cluster
trozos = []
for fecha_d, (df_d, tpu_d, _) in resultados.items():
    df_m = df_d.merge(tpu_d[["url_norm","cluster"]],
                      on="url_norm", how="left")
    df_m = df_m.assign(
        fecha=fecha_d,
        cluster_global=fecha_d + "_" + df_m["cluster"].astype(str))
    trozos.append(df_m)
df_all = pd.concat(trozos, ignore_index=True)

# Filtros A (concurrencia) y B (geopolitica)
tam_cluster = df_all.groupby("cluster_global")["url_norm"].nunique()
mask_A = df_all["cluster_global"].isin(
    set(tam_cluster[tam_cluster >= K_MIN].index))
mask_B = (df_all["Actor1CountryCode"].isin(NODOS_ACTA)
          | df_all["Actor2CountryCode"].isin(NODOS_ACTA))

df_grafo = df_all[mask_A & mask_B].copy().reset_index(drop=True)
```

**Salida ilustrativa:**

```text
Base post §4.1–§4.4: 288 925 filas   51 294 clusters

Barrido de K (con filtro B activo):
   K       filas    clusters
   2      40 433       2 388
   3      26 540       1 028
   5      23 247         375
  10      18 061         138
  20       6 500          25

Filas finales (df_grafo):              23 247
Clusters (noticias) finales:              375
Reducción vs base post §4.1–§4.4:      filas ×12.4,  clusters ×136.8

Reparto por día:
          filas  noticias  países_distintos
fecha
20260514  10093       149                23
20260515   7787       136                22
20260516   5367        90                21
```

Sobre los 288 925 filas y 51 294 clusters de la base, la combinación **K ≥ 5 + países_OR** produce **23 247 filas / 375 noticias** repartidas de forma equilibrada entre los tres días (149 / 136 / 90). El número de países distintos por día oscila entre 21 y 23, próximo al objetivo de ~20 nodos del grafo. Esto valida empíricamente la elección de parámetros del filtrado dirigido.

### X.4.7 LDA — temas latentes

Tras la limpieza por contenido (§X.4.1–§X.4.4) y la reducción dirigida al grafo (§X.4.6), se aplica un **Modelado de Tópicos Latentes** (Latent Dirichlet Allocation, Blei et al., 2003) sobre el corpus de textos sintéticos. El objetivo es complementar el *clustering* estructural de §X.4.4 con una **partición temática suave**: cada documento se representa como una distribución de probabilidad sobre *k* tópicos, y cada tópico como una distribución sobre el vocabulario. Esta representación permitirá, en la fase de modelado, incorporar el *topic mix* como atributo adicional de las aristas del grafo (`edge_attr`) o como *feature* agregado del nodo (perfil temático del país).

**Precauciones específicas del corpus GDELT.** Tres consideraciones condicionan la calidad y la interpretación de los tópicos resultantes:

1. **El texto sintético es pobre** (~18 *tokens* por documento) frente a un LDA clásico sobre artículos completos. Los tópicos tienden a estar dominados por nombres de actor y descriptores geográficos más que por temáticas noticiosas en sentido amplio.
2. **Las palabras del propio etiquetado CAMEO** (`cooperation`, `conflict`, `threaten`, etc.) aparecen en casi todos los documentos. Si no se filtran como *stopwords*, dominan los tópicos artificialmente. Lo mismo ocurre con las *stopwords* específicas de URLs utilizadas en §X.4.3 (`news`, `index`, `html`, ...).
3. **El vocabulario se restringe** a términos alfabéticos de ≥ 3 caracteres que aparezcan en al menos 10 documentos y en menos del 50 % del corpus, para reducir el ruido y los términos demasiado frecuentes.

**Granularidad.** Se entrena el LDA sobre los textos únicos por URL del corpus combinado de los tres días (~60 000 documentos), idéntica granularidad que la utilizada para los embeddings de §X.4.4, para evitar inflación artificial por la repetición de filas con misma URL.

**Estado actual de la implementación.** En el notebook `desarrollo.ipynb`, el LDA está implementado en las celdas §4.7 posteriores al filtrado dirigido. El modelo no se utiliza todavía como filtro adicional del corpus: su papel actual es **exploratorio y de enriquecimiento**. Es decir, permite etiquetar temáticamente las 375 noticias finales y deja preparada una variable candidata para la fase de modelado, pero no altera el conjunto de aristas que llega a la GNN.

La cadena implementada es la siguiente: primero se toma un único documento por URL normalizada (`url_norm`) a partir de `df_all`, evitando que las múltiples filas GDELT de una misma noticia inflen artificialmente el entrenamiento; después se construye una matriz *bag-of-words* con `CountVectorizer`; finalmente se entrena `LatentDirichletAllocation` con `k = 15`, método `online`, `max_iter = 15` y `random_state = 0`. La salida del modelo (`doc_topic`) contiene, para cada URL, una distribución de probabilidad sobre los 15 tópicos.

**Elección de `k`.** Se realiza un barrido con `k ∈ {10, 15, 20}`, entrenando un LDA *online* durante 15 iteraciones y reportando la perplejidad sobre el propio corpus. La tabla siguiente resume el resultado del barrido:

| `k` | Perplejidad | Tiempo entrenamiento |
|---:|---:|---:|
| 10 | 2 081 | 58 s |
| **15** | **2 239** | **63 s** |
| 20 | 2 206 | 83 s |

Para `k = 10` los tópicos agrupan regiones excesivamente amplias (p. ej. un único tópico que mezcla EE.UU., Reino Unido y África). Para `k = 20` los tópicos empiezan a fragmentarse en subgrupos poco interpretables. Aunque la perplejidad no mejora monótonamente, **se elige `k = 15`** como compromiso interpretativo entre granularidad y coherencia; en este caso la decisión no se toma por optimización automática de la perplejidad, sino por inspección cualitativa de los tópicos.

**Tópicos resultantes (k = 15).** Una vez entrenado el modelo, cada tópico queda caracterizado por las palabras con mayor probabilidad asignada. A modo ilustrativo, los más representativos del corpus analizado son:

- **T0 — Oriente Medio:** *israel, general, media, bank, west, gaza, lebanon, british, arab, israeli, emirates*
- **T8 — África / Pakistán:** *nigeria, africa, student, cms, lagos, woman, ghana, netherlands, kerala, accused, greece*
- **T10 — Eje EEUU–China–Taiwán–Irán:** *china, iran, trump, beijing, president, london, taiwan, tehran, chinese, war, says, east*
- **T13 — EEUU local:** *united, states, new, texas, york, florida, county, health, north, carolina, zealand, arizona*
- **T11 — Política británica:** *united, kingdom, minister, opinion, louisiana, congress, georgia, manchester, tennessee, voter, prime, massachusetts*

El resto de tópicos cubre regiones secundarias (India, Australia, Canadá, Francia) o sub-tipos de eventos (policía/judicial, universidad/educación, comunidad/política local). La interpretación detallada figura como **Figura X.6** y en la salida del Listado X.9 del notebook (§4.7).

**Asignación a las noticias filtradas.** Para cada noticia del corpus final (`cluster_global` de §X.4.6) se asigna el **tópico dominante**, definido como el tópico de mayor probabilidad en su documento representativo. La asignación se hace con un mapeo `url_norm → tópico`, de forma que el tópico se calcula en la granularidad de URL única y después se propaga al cluster filtrado. Sobre las **375 noticias** finales, la distribución observada es:

| Tópico | Noticias | Lectura principal |
|---:|---:|---|
| T0 | 30 | Oriente Medio / Israel / Gaza |
| T1 | 32 | India / BRICS / política internacional |
| T2 | 14 | Cuba / administración / negocio |
| T3 | 28 | EE.UU. institucional / Washington |
| T4 | 15 | Francia / Italia / Filipinas |
| T5 | 9 | Policía / Pakistán / administración local |
| T6 | 42 | Australia / Rusia / seguridad |
| T7 | 21 | Canadá / Irlanda / actividad militar y política |
| T8 | 24 | Nigeria / África / India |
| T9 | 6 | Corte / energía / justicia internacional |
| T10 | 40 | China / Irán / Trump / Taiwán |
| T11 | 45 | Reino Unido / política británica |
| T12 | 20 | Ucrania / Australia / internacional |
| T13 | 27 | EE.UU. local / salud / condados |
| T14 | 22 | EE.UU. local / policía / educación |

La mayor concentración se observa en T11, T6 y T10, seguidos de T1 y T0. Esto muestra que el LDA captura tanto ejes geopolíticos esperables (China-Irán-Taiwán, Oriente Medio, Ucrania) como ruido de actualidad local estadounidense y anglosajona. Por tanto, el tópico dominante es útil como descriptor complementario, pero debe tratarse como una variable auxiliar y no como una clasificación temática definitiva.

> 📊 **INSERTAR FIGURA X.6 — Distribución de noticias filtradas por tópico LDA.**
>
> Captura del gráfico generado en el notebook `desarrollo.ipynb`, sección §4.7 (última celda gráfica). Diagrama de barras del número de noticias del corpus filtrado asignadas a cada uno de los 15 tópicos LDA, con etiqueta de las 3 palabras más representativas de cada tópico bajo el eje horizontal. Permite verificar la concentración temática observada en los datos.

📄 **LISTADO X.9 — Entrenamiento y aplicación del LDA** (notebook §4.7).

```python
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Corpus: un documento por URL única
corpus_lda = df_all.drop_duplicates(subset="url_norm")["texto"].tolist()

# Stopwords combinadas: inglés + URL slug + palabras del etiquetado CAMEO
stop_cameo = set()
for frase in list(CAMEO_ROOT.values()) + list(QUAD_CLASS.values()):
    stop_cameo.update(frase.split())
stop_total = list(ENGLISH_STOP_WORDS | _STOP_SLUG | stop_cameo)

# Bag-of-words con vocabulario restringido
cv = CountVectorizer(stop_words=stop_total, min_df=10, max_df=0.5,
                     max_features=20000, token_pattern=r"[a-z]{3,}")
X_bow = cv.fit_transform(corpus_lda)

# Entrenamiento LDA online con k=15
K_LDA = 15
lda = LatentDirichletAllocation(n_components=K_LDA, learning_method="online",
                                random_state=0, max_iter=15, n_jobs=1)
doc_topic = lda.fit_transform(X_bow)

# Tópico dominante por URL y propagación a noticias filtradas
url_a_topico = pd.Series(doc_topic.argmax(axis=1),
                         index=df_all.drop_duplicates(subset="url_norm")["url_norm"])
texto_por_cluster = df_grafo.groupby("cluster_global").agg(
    url=("url_norm","first"), fecha=("fecha","first"), texto=("texto","first")
).reset_index()
texto_por_cluster["topico"] = texto_por_cluster["url"].map(url_a_topico)

dist_topicos = texto_por_cluster["topico"].value_counts().sort_index()
```

**Salida ilustrativa:**

```text
Documentos únicos para LDA: 60 140
Stopwords combinadas:           385
Matriz BoW: (60140, 7889)
Perplejidad: 2 239

TÓPICOS (top 12 palabras):
  T 0  ( 3 306 docs)  israel general media bank chief west gaza lebanon british arab israeli emirates
  T 1  ( 3 794 docs)  india delhi new pradesh minist governor senate colorado federal global michigan ece
  T 2  ( 2 003 docs)  business university day cuba administration oklahoma singapore travel kansas arrest tax
  T 3  ( 4 434 docs)  states united columbia district washington government house illinois american spain
  ...
  T10  ( 5 349 docs)  china iran trump beijing president london taiwan tehran chinese war says east
  T11  ( 4 345 docs)  united kingdom minister opinion louisiana congress georgia manchester tennessee voter prime
  T13  ( 6 499 docs)  states united new texas york florida county health north carolina zealand arizona

Distribución de tópicos sobre 375 noticias filtradas:
  T 0  30
  T 1  32
  T 2  14
  T 3  28
  T 4  15
  T 5   9
  T 6  42
  T 7  21
  T 8  24
  T 9   6
  T10  40
  T11  45
  T12  20
  T13  27
  T14  22
```

La perplejidad de 2 239 es razonable para un corpus de texto sintético corto, aunque no debe interpretarse como validación suficiente por sí sola. La inspección manual de los tópicos confirma que el modelo captura dimensiones geográficas y geopolíticas dominantes del periodo analizado (eje EEUU–China, Oriente Medio, África, política británica, EE.UU. local), validando su utilidad como *feature* complementaria para la fase de modelado.

### X.4.8 Tabla resumen del pipeline

Como cierre cuantitativo del bloque, se consolida en una única tabla el recorrido completo del corpus a lo largo de las etapas del pipeline. Esta tabla permite verificar de un vistazo la reducción acumulada y comparar el orden de magnitud de filas y noticias en cada paso.

| Etapa | Filas | Noticias | Reducción | Comentario |
|---|---:|---|---:|---|
| §3 Carga inicial | 319 345 | — | — | GDELT bruto, 3 días |
| §4.1 URL normalizada | 319 345 | — | 0 % | `SOURCEURL` íntegro |
| §4.3 Filtro slug ≥ 3 | 288 925 | 60 163 URLs | −9.5 % | Filtra URLs basura |
| §4.4 Clustering 0.80 | 288 925 | 51 294 clusters | — | Agrupa noticias semánticas |
| §4.6 K ≥ 5 + países_OR | 23 247 | 375 clusters | −92.7 % | Listo para GNN |

📄 **LISTADO X.10 — Generación de la tabla resumen** (notebook §4.8).

```python
filas_resumen = pd.DataFrame([
    {"Etapa": "§3 Carga inicial",
     "Filas": n_inicial_total,
     "Noticias": "—",
     "Reducción": "—"},
    {"Etapa": "§4.3 Filtro slug ≥ 3",
     "Filas": n_post_slug_total,
     "Noticias": f"{sum(r[2]['urls_unicas'] for r in resultados.values()):,} URLs",
     "Reducción": f"-{100*(n_inicial-n_post_slug)/n_inicial:.1f}%"},
    {"Etapa": "§4.4 Clustering 0.80",
     "Filas": n_post_slug_total,
     "Noticias": f"{sum(r[2]['n_clusters'] for r in resultados.values()):,} clusters",
     "Reducción": "—"},
    {"Etapa": "§4.6 K≥5 + paises_OR",
     "Filas": len(df_grafo),
     "Noticias": f"{df_grafo['cluster_global'].nunique():,} clusters",
     "Reducción": f"-{100*(n_inicial-len(df_grafo))/n_inicial:.1f}%"},
])
print(filas_resumen.to_string(index=False))
```

**Salida ilustrativa:**

```text
              Etapa     Filas              Noticias Reducción
   §3 Carga inicial   319 345                     —         —
§4.3 Filtro slug ≥3   288 925         60 163 URLs    -9.5 %
§4.4 Clustering 0.80  288 925       51 294 clusters       —
§4.6 K≥5 + paises_OR   23 247         375 clusters   -92.7 %
```

La tabla deja ver en una sola lectura el recorrido completo del corpus. La reducción global desde la carga inicial al conjunto final es de **−92.7 % en filas y de −99.3 % en clusters**, una compresión deliberadamente agresiva justificada por la necesidad de alimentar un grafo de tamaño moderado (20 nodos × 3 días) con señal informativa relevante en cada arista.

### X.4.9 Listado completo de noticias y veces vistas

La última operación del bloque produce, como artefacto final del tratamiento de datos, el **listado completo de las 375 noticias significativas** que componen el corpus final, ordenadas de mayor a menor cobertura mediática. Para cada noticia se reportan dos métricas complementarias:

- **Cobertura.** Número de URLs distintas que cubrieron la noticia en el corpus completo, antes del filtro de relevancia geopolítica. Es la métrica que se utilizó en el filtrado §4.6 (filtro A). Por construcción, todas las noticias del corpus tienen cobertura ≥ 5.
- **Filas.** Número de eventos GDELT (potenciales aristas del grafo) que esa noticia genera tras pasar el filtro completo (cluster ≥ 5 **y** algún actor en los nodos del acta).

Una noticia muy cubierta (cobertura alta) pero con pocas filas indica que solo una pequeña fracción de los eventos generados por la noticia involucra a los países del grafo. Una noticia con cobertura moderada y muchas filas, en cambio, indica que la noticia se distribuye entre varios pares Actor1-Actor2 dentro del conjunto de nodos.

A modo ilustrativo, las cinco noticias con mayor cobertura del periodo analizado son:

| # | Cobertura | Filas | Día | Noticia |
|---:|---:|---:|---|---|
| 1 | 459 | 3 645 | 14-may | Visita histórica China–Nixon evocada en relaciones Trump |
| 2 | 318 | 2 284 | 15-may | Beijing redefine relaciones bilaterales con EEUU |
| 3 | 192 | 371 | 16-may | Fuerzas EE.UU.–Nigeria eliminan líder de ISIS |
| 4 | 158 | 1 243 | 16-may | Controversia académicos chinos – Trump |
| 5 | 107 | 298 | 15-may | Brote hantavirus en crucero |

El listado completo de las 375 noticias se imprime en la última celda del notebook (§4.9) y queda disponible como referencia para la fase de modelado, donde cada cluster identificará un evento del grafo dinámico.

📄 **LISTADO X.11 — Generación del listado de noticias** (notebook §4.9).

```python
noticias_finales = (df_grafo.groupby("cluster_global")
                    .agg(n_filas=("GLOBALEVENTID", "size"),
                         fecha=("fecha", "first"),
                         texto=("texto", "first"))
                    .reset_index())

# Cobertura = tamaño original del cluster en df_all
noticias_finales["cobertura"] = noticias_finales["cluster_global"].map(tam_cluster)
noticias_finales = (noticias_finales
                    .sort_values("cobertura", ascending=False)
                    .reset_index(drop=True))

for i, row in noticias_finales.iterrows():
    print(f"{i+1:>4}  {row['cobertura']:>4}  {row['n_filas']:>6}  "
          f"{row['fecha']:>10}  {row['texto'][:110]}")
```

**Salida ilustrativa** (primeras y últimas filas del listado de 375):

```text
Total de noticias en el corpus filtrado: 375

   #  Cobertura   Filas         Día  Noticia
---------------------------------------------------------------------------------------------------
   1        459    3645    20260514  china visits nixon trump china united states make public statement
   2        318    2284    20260515  while trump sought business deals beijing came prepared redefine
   3        192     371    20260516  nigerian forces eliminate top isis leader abu bilal minuki africa
   4        158    1243    20260516  trump chinese scholars controversy china china appeal verbal
   5        107     298    20260515  reports hantavirus cases cruise outbreak united states australia
   6         93     257    20260515  cuba cia chief trump message cuba the white house havana
   7         85     311    20260515  jury resumes deliberations weinstein rape retrial lawyer united
   8         79     301    20260516  middle east gaza airstrike targeted hamas military wing leader
   ...
 372          5      36    20260516  passenger hantavirus cruise quarantines taiwan new zealand taiwan
 373          5       5    20260516  katie price marriage concerns lee andrews united kingdom dubai
 374          5      25    20260516  keir starmer stand aside andy burnham wes streeting deputy
 375          5      22    20260514  irans calls brics unequivocally condemn violations international
```

El listado se abre con las noticias más cubiertas —dominadas por la relación EEUU–China, los conflictos de Oriente Medio y eventos sanitarios de alcance internacional— y se cierra con la cota mínima del filtro de cobertura (`5`), confirmando por construcción la homogeneidad del corpus producido.

---

## Síntesis del capítulo

El bloque de obtención y limpieza de datos produce, sobre cada fichero diario de GDELT 1.0, un DataFrame con texto sintético por evento, URL canónica, identificador de cluster temático y todas las columnas relevantes del codebook. Los principales hallazgos cuantitativos sobre el día analizado se resumen en la siguiente tabla:

| Etapa | Filas | Reducción | Observación |
|---|---:|---:|---|
| Carga | 118 201 | — | Volumen típico de un día completo |
| Normalización URL | 118 201 | 0 % | `SOURCEURL` íntegro |
| URLs únicas (X.4.2) | 24 412 (URLs) | 4.84× inflación | Mediana 3 ocurrencias |
| Filtro de slug (X.4.3) | 107 248 | 9.3 % descartadas | Elimina URLs basura |
| URLs únicas tras filtro | 22 572 (URLs) | — | Base para embeddings |
| Clustering (X.4.4) | 19 423 clusters | — | 94 % singletons |
| Validación cruzada (X.4.6) | 3 días | varianza < 1 pp | Pipeline estable día a día |
| Filtrado dirigido (X.4.6) | 23 247 | ~375 clusters | K≥5 + países_OR — listo para GNN |

Estos números fundamentan las decisiones que se toman en el capítulo siguiente, dedicado al análisis exploratorio y al filtrado de modelado (selección final de nodos país, umbral de `NumMentions`, elección entre `QuadClass` y `EventRootCode` como tipado de aristas).

---

*Documento generado a partir del notebook `desarrollo.ipynb` el 20-may-2026 en la sesión de implementación del TFM. Las cifras corresponden a la ejecución sobre `data/raw/20260515.export.CSV`. Para otro día o rango, los números se actualizan re-ejecutando el notebook.*
