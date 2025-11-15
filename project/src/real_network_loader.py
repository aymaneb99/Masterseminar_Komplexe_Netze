from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import networkx as nx


def load_real_graph(graph_cfg: Dict[str, Any]) -> nx.Graph:
    """
    Load a real network from disk based on config entry.

    Currently supported:
      - model: "real_graphml" with key 'path' pointing to a GraphML file,
        e.g. a SciGRID-based transmission grid.
    """
    model = graph_cfg.get("model", "").lower()
    if model != "real_graphml":
        raise ValueError(f"Unsupported real model: {model}")

    path = graph_cfg.get("path", None)
    if path is None:
        raise ValueError("Real graph config requires a 'path' to the data file.")

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Real graph file not found: {path_obj}")

    # For SciGRID and many others, GraphML is a natural format.
    g = nx.read_graphml(path_obj)

    preprocess_cfg = graph_cfg.get("preprocess", {})
    g = _preprocess_real_graph(g, preprocess_cfg)

    return g


def _preprocess_real_graph(g: nx.Graph, cfg: Dict[str, Any]) -> nx.Graph:
    """
    Apply basic preprocessing to the real graph, such as:
      - keeping only the giant component
      - relabelling nodes to consecutive integers
    """
    giant_only = bool(cfg.get("giant_component_only", True))
    relabel = bool(cfg.get("relabel_to_integers", True))

    if giant_only and g.number_of_nodes() > 0:
        components = list(nx.connected_components(g))
        if components:
            largest = max(components, key=len)
            g = g.subgraph(largest).copy()

    if relabel:
        mapping = {old: i for i, old in enumerate(g.nodes())}
        g = nx.relabel_nodes(g, mapping)

    return g
