from __future__ import annotations

from typing import Dict, List, Set

import networkx as nx


def generate_random_failures(
	graph: nx.Graph,
	fractions: List[float],
	seed: int,
) -> Dict[float, Set[int]]:
	"""Erzeugt zufällige Ausfallmengen für gegebene Entfernungsanteile."""
	_validate_fractions(fractions)

	nodes = list(graph.nodes())
	if not nodes:
		raise ValueError("Graph muss Knoten enthalten.")

	rng = _rng(seed)
	rng.shuffle(nodes)

	sorted_fractions = sorted(set(fractions))
	failures: Dict[float, Set[int]] = {}

	for fraction in sorted_fractions:
		if fraction == 0.0:
			failures[fraction] = set()
			continue

		k = int(round(fraction * len(nodes)))
		k = min(max(k, 0), len(nodes))
		failures[fraction] = set(nodes[:k])

	return failures


def _validate_fractions(fractions: List[float]) -> None:
	"""Prüft die Gültigkeit der Anteile."""
	for fraction in fractions:
		if not 0.0 <= fraction <= 1.0:
			raise ValueError("Alle Anteile müssen in [0, 1] liegen.")


def _rng(seed: int):
	"""Erzeugt einen lokalen Zufallszahlengenerator."""
	import random

	return random.Random(seed)
