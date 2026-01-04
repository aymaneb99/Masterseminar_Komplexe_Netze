from __future__ import annotations

from typing import Dict, Any, List

import networkx as nx
import numpy as np


def compute_metrics(graph: nx.Graph, original_n: int) -> Dict[str, Any]:
    """
    Compute resilience and structural metrics for the (possibly damaged) graph.

    Enthalten sind:
      - gcc_fraction: Anteil der größten zusammenhängenden Komponente (GCC)
      - gcc_size: absolute Größe der GCC
      - avg_path_length_gcc: mittlere Pfadlänge in der GCC
      - diameter_gcc: Durchmesser der GCC
      - global_efficiency: globale Effizienz des Graphen
      - global_clustering: globaler Clustering-Koeffizient (Transitivität)
      - avg_local_clustering: mittlerer lokaler Clustering-Koeffizient
      - mean_degree, max_degree, degree_std: Kenngrößen der Gradverteilung
    """
    metrics: Dict[str, Any] = {}

    n_nodes = graph.number_of_nodes()
    if n_nodes == 0:
        # Leerer Graph: alle Metriken auf 0
        metrics["gcc_fraction"] = 0.0
        metrics["gcc_size"] = 0
        metrics["avg_path_length_gcc"] = 0.0
        metrics["diameter_gcc"] = 0
        metrics["global_efficiency"] = 0.0
        metrics["global_clustering"] = 0.0
        metrics["avg_local_clustering"] = 0.0
        metrics["mean_degree"] = 0.0
        metrics["max_degree"] = 0
        metrics["degree_std"] = 0.0
        return metrics

    # ---------------------------
    # GCC (größte zusammenhängende Komponente)
    # ---------------------------
    components = list(nx.connected_components(graph))
    if components:
        gcc_nodes = max(components, key=len)
        gcc_size = len(gcc_nodes)
        gcc_fraction = gcc_size / float(original_n) if original_n > 0 else 0.0
        gcc_graph = graph.subgraph(gcc_nodes).copy()
    else:
        gcc_size = 0
        gcc_fraction = 0.0
        gcc_graph = None

    metrics["gcc_fraction"] = gcc_fraction
    metrics["gcc_size"] = gcc_size

    # ---------------------------
    # Mittlere Pfadlänge und Durchmesser in der GCC
    # ---------------------------
    if gcc_graph is None or gcc_graph.number_of_nodes() <= 1:
        # Keine/zu kleine GCC: Pfadmetriken = 0
        metrics["avg_path_length_gcc"] = 0.0
        metrics["diameter_gcc"] = 0
    else:
        try:
            apl = nx.average_shortest_path_length(gcc_graph)
        except Exception:
            apl = 0.0
        metrics["avg_path_length_gcc"] = apl

        try:
            diameter = nx.diameter(gcc_graph)
        except Exception:
            diameter = 0
        metrics["diameter_gcc"] = diameter

    # ---------------------------
    # Globale Effizienz
    # ---------------------------
    try:
        ge = nx.global_efficiency(graph)
    except Exception:
        ge = 0.0
    metrics["global_efficiency"] = ge

    # ---------------------------
    # Clustering (Fehlertoleranz / Redundanz-Proxies)
    # ---------------------------
    try:
        global_clustering = nx.transitivity(graph)
    except Exception:
        global_clustering = 0.0

    try:
        avg_local_clustering = nx.average_clustering(graph)
    except Exception:
        avg_local_clustering = 0.0

    metrics["global_clustering"] = global_clustering
    metrics["avg_local_clustering"] = avg_local_clustering

    # ---------------------------
    # Gradverteilung-Statistiken
    # ---------------------------
    degrees: List[int] = [deg for _, deg in graph.degree()]
    if degrees:
        arr = np.array(degrees, dtype=float)
        metrics["mean_degree"] = float(arr.mean())
        metrics["max_degree"] = int(arr.max())
        metrics["degree_std"] = float(arr.std())
    else:
        metrics["mean_degree"] = 0.0
        metrics["max_degree"] = 0
        metrics["degree_std"] = 0.0

    return metrics
