from __future__ import annotations

from typing import Dict, Iterable, Set

import networkx as nx


def create_dependency_links(
	gp: nx.Graph,
	gc: nx.Graph,
	q: float,
	r: int,
	seed: int,
	correlation_mode: str = "random",
) -> Dict[int, Set[int]]:
	"""Erzeugt Abhängigkeiten von GP-Knoten zu GC-Knoten (GC → GP).
	
	Args:
		correlation_mode: "random" (zufällige Zuweisung) oder 
		                  "degree" (wichtige GP-Knoten → wichtige GC-Knoten)
	"""
	if not 0.0 <= q <= 1.0:
		raise ValueError("q muss in [0, 1] liegen.")
	if r < 1:
		raise ValueError("r muss >= 1 sein.")
	if correlation_mode not in {"random", "degree"}:
		raise ValueError("correlation_mode muss 'random' oder 'degree' sein.")

	gp_nodes = list(gp.nodes())
	gc_nodes = list(gc.nodes())
	if not gp_nodes or not gc_nodes:
		raise ValueError("GP und GC müssen Knoten enthalten.")

	rng = _rng(seed)
	dep_count = int(round(q * len(gp_nodes)))

	if correlation_mode == "degree":
		# Korrelierte Zuweisung: Sortiere nach Degree (absteigend)
		gp_sorted = sorted(gp_nodes, key=lambda n: gp.degree(n), reverse=True)
		gc_sorted = sorted(gc_nodes, key=lambda n: gc.degree(n), reverse=True)
		dependent_gp_nodes = gp_sorted[:dep_count]
	else:
		# Zufällige Zuweisung (Standardverhalten)
		dependent_gp_nodes = rng.sample(gp_nodes, dep_count)
		gc_sorted = gc_nodes  # Nicht verwendet bei random

	dependencies: Dict[int, Set[int]] = {}
	for idx, gp_node in enumerate(gp_nodes):
		if gp_node in dependent_gp_nodes:
			if correlation_mode == "degree":
				# Weise den i-ten GP-Knoten den top-r GC-Knoten zu
				# (zyklisch, falls mehr abhängige GP-Knoten als GC-Knoten)
				gp_rank = dependent_gp_nodes.index(gp_node)
				gc_indices = [(gp_rank + j) % len(gc_sorted) for j in range(min(r, len(gc_sorted)))]
				chosen_gc = set(gc_sorted[i] for i in gc_indices)
			else:
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
