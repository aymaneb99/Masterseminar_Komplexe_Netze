from __future__ import annotations

from typing import Optional

import networkx as nx


def compute_gcc_fraction(graph: nx.Graph, original_n: Optional[int] = None) -> float:
	"""Berechnet den GCC-Anteil."""
	if graph is None:
		raise ValueError("Graph darf nicht None sein.")

	n_nodes = graph.number_of_nodes()
	denominator = original_n if original_n is not None else n_nodes

	if denominator == 0:
		return 0.0
	if n_nodes == 0:
		return 0.0

	largest_cc = max(nx.connected_components(graph), key=len)
	fraction = len(largest_cc) / denominator

	assert 0.0 <= fraction <= 1.0, "GCC-Anteil muss in [0, 1] liegen."
	return fraction
