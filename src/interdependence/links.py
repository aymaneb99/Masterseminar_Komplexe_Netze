from __future__ import annotations

from typing import Dict, Iterable, Set

import networkx as nx


def create_dependency_links(
	gp: nx.Graph,
	gc: nx.Graph,
	q: float,
	r: int,
	seed: int,
) -> Dict[int, Set[int]]:
	"""Erzeugt Abhängigkeiten von GP-Knoten zu GC-Knoten (GC → GP)."""
	if not 0.0 <= q <= 1.0:
		raise ValueError("q muss in [0, 1] liegen.")
	if r < 1:
		raise ValueError("r muss >= 1 sein.")

	gp_nodes = list(gp.nodes())
	gc_nodes = list(gc.nodes())
	if not gp_nodes or not gc_nodes:
		raise ValueError("GP und GC müssen Knoten enthalten.")

	rng = _rng(seed)
	dep_count = int(round(q * len(gp_nodes)))
	dependent_gp_nodes = rng.sample(gp_nodes, dep_count)

	dependencies: Dict[int, Set[int]] = {}
	for gp_node in gp_nodes:
		if gp_node in dependent_gp_nodes:
			chosen_gc = set(rng.sample(gc_nodes, min(r, len(gc_nodes))))
			dependencies[gp_node] = chosen_gc
		else:
			dependencies[gp_node] = set()

	_assert_dependencies_valid(gp, gc, dependencies)
	return dependencies


def propagate_failures(
	gp: nx.Graph,
	gc: nx.Graph,
	dependencies: Dict[int, Set[int]],
	failed_gc_nodes: Set[int],
) -> Set[int]:
	"""Bestimmt GP-Ausfälle aufgrund ausgefallener GC-Knoten."""
	if not dependencies:
		return set()

	gc_node_set = set(gc.nodes())
	failed_gc = set(failed_gc_nodes) & gc_node_set

	failed_gp: Set[int] = set()
	for gp_node in gp.nodes():
		deps = dependencies.get(gp_node, set())
		if not deps:
			continue
		if deps.issubset(failed_gc):
			failed_gp.add(gp_node)

	return failed_gp


def _rng(seed: int):
	"""Erzeugt einen lokalen Zufallszahlengenerator."""
	import random

	return random.Random(seed)


def _assert_dependencies_valid(
	gp: nx.Graph,
	gc: nx.Graph,
	dependencies: Dict[int, Set[int]],
) -> None:
	"""Prüft, ob Abhängigkeiten konsistent sind."""
	gp_nodes = set(gp.nodes())
	gc_nodes = set(gc.nodes())

	assert set(dependencies.keys()) == gp_nodes, "Abhängigkeiten müssen alle GP-Knoten abdecken."
	for gp_node, deps in dependencies.items():
		assert gp_node in gp_nodes, "Abhängigkeit enthält unbekannten GP-Knoten."
		assert deps.issubset(gc_nodes), "Abhängigkeit enthält unbekannte GC-Knoten."
