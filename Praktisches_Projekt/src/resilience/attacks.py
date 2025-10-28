from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Iterable
import random
import numpy as np
import networkx as nx

from .metrics import compute_metrics


def _removal_sequence_random(G: nx.Graph, seed: Optional[int]) -> List[int]:
    nodes = list(G.nodes())
    rng = np.random.default_rng(seed)
    rng.shuffle(nodes)
    return nodes


def _select_node_by_degree(G: nx.Graph) -> int:
    # Wählt den Knoten mit maximalem Grad (bei Gleichstand beliebig)
    node, _ = max(G.degree, key=lambda kv: kv[1])
    return node


def _select_node_by_betweenness(G: nx.Graph) -> int:
    bc = nx.betweenness_centrality(G)
    # Wählt den Knoten mit der höchsten Zwischenzentralität
    node = max(bc.items(), key=lambda kv: kv[1])[0]
    return node


def simulate_progressive_node_removal(
    G0: nx.Graph,
    strategy: str,
    step: float = 0.02,
    seed: Optional[int] = None,
    recompute_each_step: bool = True,
) -> List[Dict]:
    """
    Entfernt Knoten schrittweise und protokolliert Metriken bei regelmäßigen Entfernungsanteilen.
    Gibt eine Liste von Zeilen (Dicts) zurück mit: fraction_removed, lcc_frac, avg_path_length, global_efficiency, removed_count.

    Strategien:
      - 'random': zufällige Reihenfolge
      - 'degree': in jedem Schritt Knoten mit höchstem Grad entfernen (adaptiv)
      - 'betweenness': in jedem Schritt Knoten mit höchster Zwischenzentralität entfernen (adaptiv)
    """
    G = G0.copy()
    n0 = G.number_of_nodes()
    if n0 == 0:
        return []

    # Entfernungsplan aufbauen
    if strategy == "random":
        order = _removal_sequence_random(G, seed)
        adaptive = False
    elif strategy == "degree":
        order = []
        adaptive = True
    elif strategy == "betweenness":
        order = []
        adaptive = True
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    targets = list(np.round(np.arange(0, 1 + 1e-9, step) * n0).astype(int))
    targets = sorted(set(targets))  # unique and sorted
    next_target_idx = 0
    removed = 0

    rows: List[Dict] = []

    # Basiswert protokollieren (0 entfernt)
    rows.append({
        "fraction_removed": 0.0,
        "removed_count": 0,
        **compute_metrics(G, n0),
    })

    while G.number_of_nodes() > 0:
    # Nächsten zu entfernenden Knoten bestimmen
        if adaptive:
            if strategy == "degree":
                node = _select_node_by_degree(G)
            else:  # Zwischenzentralität
                node = _select_node_by_betweenness(G)
        else:
            node = order[removed]

        if node not in G:
            # Sollte nicht vorkommen; falls doch, wähle irgendeinen vorhandenen Knoten
            node = next(iter(G.nodes()))
        G.remove_node(node)
        removed += 1

    # Zielschritt erreicht/überschritten? Dann Messwerte protokollieren
        while next_target_idx < len(targets) and removed >= targets[next_target_idx]:
            frac = removed / n0
            rows.append({
                "fraction_removed": float(frac),
                "removed_count": removed,
                **compute_metrics(G, n0),
            })
            next_target_idx += 1

        if removed >= n0:
            break

    return rows
