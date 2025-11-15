from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import matplotlib.pyplot as plt

from .attacks import compute_attack_order


class DynamicState:
    """
    Kleiner Container für den Zustand des Graphen in einem bestimmten Schritt.
    """
    def __init__(self, fraction: float, failed_nodes: Set[int]):
        self.fraction = float(fraction)
        self.failed_nodes = set(failed_nodes)


def compute_dynamic_states(
    graph: nx.Graph,
    attack_cfg: Dict[str, Any],
    fractions: List[float],
    seed: int | None = None,
) -> Tuple[Dict[Any, Tuple[float, float]], List[DynamicState]]:
    """
    Berechne die Abfolge von Ausfallzuständen für einen Graphen
    und ein Angriffsszenario.

    Rückgabe:
      - positions: Layout-Positionen für alle Knoten (spring_layout)
      - states: Liste von DynamicState (für jeden Fraction-Schritt)
    """
    original_n = graph.number_of_nodes()
    if original_n == 0:
        return {}, []

    # Layout einmal berechnen, damit sich der Graph nicht „zuckend“ verschiebt
    positions = nx.spring_layout(graph, seed=seed)

    node_order = compute_attack_order(graph, attack_cfg, seed=seed)

    states: List[DynamicState] = []
    for frac in fractions:
        frac_clamped = max(0.0, min(1.0, float(frac)))
        k = int(round(frac_clamped * original_n))
        k = min(k, original_n)
        failed_nodes = set(node_order[:k])
        states.append(DynamicState(fraction=frac_clamped, failed_nodes=failed_nodes))

    return positions, states


def draw_graph_state(
    graph: nx.Graph,
    positions: Dict[Any, Tuple[float, float]],
    state: DynamicState,
    highlight_lcc: bool = True,
) -> plt.Figure:
    """
    Zeichne den Graphen für einen bestimmten Ausfallzustand.

    - aktive Knoten: blau
    - ausgefallene Knoten: rot
    - optional: größte verbundene Komponente der aktiven Knoten wird dunkler hervorgehoben
    """
    failed = state.failed_nodes
    active = [n for n in graph.nodes() if n not in failed]

    # LCC der aktiven Knoten bestimmen (optional)
    lcc_nodes: set[Any] = set()
    if highlight_lcc and active:
        sub = graph.subgraph(active)
        components = list(nx.connected_components(sub))
        if components:
            lcc_nodes = set(max(components, key=len))

    node_colors = []
    node_sizes = []
    for n in graph.nodes():
        if n in failed:
            node_colors.append("tab:red")
            node_sizes.append(50)
        elif n in lcc_nodes:
            node_colors.append("tab:blue")
            node_sizes.append(80)
        else:
            node_colors.append("lightskyblue")
            node_sizes.append(50)

    # Kanten: nur Kanten zeichnen, deren Endpunkte noch aktiv sind
    active_edges = [(u, v) for (u, v) in graph.edges() if u not in failed and v not in failed]

    fig, ax = plt.subplots()
    nx.draw_networkx_nodes(
        graph,
        pos=positions,
        nodelist=list(graph.nodes()),
        node_color=node_colors,
        node_size=node_sizes,
        ax=ax,
    )
    nx.draw_networkx_edges(
        graph,
        pos=positions,
        edgelist=active_edges,
        width=0.8,
        alpha=0.8,
        ax=ax,
    )
    ax.set_title(f"Fraction removed: {state.fraction:.2f}")
    ax.axis("off")
    fig.tight_layout()
    return fig
