"""Diagrama de bloques de la arquitectura del sistema (Figura X del capítulo 1)."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


COLOR_INPUT = "#DDE7F2"
COLOR_GRAFO = "#F7E1B5"
COLOR_MODELO = "#E6D3EC"
COLOR_EMB = "#D6ECD2"
COLOR_HEAD = "#F5C6C6"
COLOR_EDGE = "#333333"
COLOR_TEXT = "#111111"
COLOR_LOOP = "#B84A3A"


def box(ax, cx, cy, w, h, title, body, color):
    x = cx - w / 2
    y = cy - h / 2
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=1.1, edgecolor=COLOR_EDGE, facecolor=color,
        )
    )
    # Bloque título + cuerpo centrado en el eje vertical de la caja
    body_lines = body.count("\n") + 1
    body_h = body_lines * 0.18
    gap = 0.14
    total_h = 0.26 + gap + body_h
    top = cy + total_h / 2

    ax.text(cx, top, title,
            ha="center", va="top", fontsize=12,
            fontweight="bold", color=COLOR_TEXT)
    ax.text(cx, top - 0.26 - gap, body,
            ha="center", va="top", fontsize=10,
            color=COLOR_TEXT, linespacing=1.4)


def arrow(ax, x1, y1, x2, y2, curve=0.0, lw=1.1, color=None, dashed=False):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=10,
            linewidth=lw, color=color or COLOR_EDGE,
            connectionstyle=f"arc3,rad={curve}",
            linestyle=(0, (4, 2)) if dashed else "-",
        )
    )


def main():
    fig, ax = plt.subplots(figsize=(16, 5.2))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    y_c = 2.4

    # Columna 1 · Entradas (2 cajas apiladas)
    box(ax, 1.55, 3.45, 2.7, 1.4, "GDELT 1.0",
        "Eventos geopolíticos", COLOR_INPUT)
    box(ax, 1.55, 1.55, 2.7, 1.4, "S&P 500 + macro",
        "Cotización + VIX + tipos", COLOR_INPUT)

    # Columna 2 · Grafo
    box(ax, 5.0, y_c, 3.0, 3.3, "Grafo heterogéneo",
        "20 países + mercado\nMemoria decay", COLOR_GRAFO)

    # Columna 3 · Modelo
    box(ax, 8.3, y_c, 2.7, 3.3, "HeteroGAT · GATv2",
        "2 capas · 4 cabezas", COLOR_MODELO)

    # Columna 4 · Embedding
    box(ax, 11.1, y_c, 2.4, 3.3, "Vector mercado",
        "64 dimensiones", COLOR_EMB)

    # Columna 5 · Predicción
    box(ax, 14.15, y_c, 3.0, 3.3, "Cabeza MLP",
        "↑ subida\n= neutralidad\n↓ bajada",
        COLOR_HEAD)

    # Flechas horizontales
    arrow(ax, 2.95, 3.45, 3.55, y_c + 0.6, lw=1.4)
    arrow(ax, 2.95, 1.55, 3.55, y_c - 0.6, lw=1.4)
    arrow(ax, 6.55, y_c, 6.90, y_c, lw=1.4)
    arrow(ax, 9.70, y_c, 9.85, y_c, lw=1.4)
    arrow(ax, 12.35, y_c, 12.60, y_c, lw=1.4)

    # Bucle temporal encima del grafo
    ax.add_patch(FancyArrowPatch(
        (3.75, 4.35), (6.25, 4.35),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.4, color=COLOR_LOOP,
        connectionstyle="arc3,rad=-0.5",
        linestyle=(0, (5, 3)),
    ))
    ax.text(5.0, 4.9, "día t → t+1 · refuerzo + decay",
            ha="center", va="center", fontsize=11,
            style="italic", color=COLOR_LOOP)

    # Pie
    ax.text(8.0, 0.28,
            "Figura 1. Arquitectura del sistema: GDELT + datos financieros → grafo persistente con decay → "
            "HeteroGAT (GATv2) → vector del nodo mercado → clasificación triclase del S&P 500 en t+1. "
            "Fuente: Elaboración propia.",
            ha="center", va="center", fontsize=10, color=COLOR_TEXT)

    fig.tight_layout()
    out = Path("docs/figuras/arquitectura_sistema.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=260, bbox_inches="tight", facecolor="white")
    print(f"Guardado en {out}")


if __name__ == "__main__":
    main()
