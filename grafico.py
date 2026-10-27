# -*- coding: utf-8 -*-
"""
grafico.py  --  Grupo 7 (IO1-82)

Dibuja la gráfica del método gráfico: cada restricción como recta, la región
factible sombreada, los vértices con su valor de z y el óptimo marcado.
Solo dibuja; no resuelve nada (la solución viene de metodo_grafico.py).
"""
from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from metodo_grafico import Problema, Resultado


def _limites(p: Problema, res: Resultado):
    """Tamaño de la ventana: abarca vértices e interceptos de las rectas."""
    xs, ys = [0.0], [0.0]
    for v in res.vertices:
        xs.append(v.x1)
        ys.append(v.x2)
    for r in p.restricciones:
        if r.a1 != 0 and r.b / r.a1 > 0:
            xs.append(r.b / r.a1)
        if r.a2 != 0 and r.b / r.a2 > 0:
            ys.append(r.b / r.a2)
    factor = 1.5 if res.estado == "no_acotado" else 1.25
    xmax = max(xs) * factor or 10.0
    ymax = max(ys) * factor or 10.0
    return xmax, ymax


def dibujar(p: Problema, res: Resultado) -> Figure:
    """Devuelve una figura de matplotlib lista para mostrar en la interfaz."""
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    xmax, ymax = _limites(p, res)

    # --- Región factible (sombreada) -------------------------------------
    hay_igualdad = any(r.signo == "=" for r in p.restricciones)
    if not hay_igualdad:
        X, Y = np.meshgrid(np.linspace(0, xmax, 500), np.linspace(0, ymax, 500))
        mascara = np.ones_like(X, dtype=bool)
        for r in p.restricciones:
            V = r.a1 * X + r.a2 * Y
            tol = 1e-7 * (1 + abs(r.b))
            mascara &= (V <= r.b + tol) if r.signo == "<=" else (V >= r.b - tol)
        if mascara.any():
            ax.contourf(X, Y, mascara.astype(float), levels=[0.5, 1.5],
                        colors=["#2e9d5b"], alpha=0.25)
    elif res.vertices:
        # Con una igualdad la región es un segmento: se dibuja entre sus vértices
        pts = sorted((v.x1, v.x2) for v in res.vertices)
        ax.plot([q[0] for q in pts], [q[1] for q in pts], color="#2e9d5b",
                linewidth=5, alpha=0.5, label="Región factible")

    # --- Una recta por cada restricción ----------------------------------
    colores = ["#1f77b4", "#d62728", "#9467bd", "#8c564b",
               "#e377c2", "#17becf", "#bcbd22", "#ff7f0e"]
    for i, r in enumerate(p.restricciones):
        color = colores[i % len(colores)]
        etiqueta = f"{r.nombre}: {r.a1:g}x1 + {r.a2:g}x2 {r.signo} {r.b:g}"
        if r.a2 != 0:
            xx = np.array([0.0, xmax])
            ax.plot(xx, (r.b - r.a1 * xx) / r.a2, color=color, label=etiqueta)
        else:
            ax.axvline(r.b / r.a1, color=color, label=etiqueta)

    # --- Vértices con su valor de z --------------------------------------
    for v in res.vertices:
        ax.plot(v.x1, v.x2, "o", color="black", markersize=5, zorder=5)
        ax.annotate(f"({v.x1:.3g}; {v.x2:.3g})\nz = {v.z:.4g}", (v.x1, v.x2),
                    textcoords="offset points", xytext=(6, 6), fontsize=8)

    # --- Óptimo marcado y recta de z -------------------------------------
    for v in res.optimos:
        ax.plot(v.x1, v.x2, "*", color="gold", markeredgecolor="black",
                markersize=18, zorder=6, label="Óptimo" if v is res.optimos[0] else None)
    if res.optimos:
        z = res.z_optimo
        if p.c2 != 0:
            xx = np.array([0.0, xmax])
            ax.plot(xx, (z - p.c1 * xx) / p.c2, "k--", linewidth=1,
                    label=f"z = {z:.4g}")
        else:
            ax.axvline(z / p.c1, color="k", linestyle="--", linewidth=1)

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    u1 = f" ({p.unidad_x1})" if p.unidad_x1 else ""
    u2 = f" ({p.unidad_x2})" if p.unidad_x2 else ""
    ax.set_xlabel(f"x1 = {p.nombre_x1}{u1}")
    ax.set_ylabel(f"x2 = {p.nombre_x2}{u2}")
    ax.set_title("Método gráfico: región factible y óptimo")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    return fig
