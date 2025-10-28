from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
import numpy as np
import networkx as nx


def _largest_component(G: nx.Graph) -> Optional[nx.Graph]:
    if G.number_of_nodes() == 0:
        return None
    components = list(nx.connected_components(G))
    if not components:
        return None
    largest_nodes = max(components, key=len)
    return G.subgraph(largest_nodes).copy()


def lcc_fraction(G: nx.Graph, n0: int) -> float:
    """Größe der größten verbundenen Komponente geteilt durch die anfängliche Knotenzahl n0."""
    if n0 <= 0:
        return 0.0
    if G.number_of_nodes() == 0:
        return 0.0
    L = _largest_component(G)
    return (L.number_of_nodes() / n0) if L is not None else 0.0


def avg_path_length_lcc(G: nx.Graph) -> float:
    """Mittlere kürzeste Pfadlänge auf der größten verbundenen Komponente.
    Gibt NaN zurück für Graphen mit < 2 Knoten in der LCC oder wenn nicht definiert.
    """
    if G.number_of_nodes() < 2:
        return math.nan
    L = _largest_component(G)
    if L is None or L.number_of_nodes() < 2:
        return math.nan
    try:
        return nx.average_shortest_path_length(L)
    except Exception:
        return math.nan


def global_efficiency(G: nx.Graph) -> float:
    try:
        return nx.global_efficiency(G)
    except Exception:
        return math.nan


def compute_metrics(G: nx.Graph, n0: int) -> Dict[str, float]:
    return {
        "lcc_frac": lcc_fraction(G, n0),
        "avg_path_length": avg_path_length_lcc(G),
        "global_efficiency": global_efficiency(G),
    }


def auc_trapz(xs: np.ndarray, ys: np.ndarray) -> float:
    if len(xs) < 2:
        return 0.0
    return float(np.trapz(ys, xs))


def critical_fraction(xs: np.ndarray, ys: np.ndarray, threshold: float = 0.5) -> float:
    """Kleinstes x, bei dem y <= Schwellwert; lineare Interpolation zwischen Stützstellen.
    Gibt 1.0 zurück, falls keine Unterschreitung auftritt.
    """
    if len(xs) == 0:
        return 1.0
    # Ensure sorted by xs
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    below = ys <= threshold
    if not below.any():
        return 1.0
    idx = np.argmax(below)  # first True index
    if ys[idx] == threshold or idx == 0:
        return float(xs[idx])
    # interpolate between (idx-1) and idx
    x0, y0 = xs[idx - 1], ys[idx - 1]
    x1, y1 = xs[idx], ys[idx]
    if y1 == y0:
        return float(x1)
    t = (threshold - y0) / (y1 - y0)
    return float(x0 + t * (x1 - x0))
