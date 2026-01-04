from __future__ import annotations

from typing import Dict, Any

import networkx as nx

from .network_models import generate_synthetic_graph
from .real_network_loader import load_real_graph


def build_graph_from_config(
    graph_cfg: Dict[str, Any],
    seed: int | None = None,
) -> nx.Graph:
    """
    Build either a synthetic or a real graph depending on graph_cfg['type'].
    """
    gtype = graph_cfg.get("type", "").lower()
    if gtype == "synthetic":
        # Synthetisches Modell über network_models
        model = graph_cfg.get("model", "")
        return generate_synthetic_graph(model, graph_cfg, seed=seed)

    if gtype == "real":
        # Reales Netz aus Datei (GraphML)
        return load_real_graph(graph_cfg)

    raise ValueError(f"Unknown graph type in config: {gtype}")
