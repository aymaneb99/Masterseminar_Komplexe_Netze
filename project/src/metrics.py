from __future__ import annotations

from typing import Dict, Any

import networkx as nx


def compute_metrics(graph: nx.Graph, original_n: int) -> Dict[str, Any]:
    """
    Compute resilience metrics for the (possibly damaged) graph:

      - lcc_fraction
      - average_path_length_lcc
      - global_efficiency
    """
    metrics: Dict[str, Any] = {}

    if graph.number_of_nodes() == 0:
        metrics["lcc_fraction"] = 0.0
        metrics["average_path_length_lcc"] = 0.0
        metrics["global_efficiency"] = 0.0
        return metrics

    components = list(nx.connected_components(graph))
    if components:
        lcc_nodes = max(components, key=len)
        lcc_size = len(lcc_nodes)
        lcc_fraction = lcc_size / float(original_n) if original_n > 0 else 0.0
        lcc_graph = graph.subgraph(lcc_nodes).copy()
    else:
        lcc_size = 0
        lcc_fraction = 0.0
        lcc_graph = None

    metrics["lcc_fraction"] = lcc_fraction

    if lcc_graph is None or lcc_graph.number_of_nodes() <= 1:
        metrics["average_path_length_lcc"] = 0.0
    else:
        try:
            apl = nx.average_shortest_path_length(lcc_graph)
        except Exception:
            apl = 0.0
        metrics["average_path_length_lcc"] = apl

    try:
        ge = nx.global_efficiency(graph)
    except Exception:
        ge = 0.0
    metrics["global_efficiency"] = ge

    return metrics
