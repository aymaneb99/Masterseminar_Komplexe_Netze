from __future__ import annotations

from typing import Dict, List, Set

import networkx as nx


def generate_targeted_failures(
	graph: nx.Graph,
	fractions: List[float],
	metric: str,
) -> Dict[float, Set[int]]:
	"""Erzeugt Ausfallmengen basierend auf Zentralitätsmetriken."""
	_validate_fractions(fractions)
	_validate_metric(metric)

	nodes = list(graph.nodes())
	if not nodes:
		raise ValueError("Graph muss Knoten enthalten.")

	scores = _compute_scores(graph, metric)
	ordered_nodes = _order_by_score(scores)

	sorted_fractions = sorted(set(fractions))
	failures: Dict[float, Set[int]] = {}

	for fraction in sorted_fractions:
		if fraction == 0.0:
			failures[fraction] = set()
			continue

		k = int(round(fraction * len(ordered_nodes)))
		k = min(max(k, 0), len(ordered_nodes))
		failures[fraction] = set(ordered_nodes[:k])

	return failures


def _compute_scores(graph: nx.Graph, metric: str) -> Dict[int, float]:
	"""Berechnet Zentralitätswerte auf dem Ausgangsgraphen."""
	if metric == "degree":
		return dict(graph.degree())
	if metric == "betweenness":
		return nx.betweenness_centrality(graph)
	raise ValueError(f"Unbekannte Metrik: {metric}")


def _order_by_score(scores: Dict[int, float]) -> List[int]:
	"""Sortiert Knoten absteigend nach Zentralität."""
	return [node for node, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)]


def _validate_fractions(fractions: List[float]) -> None:
	"""Prüft die Gültigkeit der Anteile."""
	for fraction in fractions:
		if not 0.0 <= fraction <= 1.0:
			raise ValueError("Alle Anteile müssen in [0, 1] liegen.")


def _validate_metric(metric: str) -> None:
	"""Prüft die erlaubten Metriken."""
	if metric not in {"degree", "betweenness"}:
		raise ValueError("Metrik muss 'degree' oder 'betweenness' sein.")
