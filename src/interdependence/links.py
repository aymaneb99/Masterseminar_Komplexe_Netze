from __future__ import annotations

from typing import Dict, Iterable, List, NamedTuple, Set

import networkx as nx


def create_dependency_links(
	gp: nx.Graph,
	gc: nx.Graph,
	q: float,
	r: int,
	seed: int,
	correlation_mode: str = "random",
) -> Dict[int, Set[int]]:
	"""Erzeugt Abhängigkeiten von GP-Knoten zu GC-Knoten."""
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
		# Korrelierte Zuweisung nach Grad
		gp_sorted = sorted(gp_nodes, key=lambda n: gp.degree(n), reverse=True)
		gc_sorted = sorted(gc_nodes, key=lambda n: gc.degree(n), reverse=True)
		dependent_gp_nodes = gp_sorted[:dep_count]
	else:
		# Zufällige Zuweisung
		dependent_gp_nodes = rng.sample(gp_nodes, dep_count)
		gc_sorted = gc_nodes

	dependencies: Dict[int, Set[int]] = {}
	for idx, gp_node in enumerate(gp_nodes):
		if gp_node in dependent_gp_nodes:
			if correlation_mode == "degree":
				# Weist zyklisch die wichtigsten GC-Knoten zu
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


class CascadeResult(NamedTuple):
	"""Ergebnis einer iterativen Kaskadensimulation."""
	failed_gp: Set[int]
	failed_gc: Set[int]
	cascade_steps: int
	per_step_stats: List[Dict[str, int]]


def build_reverse_dependencies(
	dependencies: Dict[int, Set[int]],
) -> Dict[int, Set[int]]:
	"""Erzeugt die Rückrichtung der Abhängigkeiten (GC -> GP)."""
	reverse: Dict[int, Set[int]] = {}
	for gp_node, gc_deps in dependencies.items():
		for gc_node in gc_deps:
			if gc_node not in reverse:
				reverse[gc_node] = set()
			reverse[gc_node].add(gp_node)
	return reverse


def propagate_cascade(
	gp: nx.Graph,
	gc: nx.Graph,
	dependencies: Dict[int, Set[int]],
	failed_gc_nodes: Set[int],
	max_steps: int = 100,
) -> CascadeResult:
	"""Führt die iterative Kaskadenpropagation aus."""
	if not dependencies:
		return CascadeResult(set(), set(), 0, [])

	# Kopien für die Berechnung
	gp_work = gp.copy()
	gc_work = gc.copy()

	# Rückrichtung GC -> GP
	reverse_deps = build_reverse_dependencies(dependencies)

	# Bisherige Ausfälle
	all_failed_gc: Set[int] = set()
	all_failed_gp: Set[int] = set()

	# Initiale GC-Ausfälle
	initial_gc_failures = set(failed_gc_nodes) & set(gc_work.nodes())
	gc_work.remove_nodes_from(initial_gc_failures)
	all_failed_gc.update(initial_gc_failures)

	per_step_stats: List[Dict[str, int]] = []
	step = 0

	while step < max_steps:
		step += 1
		new_gc_failures: Set[int] = set()
		new_gp_failures: Set[int] = set()

		# Phase A: GC außerhalb GCC fällt aus
		if gc_work.number_of_nodes() > 0:
			gc_gcc_nodes = _get_gcc_nodes(gc_work)
			gc_non_gcc = set(gc_work.nodes()) - gc_gcc_nodes
			if gc_non_gcc:
				gc_work.remove_nodes_from(gc_non_gcc)
				new_gc_failures.update(gc_non_gcc)
				all_failed_gc.update(gc_non_gcc)

		# Phase B: Ausfälle von GC nach GP
		for gp_node in list(gp_work.nodes()):
			deps = dependencies.get(gp_node, set())
			if not deps:
				continue
			# GP fällt aus, wenn alle GC-Abhängigkeiten ausgefallen sind
			if deps.issubset(all_failed_gc):
				new_gp_failures.add(gp_node)

		if new_gp_failures:
			gp_work.remove_nodes_from(new_gp_failures)
			all_failed_gp.update(new_gp_failures)

		# Phase C: GP außerhalb GCC fällt aus
		gp_fragmentation_failures: Set[int] = set()
		if gp_work.number_of_nodes() > 0:
			gp_gcc_nodes = _get_gcc_nodes(gp_work)
			gp_non_gcc = set(gp_work.nodes()) - gp_gcc_nodes
			if gp_non_gcc:
				gp_work.remove_nodes_from(gp_non_gcc)
				gp_fragmentation_failures.update(gp_non_gcc)
				all_failed_gp.update(gp_non_gcc)

		# Phase D: Ausfälle von GP nach GC
		gc_from_gp_failures: Set[int] = set()
		for gc_node in list(gc_work.nodes()):
			gp_suppliers = reverse_deps.get(gc_node, set())
			if not gp_suppliers:
				continue
			# GC fällt aus, wenn alle GP-Versorger ausgefallen sind
			if gp_suppliers.issubset(all_failed_gp):
				gc_from_gp_failures.add(gc_node)

		if gc_from_gp_failures:
			gc_work.remove_nodes_from(gc_from_gp_failures)
			all_failed_gc.update(gc_from_gp_failures)

		# Schrittstatistik
		total_new = (
			len(new_gc_failures)
			+ len(new_gp_failures)
			+ len(gp_fragmentation_failures)
			+ len(gc_from_gp_failures)
		)
		per_step_stats.append({
			"step": step,
			"new_gc_failures": len(new_gc_failures) + len(gc_from_gp_failures),
			"new_gp_failures": len(new_gp_failures) + len(gp_fragmentation_failures),
			"total_failed_gc": len(all_failed_gc),
			"total_failed_gp": len(all_failed_gp),
		})

		# Abbruch ohne neue Ausfälle
		if total_new == 0:
			break

	return CascadeResult(
		failed_gp=all_failed_gp,
		failed_gc=all_failed_gc,
		cascade_steps=step,
		per_step_stats=per_step_stats,
	)


def _get_gcc_nodes(graph: nx.Graph) -> Set[int]:
	"""Bestimmt die Knotenmenge der größten Zusammenhangskomponente."""
	if graph.number_of_nodes() == 0:
		return set()
	return set(max(nx.connected_components(graph), key=len))


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
