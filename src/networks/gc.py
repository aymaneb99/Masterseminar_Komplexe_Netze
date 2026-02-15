from __future__ import annotations

from typing import Any, Dict

import networkx as nx


def create_gc_network(config: Dict[str, Any], seed: int) -> nx.Graph:
	"""Erzeugt das Kommunikationsnetz (GC) als zusammenhängenden Graph."""
	gc_cfg = config["gc"]

	n_nodes = int(gc_cfg.get("N", config["allgemein"]["N"]))
	topologie = gc_cfg["topologie"]
	parameter = gc_cfg["parameter"][topologie]

	if n_nodes <= 0:
		raise ValueError("N muss positiv sein.")

	graph = _generate_graph(n_nodes, topologie, parameter, seed)
	graph = _ensure_connected(graph)

	assert graph.number_of_nodes() == n_nodes, "Unerwartete Knotenzahl im GC."
	assert graph.number_of_nodes() > 0, "GC darf nicht leer sein."

	return graph


def _generate_graph(n_nodes: int, topologie: str, parameter: Dict[str, Any], seed: int) -> nx.Graph:
	"""Erzeugt einen Graphen gemäß der gewählten Topologie."""
	if topologie == "ER":
		p = float(parameter["p"])
		return nx.erdos_renyi_graph(n_nodes, p, seed=seed)

	if topologie == "WS":
		k = int(parameter["k"])
		beta = float(parameter["beta"])
		return nx.watts_strogatz_graph(n_nodes, k, beta, seed=seed)

	if topologie == "BA":
		m = int(parameter["m"])
		return nx.barabasi_albert_graph(n_nodes, m, seed=seed)

	raise ValueError(f"Unbekannte GC-Topologie: {topologie}")


def _ensure_connected(graph: nx.Graph) -> nx.Graph:
	"""Stellt Zusammenhängigkeit durch minimale Nachverdrahtung sicher."""
	if graph.number_of_nodes() == 1:
		return graph

	if nx.is_connected(graph):
		return graph

	components = [sorted(component) for component in nx.connected_components(graph)]
	representatives = [nodes[0] for nodes in components]

	for idx in range(1, len(representatives)):
		graph.add_edge(representatives[idx - 1], representatives[idx])

	assert nx.is_connected(graph), "GC ist nach Nachverdrahtung nicht zusammenhängend."
	return graph
