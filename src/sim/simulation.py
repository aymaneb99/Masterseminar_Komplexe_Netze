from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx

from src.interdependence.links import create_dependency_links, propagate_failures
from src.metrics.gcc import compute_gcc_fraction
from src.networks.gc import create_gc_network
from src.networks.gp import create_gp_network
from src.scenarios.random_failures import generate_random_failures
from src.scenarios.targeted_failures import generate_targeted_failures


def run_single_simulation(config: Dict[str, Any], seed: int, mode: str) -> Dict[str, Any]:
	"""Führt einen einzelnen Simulationslauf aus und liefert die Robustheitskurve."""
	if mode not in {"konventionell", "smart_grid"}:
		raise ValueError("mode muss 'konventionell' oder 'smart_grid' sein.")

	allgemein = config["allgemein"]
	szenario = config["stoerszenarien"]
	inter_cfg = config["interdependenz"]

	fractions = _generate_fractions(float(allgemein["schrittweite"]))
	gp = create_gp_network(config, seed)

	gc: nx.Graph | None = None
	if mode == "smart_grid":
		gc = create_gc_network(config, seed)

	interdependenz_aktiv = mode == "smart_grid" and bool(inter_cfg["aktiv"])
	dependencies = {}
	if interdependenz_aktiv:
		dependencies = create_dependency_links(
			gp=gp,
			gc=gc,
			q=float(inter_cfg["q"]),
			r=int(inter_cfg["r"]),
			seed=seed,
		)

	angreifbares_netz = szenario["angreifbares_netz"]
	if angreifbares_netz == "GC" and mode != "smart_grid":
		raise ValueError("Angriff auf GC ist nur im smart_grid-Modus möglich.")

	ziel_graph = gp if angreifbares_netz == "GP" else gc
	assert ziel_graph is not None

	szenario_typ = szenario["szenario_typ"]
	if szenario_typ == "random":
		failures = generate_random_failures(ziel_graph, fractions, seed)
	elif szenario_typ == "targeted":
		metric = szenario["targeted_metrik"]
		failures = generate_targeted_failures(ziel_graph, fractions, metric)
	else:
		raise ValueError("szenario_typ muss 'random' oder 'targeted' sein.")

	curve: List[Dict[str, float]] = []
	for fraction in sorted(failures.keys()):
		failed_nodes = failures[fraction]
		gp_copy = gp.copy()

		if angreifbares_netz == "GP":
			gp_copy.remove_nodes_from(failed_nodes)
		else:
			if interdependenz_aktiv:
				failed_gp = propagate_failures(
					gp=gp_copy,
					gc=gc,
					dependencies=dependencies,
					failed_gc_nodes=set(failed_nodes),
				)
				gp_copy.remove_nodes_from(failed_gp)

		gcc_frac = compute_gcc_fraction(gp_copy)
		curve.append({"removed_frac": float(fraction), "gcc_frac": float(gcc_frac)})

	meta = {
		"mode": mode,
		"seed": seed,
		"N": int(allgemein["N"]),
		"gp_topologie": config["gp"]["topologie"],
		"gc_topologie": config["gc"]["topologie"] if mode == "smart_grid" else None,
		"szenario_typ": szenario_typ,
		"angreifbares_netz": angreifbares_netz,
		"targeted_metrik": szenario.get("targeted_metrik"),
		"interdependenz_aktiv": bool(inter_cfg["aktiv"]),
		"q": float(inter_cfg["q"]),
		"r": int(inter_cfg["r"]),
	}

	return {"curve": curve, "meta": meta}


def _generate_fractions(step: float) -> List[float]:
	"""Erzeugt eine monoton wachsende Liste von Anteilen in [0, 1]."""
	if not 0.0 < step <= 1.0:
		raise ValueError("schrittweite muss in (0, 1] liegen.")

	fractions: List[float] = [0.0]
	current = step
	while current < 1.0:
		fractions.append(round(current, 10))
		current += step
	fractions.append(1.0)

	return sorted(set(fractions))
