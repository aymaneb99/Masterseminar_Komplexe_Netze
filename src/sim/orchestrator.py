from __future__ import annotations

import time
from typing import Any, Dict, List

import pandas as pd

from src.metrics.auc import compute_auc
from src.sim.simulation import run_single_simulation


def run_experiments(config: Dict[str, Any]) -> Dict[str, Any]:
	"""Führt mehrere Runs aus und aggregiert Kurven- und AUC-Daten."""
	_validate_config(config)

	allgemein = config["allgemein"]
	runs = int(allgemein["runs"])
	seed_base = int(allgemein["seed"])

	modes = config.get("modi", ["konventionell", "smart_grid"])
	if not isinstance(modes, list) or not modes:
		raise ValueError("modi muss eine nichtleere Liste sein.")

	start_time = time.time()
	curve_rows: List[Dict[str, Any]] = []
	auc_rows: List[Dict[str, Any]] = []

	for mode in modes:
		for run_id in range(runs):
			seed = seed_base + run_id
			result = run_single_simulation(config=config, seed=seed, mode=mode)

			curve = result["curve"]
			meta = result["meta"]

			for point in curve:
				curve_rows.append(
					{
						"mode": meta["mode"],
						"scenario_type": meta["szenario_typ"],
						"target_metric": meta["targeted_metrik"],
						"attack_network": meta["angreifbares_netz"],
						"run_id": run_id,
						"removed_frac": point["removed_frac"],
						"gcc_frac": point["gcc_frac"],
						"seed": meta["seed"],
						"N": meta["N"],
						"q": meta["q"],
						"r": meta["r"],
					}
				)

			fractions = [p["removed_frac"] for p in curve]
			values = [p["gcc_frac"] for p in curve]
			auc_value = compute_auc(fractions, values)

			auc_rows.append(
				{
					"mode": meta["mode"],
					"scenario_type": meta["szenario_typ"],
					"target_metric": meta["targeted_metrik"],
					"attack_network": meta["angreifbares_netz"],
					"auc": auc_value,
					"run_id": run_id,
					"seed": meta["seed"],
					"N": meta["N"],
					"q": meta["q"],
					"r": meta["r"],
				}
			)

	curves_df = pd.DataFrame(curve_rows)
	auc_df = _aggregate_auc(pd.DataFrame(auc_rows), runs, seed_base)

	meta = {
		"runs": runs,
		"seed_base": seed_base,
		"modes": modes,
		"runtime_s": round(time.time() - start_time, 3),
	}

	return {"curves_df": curves_df, "auc_df": auc_df, "meta": meta}


def _aggregate_auc(auc_df: pd.DataFrame, runs: int, seed_base: int) -> pd.DataFrame:
	"""Aggregiert AUC-Werte über Runs (Mittelwert/Std)."""
	if auc_df.empty:
		return pd.DataFrame(
			columns=[
				"mode",
				"scenario_type",
				"target_metric",
				"attack_network",
				"auc_mean",
				"auc_std",
				"runs",
				"seed_base",
				"N",
				"q",
				"r",
			]
		)

	group_cols = ["mode", "scenario_type", "target_metric", "attack_network", "N", "q", "r"]
	summary = (
		auc_df.groupby(group_cols, dropna=False)["auc"]
		.agg(auc_mean="mean", auc_std="std")
		.reset_index()
	)
	summary["runs"] = runs
	summary["seed_base"] = seed_base

	return summary[
		[
			"mode",
			"scenario_type",
			"target_metric",
			"attack_network",
			"auc_mean",
			"auc_std",
			"runs",
			"seed_base",
			"N",
			"q",
			"r",
		]
	]


def _validate_config(config: Dict[str, Any]) -> None:
	"""Prüft zentrale Konfigurationsfelder."""
	if "allgemein" not in config:
		raise ValueError("Konfiguration muss 'allgemein' enthalten.")
	if "runs" not in config["allgemein"]:
		raise ValueError("Konfiguration muss 'allgemein.runs' enthalten.")
	if "seed" not in config["allgemein"]:
		raise ValueError("Konfiguration muss 'allgemein.seed' enthalten.")
