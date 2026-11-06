"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import rte_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, placed=None, chain=None, title_prefix="Route"):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route des Splits eine Farbe.

    `placed`: nur diese Kunden sind schon gesetzt (die übrigen blass, Experiment 1); `chain`: die Folge als gestrichelte graue Linie Depot - Folge - Depot.
    Gleicher Maßstab in x und y über scaleanchor mit autorange; der Rand kommt von zwei unsichtbaren Eckmarken (DEMO-PLAYBOOK §3)."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    placed_set = set(range(1, inst.n + 1)) if placed is None else set(placed)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    if chain:
        pts = [inst.xy[0]] + [inst.xy[c] for c in chain] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color="rgba(120,120,120,0.55)", width=2, dash="dot"),
                                 name="Folge (Rundreise)", hoverinfo="skip"))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color=["rgba(150,150,150,0.55)" if c in placed_set else "rgba(150,150,150,0.12)" for c in customers],
                    line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 400)


def build_scatter(data, marks):
    """Länge der Rundreise (x) gegen Split-Kosten (y) für eine Stichprobe aller Reihenfolgen; `marks`: Liste (Name, Länge, Split, Farbe, Symbol) der Erzeuger und der kürzesten Rundreise."""
    fig = go.Figure(go.Scattergl(x=np.asarray(data["sample_length"]), y=np.asarray(data["sample_cost"]), mode="markers", marker=dict(size=4, color=C.COLOR_OTHER),
                                 hovertemplate="Länge %{x:.1f}, Split %{y:.1f}<extra></extra>", name="Reihenfolgen (Stichprobe)"))
    fig.add_hline(y=data["optimum"], line=dict(color=C.COLOR_OPT, width=2, dash="dash"), annotation_text=f"Optimum {data['optimum']:.2f}", annotation_position="top right")
    for name, length, split, color, symbol in marks:
        fig.add_trace(go.Scatter(x=[length], y=[split], mode="markers", marker=dict(size=13, color=color, symbol=symbol, line=dict(color="#222", width=1)), name=name,
                                 hovertemplate=f"{name}: Länge %{{x:.2f}}, Split %{{y:.2f}}<extra></extra>"))
    fig.update_xaxes(title_text="Länge der Rundreise Depot – Folge – Depot")
    fig.update_yaxes(title_text="Kosten nach dem Split")
    fig = _base(fig, 520)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), margin=dict(l=10, r=10, t=10, b=10))   # die Legende hat vier Zeilen: Platz unter dem Achsentitel
    return fig


def build_bands(by_key):
    """Median des Abstands zum Optimum (zur Referenz) je Erzeuger, mit Spanne (Minimum bis Maximum) als Fehlerbalken."""
    keys = list(C.KEYS)
    fig = go.Figure(go.Bar(
        x=[C.NAMES[k] for k in keys], y=[by_key[k]["median"] for k in keys], marker_color=[C.KEY_COLORS[k] for k in keys],
        error_y=dict(type="data", symmetric=False, array=[by_key[k]["max"] - by_key[k]["median"] for k in keys], arrayminus=[by_key[k]["median"] - by_key[k]["min"] for k in keys]),
        hovertemplate="%{x}: Median %{y:.1f} %<extra></extra>", name="Median (Balken: Minimum bis Maximum)"))
    fig.update_yaxes(title_text="Abstand (%)", rangemode="tozero")
    return _base(fig, 360)
