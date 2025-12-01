from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import matplotlib.pyplot as plt

from .attacks import compute_attack_order


class DynamicState:
    """
    Container for the state of a graph at a given removal fraction.
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
    Compute the sequence of failure states for a graph and attack.

    Returns:
      - positions: fixed node layout (spring_layout)
      - states: list of DynamicState objects
    """
    original_n = graph.number_of_nodes()
    if original_n == 0:
        return {}, []

    positions = nx.spring_layout(graph, seed=seed)  # fixes Layout für alle Schritte
    node_order = compute_attack_order(graph, attack_cfg, seed=seed)

    states: List[DynamicState] = []
    for frac in fractions:
        frac_clamped = max(0.0, min(1.0, float(frac)))
        k = int(round(frac_clamped * original_n))  # Anzahl zu entfernender Knoten
        k = min(k, original_n)
        failed_nodes = set(node_order[:k])
        states.append(DynamicState(fraction=frac_clamped, failed_nodes=failed_nodes))

    return positions, states


def draw_graph_state(
    graph: nx.Graph,
    positions: Dict[Any, Tuple[float, float]],
    state: DynamicState,
    highlight_gcc: bool = True,
) -> plt.Figure:
    """
    Draw the graph for a specific failure state.

    - active nodes: light blue
    - failed nodes: red
    - GCC among active nodes: darker blue
    """
    failed = state.failed_nodes
    active = [n for n in graph.nodes() if n not in failed]  # verbleibende Knoten

    gcc_nodes: set[Any] = set()
    if highlight_gcc and active:
        sub = graph.subgraph(active)
        components = list(nx.connected_components(sub))
        if components:
            gcc_nodes = set(max(components, key=len))

    node_colors = []
    node_sizes = []
    for n in graph.nodes():
        if n in failed:
            node_colors.append("tab:red")
            node_sizes.append(15)
        elif n in gcc_nodes:
            node_colors.append("tab:blue")
            node_sizes.append(25)
        else:
            node_colors.append("lightskyblue")
            node_sizes.append(15)

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
