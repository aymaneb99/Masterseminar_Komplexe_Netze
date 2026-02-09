from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import load_yaml_config
from src.sim.orchestrator import run_experiments


def run_cli() -> None:
	"""Startet einen reproduzierbaren Demo-Run und speichert die Ergebnisse."""
	args = _parse_args()

	experiment_name = args.experiment_name_pos or args.experiment
	experiment_file = _resolve_experiment_file(args.experiment_file_pos or args.experiment_file)
	config = _load_config(experiment_name, experiment_file)
	result = run_experiments(config)

	outdir = _create_run_dir(Path(args.outdir), experiment_name)

	curves_df: pd.DataFrame = result["curves_df"]
	auc_df: pd.DataFrame = result["auc_df"]
	meta: Dict[str, Any] = result["meta"]
	meta["experiment"] = experiment_name
	meta["output_dir"] = str(outdir)

	curves_df.to_csv(outdir / "curves.csv", index=False)
	auc_df.to_csv(outdir / "auc_summary.csv", index=False)
	(outdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

	_plot_curves(curves_df, outdir)


def _parse_args() -> argparse.Namespace:
	"""Parst CLI-Argumente."""
	parser = argparse.ArgumentParser(description="Demo-Run für Smart-Grid-Simulation")
	parser.add_argument(
		"experiment_file_pos",
		nargs="?",
		default=None,
		help="Experimentdatei relativ zu /config/ (z. B. experiment_E1_baseline.yaml)",
	)
	parser.add_argument(
		"experiment_name_pos",
		nargs="?",
		default=None,
		help="Name des Experiments innerhalb der Datei",
	)
	parser.add_argument("--experiment", type=str, default=None, help="Name des Experiments")
	parser.add_argument(
		"--experiment-file",
		type=str,
		default=None,
		help="Pfad zur Experimentdatei (Standard: config/experiment.yaml)",
	)
	parser.add_argument("--outdir", type=str, default="outputs", help="Ausgabeverzeichnis")
	return parser.parse_args()


def _load_config(experiment_name: str | None, experiment_file: str | None) -> Dict[str, Any]:
	"""Lädt defaults.yaml und wendet optional Experiment-Overrides an."""
	base_path = Path(__file__).resolve().parents[2]
	defaults_path = base_path / "config" / "defaults.yaml"
	experiments_path = Path(experiment_file) if experiment_file else (base_path / "config" / "experiment.yaml")
	return load_yaml_config(defaults_path, experiments_path, experiment_name)


def _resolve_experiment_file(experiment_file: str | None) -> str | None:
	"""Löst einen Dateinamen relativ zu /config/ auf."""
	if not experiment_file:
		return None
	path = Path(experiment_file)
	if path.is_absolute():
		return str(path)
	base_path = Path(__file__).resolve().parents[2]
	config_path = base_path / "config" / experiment_file
	return str(config_path)


def _plot_curves(curves_df: pd.DataFrame, outdir: Path) -> None:
	"""Erstellt einen einfachen Robustheitskurven-Plot."""
	if curves_df.empty:
		return

	mean_df = (
		curves_df.groupby(["mode", "scenario_type", "removed_frac"], dropna=False)["gcc_frac"]
		.mean()
		.reset_index()
	)
	grouped = mean_df.groupby(["mode", "scenario_type"], dropna=False)

	plt.figure(figsize=(7, 5))
	for (mode, scenario), group in grouped:
		group_sorted = group.sort_values("removed_frac")
		label = f"{mode} | {scenario}"
		plt.plot(
			group_sorted["removed_frac"],
			group_sorted["gcc_frac"],
			label=label,
			linewidth=2.0,
			antialiased=True,
		)

	plt.xlabel("Entfernter Anteil")
	plt.ylabel("GCC-Anteil")
	plt.title("Robustheitskurven")
	plt.legend()
	plt.tight_layout()
	plt.savefig(outdir / "robustheitskurven.png", dpi=150)
	plt.close()


def _create_run_dir(base_dir: Path, experiment_name: str | None) -> Path:
	"""Erzeugt einen Run-Ordner mit Experimentname und Zeitstempel."""
	label = experiment_name or "default"
	label = _sanitize_label(label)
	timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
	run_dir = base_dir / f"{label}_{timestamp}"
	run_dir.mkdir(parents=True, exist_ok=True)
	return run_dir


def _sanitize_label(label: str) -> str:
	"""Bereinigt Label für Ordnernamen."""
	return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)


if __name__ == "__main__":
	run_cli()
