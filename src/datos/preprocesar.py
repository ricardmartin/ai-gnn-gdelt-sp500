"""Preprocesamiento de GDELT 1.0: de eventos brutos a `df_grafo`.

Normalizacion de URL, texto sintetico por evento, clustering semantico por dia
(via cache de embeddings) y filtrado dirigido al grafo (cobertura + roster de
paises). La lectura de ficheros vive en `cargar.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .cargar import cargar_dia

# 4.3  Etiquetas CAMEO usadas para el texto sintetico
CAMEO_ROOT = {
    "01": "make public statement", "02": "appeal",
    "03": "express intent to cooperate", "04": "consult",
    "05": "engage in diplomatic cooperation",
    "06": "engage in material cooperation", "07": "provide aid",
    "08": "yield", "09": "investigate", "10": "demand",
    "11": "disapprove", "12": "reject", "13": "threaten", "14": "protest",
    "15": "exhibit force posture", "16": "reduce relations", "17": "coerce",
    "18": "assault", "19": "fight", "20": "use unconventional mass violence",
}
QUAD_CLASS = {
    "1": "verbal cooperation", "2": "material cooperation",
    "3": "verbal conflict", "4": "material conflict",
}
_STOP_SLUG = {
    "news", "article", "articles", "story", "stories", "post", "posts",
    "details", "detail", "index", "html", "htm", "php", "asp", "aspx",
    "amp", "www", "com", "org", "net", "the", "and", "for", "with",
    "from", "national", "world", "politics", "local", "latest", "video",
    "live", "breaking", "update", "updates", "content", "page", "default",
}

# Roster fijo de paises-nodo (notebook 4.6). Indices estables entre snapshots.
NODOS_ACTA = {
    "USA", "CAN", "MEX", "BRA", "EUR",
    "DEU", "FRA", "GBR",
    "CHN", "JPN", "KOR", "IND", "TWN",
    "RUS", "SAU", "IRN", "ISR", "TUR",
    "AUS", "PRK",
}

_RE_PUERTO = re.compile(r":(80|443)(?=/|$)")
_RE_QUERY = re.compile(r"[?#].*$")
_RE_HEX = re.compile(r"^[0-9a-f]{6,}$", re.I)
_RE_TIENE_DIGITO = re.compile(r"\d")
_RE_HOST = re.compile(r"^https?://([^/]+)(.*)$", re.I)


# --------------------------------------------------------------------------- #
# 4.1  Normalizacion de URL
# --------------------------------------------------------------------------- #
def normalizar_url(u):
    """URL canonica: host en minusculas, sin puerto estandar ni query/fragment."""
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


# --------------------------------------------------------------------------- #
# 4.3  Texto sintetico por evento
# --------------------------------------------------------------------------- #
def slug_tokens(url):
    """Tokens legibles del path de la URL: lo mas cercano a un 'titular'."""
    if not url:
        return ""
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
    """Concat de actores + ubicacion + etiqueta CAMEO + QuadClass, en minusculas."""
    partes = []
    for c in ("Actor1Name", "Actor2Name", "ActionGeo_FullName"):
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            partes.append(v.lower())
    root = str(row.get("EventRootCode") or "").zfill(2)
    partes.append(CAMEO_ROOT.get(root, ""))
    partes.append(QUAD_CLASS.get(str(row.get("QuadClass") or ""), ""))
    return " ".join(p for p in partes if p)


# --------------------------------------------------------------------------- #
# 4.5  Procesado completo de un dia (4.1-4.4)
# --------------------------------------------------------------------------- #
def procesar_dia(path, modelo_st=None, umbral=0.80, vecinos=15, data_dir="data"):
    """Aplica 4.1-4.4 a un fichero y devuelve (df, texto_por_url, metricas).

    Si existe la cache de embeddings del dia no se usa `modelo_st` (puede ser None).
    """
    from sklearn.neighbors import NearestNeighbors
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components

    fecha = Path(path).name[:8]
    df_d = cargar_dia(path)
    n_inicial = len(df_d)

    # 4.1 normalizacion URL
    df_d["url_norm"] = df_d["SOURCEURL"].map(normalizar_url)
    n_url_invalida = int(df_d["url_norm"].isna().sum())
    df_d = df_d[df_d["url_norm"].notna()].reset_index(drop=True)

    # 4.3 texto sintetico + filtro slug
    df_d["slug"] = df_d["url_norm"].map(slug_tokens)
    df_d["n_slug"] = df_d["slug"].str.split().map(len)
    df_d = df_d[df_d["n_slug"] >= 3].copy()
    df_d["meta"] = df_d.apply(metadatos_evento, axis=1)
    df_d["texto"] = (
        (df_d["slug"] + " " + df_d["meta"])
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df_d = df_d.drop(columns=["n_slug"]).reset_index(drop=True)
    n_post_slug = len(df_d)
    pct_descarte = 100 * (n_inicial - n_url_invalida - n_post_slug) / max(n_inicial - n_url_invalida, 1)

    # 4.4 embeddings (cache por dia) + clustering por componentes conexas
    tpu = df_d.groupby("url_norm", as_index=False)["texto"].first()
    cache = Path(data_dir) / f"embeddings_url_{fecha}.npy"
    if cache.exists():
        emb_d = np.load(cache)
    else:
        if modelo_st is None:
            raise FileNotFoundError(
                f"No hay cache {cache} y no se ha pasado modelo_st para calcularla."
            )
        emb_d = modelo_st.encode(
            tpu["texto"].tolist(), normalize_embeddings=True,
            show_progress_bar=False, batch_size=128,
        )
        emb_d = np.asarray(emb_d, dtype="float32")
        np.save(cache, emb_d)

    n_d = len(emb_d)
    nn_d = NearestNeighbors(n_neighbors=min(vecinos, n_d), metric="cosine").fit(emb_d)
    dist_d, idx_d = nn_d.kneighbors(emb_d)
    fil, col = [], []
    lim = 1.0 - umbral
    for i in range(n_d):
        for d, j in zip(dist_d[i], idx_d[i]):
            if i != j and d <= lim:
                fil.append(i); col.append(j)
    if fil:
        g_d = csr_matrix((np.ones(len(fil)), (fil, col)), shape=(n_d, n_d))
        _, etiq = connected_components(g_d, directed=False)
    else:
        etiq = np.arange(n_d)
    tpu["cluster"] = etiq
    tam = tpu["cluster"].value_counts()

    metricas = {
        "fecha": fecha,
        "filas_iniciales": n_inicial,
        "urls_invalidas": n_url_invalida,
        "filas_post_slug": n_post_slug,
        "pct_descarte_slug": pct_descarte,
        "urls_unicas": len(tpu),
        "factor_inflacion": n_post_slug / max(len(tpu), 1),
        "n_clusters": int(len(tam)),
        "pct_singletons": 100 * (tam == 1).sum() / max(len(tam), 1),
        "max_cluster": int(tam.max()),
    }
    return df_d, tpu, metricas


# --------------------------------------------------------------------------- #
# 4.6  Filtrado dirigido al grafo -> df_grafo
# --------------------------------------------------------------------------- #
def construir_df_grafo(resultados: dict, k_min: int = 5, roster=NODOS_ACTA):
    """Concatena los dias procesados y aplica los filtros A (cobertura) y B (paises).

    `resultados` es {fecha: (df_d, tpu, metricas)} tal como devuelve `procesar_dia`.
    Devuelve (df_grafo, tam_cluster).
    """
    trozos = []
    for fecha_d, (df_d, tpu_d, _) in resultados.items():
        df_m = df_d.merge(tpu_d[["url_norm", "cluster"]], on="url_norm", how="left")
        df_m = df_m.assign(
            fecha=fecha_d,
            cluster_global=fecha_d + "_" + df_m["cluster"].astype(str),
        )
        trozos.append(df_m)
    df_all = pd.concat(trozos, ignore_index=True)

    tam_cluster = df_all.groupby("cluster_global")["url_norm"].nunique()
    clusters_validos = set(tam_cluster[tam_cluster >= k_min].index)

    mask_A = df_all["cluster_global"].isin(clusters_validos)
    mask_B = (
        df_all["Actor1CountryCode"].isin(roster)
        | df_all["Actor2CountryCode"].isin(roster)
    )
    df_grafo = df_all[mask_A & mask_B].copy().reset_index(drop=True)
    return df_grafo, tam_cluster


def reproducir_df_grafo(raw_dir="data/raw", data_dir="data", k_min=5, patron="*.export.CSV"):
    """Reconstruye `df_grafo` desde los CSV diarios usando la cache de embeddings.

    `patron` permite restringir los dias (p. ej. '2022*.export.CSV' para un experimento).
    """
    paths = sorted(Path(raw_dir).glob(patron))
    resultados = {}
    for p in paths:
        df_d, tpu, met = procesar_dia(str(p), modelo_st=None, data_dir=data_dir)
        resultados[met["fecha"]] = (df_d, tpu, met)
    return construir_df_grafo(resultados, k_min=k_min)
