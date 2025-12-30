from __future__ import annotations

from typing import List, Dict, Any
import random

import networkx as nx


def compute_attack_order(
    graph: nx.Graph,
    attack_cfg: Dict[str, Any],
    seed: int | None = None,
) -> List[int]:
    """
    Compute an ordered list of nodes to remove according to an attack scenario.

    attack_cfg:
      - type: 'random' or 'targeted'
      - strategy (for targeted): 'degree' or 'betweenness'
    """
    atype = attack_cfg.get("type", "").lower()
    nodes = list(graph.nodes())

    if atype == "random":
        # Zufällige Reihenfolge der zu entfernenden Knoten
        rng = random.Random(seed)
        rng.shuffle(nodes)
        return nodes

    if atype == "targeted":
        strategy = attack_cfg.get("strategy", "").lower()
        if strategy == "degree":
            # Höchster Grad zuerst
            centrality = dict(graph.degree())
        elif strategy == "betweenness":
            # Vermittlerknoten priorisieren (ggf. Sampling)
            centrality = _betweenness_centrality_robust(graph)
        else:
            raise ValueError(f"Unknown targeted strategy: {strategy}")

        ordered = sorted(centrality.items(), key=lambda kv: (-kv[1], kv[0]))
        return [node for node, _ in ordered]

    raise ValueError(f"Unknown attack type: {atype}")


def _betweenness_centrality_robust(graph: nx.Graph) -> Dict[int, float]:
    """
    Compute betweenness centrality in a way that is more robust for larger graphs.

    - For graphs with <= 2000 nodes: exact betweenness_centrality
    - For larger graphs: approximate betweenness_centrality with sampling (k=200)
    """
    n = graph.number_of_nodes()
    if n == 0:
        return {}

    if n <= 2000:
        # Exakt für kleinere Graphen
        return nx.betweenness_centrality(graph)

    k = min(200, n)
    # Approximation via Sampling für große Graphen
    return nx.betweenness_centrality(graph, k=k)
