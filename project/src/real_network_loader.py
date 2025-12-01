from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import networkx as nx


def load_real_graph(graph_cfg: Dict[str, Any]) -> nx.Graph:
    """
    Load a real network (e.g. SciGRID) from disk.

    Currently supports:
      - model: 'real_graphml' with key 'path' pointing to a GraphML file.
    """
    model = graph_cfg.get("model", "").lower()
    if model != "real_graphml":
        raise ValueError(f"Unsupported real model: {model}")

    path = graph_cfg.get("path")
    if path is None:
        raise ValueError("Real graph config requires a 'path' to the data file.")

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Real graph file not found: {path_obj}")

    g = nx.read_graphml(path_obj)  # GraphML einlesen

    preprocess_cfg = graph_cfg.get("preprocess", {})
    g = _preprocess_real_graph(g, preprocess_cfg)
    return g


def _preprocess_real_graph(g: nx.Graph, cfg: Dict[str, Any]) -> nx.Graph:
    """
    Basic preprocessing steps:
      - keep only the giant connected component (optional)
      - relabel nodes to consecutive integers (optional)
    """
    giant_only = bool(cfg.get("giant_component_only", True))
    relabel = bool(cfg.get("relabel_to_integers", True))

    if giant_only and g.number_of_nodes() > 0:
        components = list(nx.connected_components(g))
        if components:
            largest = max(components, key=len)
            # Nur größte Komponente behalten
            g = g.subgraph(largest).copy()

    if relabel:
        # Knoten auf 0..N-1 abbilden
        mapping = {old: i for i, old in enumerate(g.nodes())}
        g = nx.relabel_nodes(g, mapping)

    return g
