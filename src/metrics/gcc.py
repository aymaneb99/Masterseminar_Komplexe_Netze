from __future__ import annotations

import networkx as nx


def compute_gcc_fraction(graph: nx.Graph) -> float:
	"""Berechnet den Anteil der Knoten in der größten Zusammenhangskomponente."""
	if graph is None:
		raise ValueError("Graph darf nicht None sein.")

	n_nodes = graph.number_of_nodes()
	if n_nodes == 0:
		return 0.0
	if n_nodes == 1:
		return 1.0

	largest_cc = max(nx.connected_components(graph), key=len)
	fraction = len(largest_cc) / n_nodes

	assert 0.0 <= fraction <= 1.0, "GCC-Anteil muss in [0, 1] liegen."
	return fraction
