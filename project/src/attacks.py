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
    Compute an ordered list of nodes to be removed according to an attack scenario.

    attack_cfg:
      - type: "random" or "targeted"
      - strategy (for targeted): "degree" or "betweenness"
    """
    atype = attack_cfg.get("type", "").lower()
    nodes = list(graph.nodes())

    if atype == "random":
        rng = random.Random(seed)
        rng.shuffle(nodes)
        return nodes

    if atype == "targeted":
        strategy = attack_cfg.get("strategy", "").lower()
        if strategy == "degree":
            centrality = dict(graph.degree())
        elif strategy == "betweenness":
            centrality = nx.betweenness_centrality(graph)
        else:
            raise ValueError(f"Unknown targeted strategy: {strategy}")

        ordered = sorted(centrality.items(), key=lambda kv: (-kv[1], kv[0]))
        return [node for node, _ in ordered]

    raise ValueError(f"Unknown attack type: {atype}")
