from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import list_experiments, load_yaml_config
from src.networks.gc import create_gc_network
from src.networks.gp import create_gp_network
from src.sim.orchestrator import run_experiments


def main() -> None:
	"""Streamlit-App für die Robustheitsanalyse eines Smart Grids."""
	st.set_page_config(page_title="Smart-Grid-Robustheit", layout="wide")
	st.title("Robustheit von Smart Grids")

	with st.sidebar:
		st.header("Konfiguration")
		config_source = st.selectbox(
			"Quelle",
			["Manuell", "defaults.yaml", "defaults + experiment.yaml"],
			index=0,
			key="config_source",
		)

		experiment_name = None
		if config_source == "defaults + experiment.yaml":
			experiment_options = _get_experiment_options()
			if experiment_options:
				experiment_name = st.selectbox(
					"Experiment",
					experiment_options,
					index=0,
					key="experiment_name",
				)
			else:
				st.info("Keine Experimente gefunden.")

		base_config = _load_base_config(config_source, experiment_name)
		st.session_state["base_config"] = base_config
		_maybe_sync_state(config_source, experiment_name, base_config)

		st.divider()
		st.header("Parameter")
		mode_label = st.selectbox(
			"Modus",
			["Konventionell", "Smart Grid", "Vergleich"],
			index=2,
			key="mode_label",
		)

		st.subheader("Allgemein")
		n_nodes = st.number_input(
			"Knotenanzahl N",
			min_value=10,
			max_value=2000,
			value=st.session_state.get("n_nodes", _get_base_value(base_config, ["allgemein", "N"], 100)),
			step=10,
			key="n_nodes",
		)
		seed = st.number_input(
			"Seed",
			min_value=0,
			max_value=10_000,
			value=st.session_state.get("seed", _get_base_value(base_config, ["allgemein", "seed"], 42)),
			step=1,
			key="seed",
		)
		runs = st.number_input(
			"Runs",
			min_value=1,
			max_value=200,
			value=st.session_state.get("runs", _get_base_value(base_config, ["allgemein", "runs"], 30)),
			step=1,
			key="runs",
		)
		step = st.slider(
			"Schrittweite",
			min_value=0.01,
			max_value=0.2,
			value=st.session_state.get("step", _get_base_value(base_config, ["allgemein", "schrittweite"], 0.05)),
			step=0.01,
			key="step",
		)

		st.subheader("Stromnetz (GP)")
		gp_topology = st.selectbox(
			"GP Topologie",
			["ER", "WS", "BA"],
			index=0,
			key="gp_topology",
		)
		gp_params = _topology_params(
			"GP",
			gp_topology,
			n_nodes,
			defaults=_get_topology_defaults(base_config, "gp"),
		)

		st.subheader("Kommunikationsnetz (GC)")
		gc_topology = st.selectbox(
			"GC Topologie",
			["ER", "WS", "BA"],
			index=0,
			key="gc_topology",
			disabled=mode_label == "Konventionell",
		)
		gc_params = _topology_params(
			"GC",
			gc_topology,
			n_nodes,
			defaults=_get_topology_defaults(base_config, "gc"),
			disabled=mode_label == "Konventionell",
		)

		st.subheader("Interdependenz")
		inter_active = st.checkbox(
			"aktiv",
			value=st.session_state.get("inter_active", _get_base_value(base_config, ["interdependenz", "aktiv"], True)),
			disabled=mode_label == "Konventionell",
			key="inter_active",
		)
		q = st.slider(
			"Kopplungsanteil q",
			min_value=0.0,
			max_value=1.0,
			value=st.session_state.get("q", _get_base_value(base_config, ["interdependenz", "q"], 0.8)),
			step=0.05,
			disabled=mode_label == "Konventionell",
			key="q",
		)
		r = st.number_input(
			"Redundanz r",
			min_value=1,
			max_value=10,
			value=st.session_state.get("r", _get_base_value(base_config, ["interdependenz", "r"], 1)),
			step=1,
			disabled=mode_label == "Konventionell",
			key="r",
		)
		gc_to_gp = st.checkbox(
			"Richtung GC → GP",
			value=st.session_state.get("gc_to_gp", _get_base_value(base_config, ["interdependenz", "GC_to_GP"], True)),
			disabled=mode_label == "Konventionell",
			key="gc_to_gp",
		)

		st.subheader("Szenario")
		scenario_type = st.selectbox(
			"Szenario-Typ",
			["random", "targeted"],
			index=0,
			key="scenario_type",
		)
		target_metric = st.selectbox(
			"Targeted-Metrik",
			["degree", "betweenness"],
			index=0,
			disabled=scenario_type != "targeted",
			key="target_metric",
		)
		attack_options = ["GP", "GC"] if mode_label != "Konventionell" else ["GP"]
		if st.session_state.get("attack_network") not in attack_options:
			st.session_state["attack_network"] = attack_options[0]
		attack_network = st.selectbox(
			"Angreifbares Netz",
			attack_options,
			index=attack_options.index(st.session_state.get("attack_network", attack_options[0])),
			key="attack_network",
		)

		st.subheader("Aktion")
		run_clicked = st.button("Run")
		reset_clicked = st.button("Reset")

	if reset_clicked:
		st.session_state.pop("results", None)
		st.session_state.pop("config", None)
		st.session_state["force_yaml_reset"] = True
		st.success("Zurückgesetzt auf YAML-Stand.")
		st.rerun()

	config = _build_config(
		n_nodes=n_nodes,
		seed=seed,
		runs=runs,
		step=step,
		gp_topology=gp_topology,
		gp_params=gp_params,
		gc_topology=gc_topology,
		gc_params=gc_params,
		inter_active=inter_active,
		q=q,
		r=r,
		gc_to_gp=gc_to_gp,
		scenario_type=scenario_type,
		target_metric=target_metric,
		attack_network=attack_network,
		mode_label=mode_label,
	)

	base_config_state = st.session_state.get("base_config")
	with st.expander("Aktive Konfiguration", expanded=False):
		st.json(config)
		if config_source != "Manuell" and isinstance(base_config_state, dict):
			st.caption("Geladener YAML-Stand (vor manuellen Änderungen)")
			st.json(base_config_state)

	if run_clicked:
		with st.status("Simulation läuft...", expanded=True) as status:
			status.write("Konfiguration prüfen")
			status.write("Simulation starten")
			results = _cached_run(config)
			st.session_state["results"] = results
			st.session_state["config"] = config
			status.update(label="Fertig", state="complete")

	results = st.session_state.get("results")
	config_state = st.session_state.get("config")

	tab_results, tab_data, tab_network, tab_info = st.tabs(["Ergebnisse", "Daten", "Netzwerk", "Info"])

	with tab_results:
		if results is None:
			st.info("Bitte einen Run starten.")
		else:
			curves_df = results["curves_df"]
			auc_df = results["auc_df"]
			fig = _plot_curves(curves_df)
			st.pyplot(fig)
			st.dataframe(auc_df, use_container_width=True)
			label = _build_run_label(config_source, experiment_name)
			_export_outputs(curves_df, auc_df, results["meta"], label)  # Export nach outputs/

	with tab_data:
		if results is None:
			st.info("Bitte einen Run starten.")
		else:
			curves_df = results["curves_df"]
			auc_df = results["auc_df"]
			st.subheader("Kurvendaten")
			st.dataframe(curves_df, use_container_width=True)
			st.download_button(
				"Kurvendaten CSV",
				curves_df.to_csv(index=False),
				file_name="curves.csv",
				mime="text/csv",
			)
			st.subheader("AUC-Zusammenfassung")
			st.dataframe(auc_df, use_container_width=True)
			st.download_button(
				"AUC CSV",
				auc_df.to_csv(index=False),
				file_name="auc_summary.csv",
				mime="text/csv",
			)

	with tab_network:
		if config_state is None:
			st.info("Bitte einen Run starten.")
		else:
			_show_networks(config_state, mode_label)

	with tab_info:
		st.markdown(
			"""
- Modelliert nur Struktur, keine Lastflüsse
- Binäre Abhängigkeit zwischen GP und GC
- Interdependenz standardmäßig GC → GP
- Auswertung erfolgt ausschließlich auf GP
- Robustheit über GCC-Anteil pro Ausfallgrad
- Targeted-Angriffe basieren auf Zentralitäten
- Reproduzierbarkeit über Seed und Konfiguration
- Fokus auf Vergleich: konventionell vs. Smart Grid
"""
		)


@st.cache_data(show_spinner=False)
def _cached_run(config: Dict[str, Any]) -> Dict[str, Any]:
	"""Zwischenspeicher für Simulationsergebnisse."""
	return run_experiments(config)


def _get_experiment_options() -> List[str]:
	"""Liest die Experimentnamen aus experiment.yaml."""
	try:
		experiments_path = PROJECT_ROOT / "config" / "experiment.yaml"
		return list_experiments(experiments_path)
	except Exception as exc:
		st.error(f"Experiment-Datei konnte nicht gelesen werden: {exc}")
		return []


def _load_base_config(config_source: str, experiment_name: str | None) -> Dict[str, Any]:
	"""Lädt die Basis-Konfiguration gemäß Auswahl."""
	if config_source == "Manuell":
		return _default_base_config()

	defaults_path = PROJECT_ROOT / "config" / "defaults.yaml"
	experiments_path = PROJECT_ROOT / "config" / "experiment.yaml"

	try:
		if config_source == "defaults.yaml":
			return load_yaml_config(defaults_path)
		return load_yaml_config(defaults_path, experiments_path, experiment_name)
	except Exception as exc:
		st.error(f"YAML konnte nicht geladen werden: {exc}")
		return _default_base_config()


def _maybe_sync_state(config_source: str, experiment_name: str | None, base_config: Dict[str, Any]) -> None:
	"""Synchronisiert Session-State bei Quellwechsel oder Reset."""
	last_source = st.session_state.get("config_source_last")
	last_experiment = st.session_state.get("experiment_last")
	force_reset = st.session_state.get("force_yaml_reset", False)

	if (last_source != config_source) or (last_experiment != experiment_name) or force_reset:
		_sync_state_from_config(base_config)
		st.session_state["config_source_last"] = config_source
		st.session_state["experiment_last"] = experiment_name
		st.session_state.pop("force_yaml_reset", None)
		return

	if "n_nodes" not in st.session_state:
		_sync_state_from_config(base_config)


def _sync_state_from_config(base_config: Dict[str, Any]) -> None:
	"""Setzt Standardwerte in den Session-State."""
	st.session_state["n_nodes"] = int(_get_base_value(base_config, ["allgemein", "N"], 100))
	st.session_state["seed"] = int(_get_base_value(base_config, ["allgemein", "seed"], 42))
	st.session_state["runs"] = int(_get_base_value(base_config, ["allgemein", "runs"], 30))
	st.session_state["step"] = float(_get_base_value(base_config, ["allgemein", "schrittweite"], 0.05))

	st.session_state["gp_topology"] = _get_base_value(base_config, ["gp", "topologie"], "ER")
	st.session_state["gc_topology"] = _get_base_value(base_config, ["gc", "topologie"], "ER")

	gp_defaults = _get_topology_defaults(base_config, "gp")
	gc_defaults = _get_topology_defaults(base_config, "gc")

	st.session_state["gp_er_p"] = float(gp_defaults["ER"].get("p", 0.06))
	st.session_state["gp_ws_k"] = int(gp_defaults["WS"].get("k", 6))
	st.session_state["gp_ws_beta"] = float(gp_defaults["WS"].get("beta", 0.1))
	st.session_state["gp_ba_m"] = int(gp_defaults["BA"].get("m", 3))

	st.session_state["gc_er_p"] = float(gc_defaults["ER"].get("p", 0.06))
	st.session_state["gc_ws_k"] = int(gc_defaults["WS"].get("k", 6))
	st.session_state["gc_ws_beta"] = float(gc_defaults["WS"].get("beta", 0.1))
	st.session_state["gc_ba_m"] = int(gc_defaults["BA"].get("m", 3))

	st.session_state["inter_active"] = bool(_get_base_value(base_config, ["interdependenz", "aktiv"], True))
	st.session_state["q"] = float(_get_base_value(base_config, ["interdependenz", "q"], 0.8))
	st.session_state["r"] = int(_get_base_value(base_config, ["interdependenz", "r"], 1))
	st.session_state["gc_to_gp"] = bool(_get_base_value(base_config, ["interdependenz", "GC_to_GP"], True))

	st.session_state["scenario_type"] = _get_base_value(base_config, ["stoerszenarien", "szenario_typ"], "random")
	st.session_state["target_metric"] = _get_base_value(base_config, ["stoerszenarien", "targeted_metrik"], "degree")
	st.session_state["attack_network"] = _get_base_value(base_config, ["stoerszenarien", "angreifbares_netz"], "GP")


def _get_base_value(config: Dict[str, Any], path: List[str], default: Any) -> Any:
	"""Liest einen verschachtelten Wert mit Fallback."""
	current: Any = config
	for key in path:
		if not isinstance(current, dict) or key not in current:
			return default
		current = current[key]
	return current


def _get_topology_defaults(config: Dict[str, Any], net_key: str) -> Dict[str, Dict[str, Any]]:
	"""Extrahiert Topologie-Parameter für GP oder GC."""
	params = _get_base_value(config, [net_key, "parameter"], {})
	return {
		"ER": params.get("ER", {}) if isinstance(params, dict) else {},
		"WS": params.get("WS", {}) if isinstance(params, dict) else {},
		"BA": params.get("BA", {}) if isinstance(params, dict) else {},
	}


def _default_base_config() -> Dict[str, Any]:
	"""Fallback-Konfiguration bei fehlendem YAML."""
	return {
		"allgemein": {"seed": 42, "runs": 30, "schrittweite": 0.05, "N": 100},
		"gp": {
			"topologie": "ER",
			"parameter": {
				"ER": {"p": 0.06},
				"WS": {"k": 6, "beta": 0.1},
				"BA": {"m": 3},
			},
		},
		"gc": {
			"topologie": "ER",
			"parameter": {
				"ER": {"p": 0.06},
				"WS": {"k": 6, "beta": 0.1},
				"BA": {"m": 3},
			},
		},
		"interdependenz": {"aktiv": True, "q": 0.8, "r": 1, "GC_to_GP": True},
		"stoerszenarien": {"szenario_typ": "random", "targeted_metrik": "degree", "angreifbares_netz": "GP"},
	}


def _build_config(
	n_nodes: int,
	seed: int,
	runs: int,
	step: float,
	gp_topology: str,
	gp_params: Dict[str, Any],
	gc_topology: str,
	gc_params: Dict[str, Any],
	inter_active: bool,
	q: float,
	r: int,
	gc_to_gp: bool,
	scenario_type: str,
	target_metric: str,
	attack_network: str,
	mode_label: str,
) -> Dict[str, Any]:
	"""Erstellt eine konsistente Konfiguration für den Orchestrator."""
	modes = ["konventionell", "smart_grid"] if mode_label == "Vergleich" else [
		"konventionell" if mode_label == "Konventionell" else "smart_grid"
	]

	return {
		"allgemein": {
			"seed": int(seed),
			"runs": int(runs),
			"schrittweite": float(step),
			"N": int(n_nodes),
		},
		"gp": {
			"topologie": gp_topology,
			"parameter": _wrap_params(gp_topology, gp_params),
		},
		"gc": {
			"topologie": gc_topology,
			"parameter": _wrap_params(gc_topology, gc_params),
		},
		"interdependenz": {
			"aktiv": bool(inter_active),
			"q": float(q),
			"r": int(r),
			"GC_to_GP": bool(gc_to_gp),
		},
		"stoerszenarien": {
			"szenario_typ": scenario_type,
			"targeted_metrik": target_metric,
			"angreifbares_netz": attack_network,
		},
		"modi": modes,
	}


def _wrap_params(topology: str, params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
	"""Packt Parameter in die erwartete Struktur."""
	return {
		"ER": params if topology == "ER" else {},
		"WS": params if topology == "WS" else {},
		"BA": params if topology == "BA" else {},
	}


def _topology_params(
	prefix: str,
	topology: str,
	n_nodes: int,
	defaults: Dict[str, Dict[str, Any]],
	disabled: bool = False,
) -> Dict[str, Any]:
	"""Erfasst Topologie-Parameter in der Sidebar."""
	prefix_key = prefix.lower()
	if topology == "ER":
		default_p = defaults.get("ER", {}).get("p", 6.0 / max(n_nodes - 1, 1))
		p = st.number_input(
			f"{prefix} ER p",
			min_value=0.0,
			max_value=1.0,
			value=st.session_state.get(f"{prefix_key}_er_p", float(default_p)),
			step=0.01,
			disabled=disabled,
			key=f"{prefix_key}_er_p",
		)
		return {"p": p}
	if topology == "WS":
		default_k = defaults.get("WS", {}).get("k", 6)
		default_beta = defaults.get("WS", {}).get("beta", 0.1)
		k = st.number_input(
			f"{prefix} WS k",
			min_value=2,
			max_value=100,
			value=st.session_state.get(f"{prefix_key}_ws_k", int(default_k)),
			step=1,
			disabled=disabled,
			key=f"{prefix_key}_ws_k",
		)
		beta = st.number_input(
			f"{prefix} WS beta",
			min_value=0.0,
			max_value=1.0,
			value=st.session_state.get(f"{prefix_key}_ws_beta", float(default_beta)),
			step=0.05,
			disabled=disabled,
			key=f"{prefix_key}_ws_beta",
		)
		return {"k": int(k), "beta": float(beta)}
	default_m = defaults.get("BA", {}).get("m", 3)
	m = st.number_input(
		f"{prefix} BA m",
		min_value=1,
		max_value=20,
		value=st.session_state.get(f"{prefix_key}_ba_m", int(default_m)),
		step=1,
		disabled=disabled,
		key=f"{prefix_key}_ba_m",
	)
	return {"m": int(m)}


def _plot_curves(curves_df: pd.DataFrame) -> plt.Figure:
	"""Erstellt einen Plot der Robustheitskurven."""
	fig, ax = plt.subplots(figsize=(7, 5))
	mean_df = (
		curves_df.groupby(["mode", "scenario_type", "removed_frac"], dropna=False)["gcc_frac"]
		.mean()
		.reset_index()
	)
	grouped = mean_df.groupby(["mode", "scenario_type"], dropna=False)
	for (mode, scenario), group in grouped:
		group_sorted = group.sort_values("removed_frac")
		label = f"{mode} | {scenario}"
		ax.plot(
			group_sorted["removed_frac"],
			group_sorted["gcc_frac"],
			label=label,
			linewidth=2.0,
			antialiased=True,
		)
	ax.set_xlabel("Entfernter Anteil")
	ax.set_ylabel("GCC-Anteil")
	ax.set_title("Robustheitskurven")
	ax.legend()
	fig.tight_layout()
	return fig


def _export_outputs(curves_df: pd.DataFrame, auc_df: pd.DataFrame, meta: Dict[str, Any], label: str) -> None:
	"""Schreibt CSV/PNG in einen Run-Ordner unter outputs/."""
	outdir = _create_run_dir(Path("outputs"), label)
	meta = dict(meta)
	meta["output_dir"] = str(outdir)

	curves_df.to_csv(outdir / "curves.csv", index=False)
	auc_df.to_csv(outdir / "auc_summary.csv", index=False)
	(outdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

	fig = _plot_curves(curves_df)
	fig.savefig(outdir / "robustheitskurven.png", dpi=150)
	plt.close(fig)


def _create_run_dir(base_dir: Path, label: str) -> Path:
	"""Erzeugt einen Run-Ordner mit Label und Zeitstempel."""
	label = _sanitize_label(label)
	timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
	run_dir = base_dir / f"{label}_{timestamp}"
	run_dir.mkdir(parents=True, exist_ok=True)
	return run_dir


def _sanitize_label(label: str) -> str:
	"""Bereinigt Label für Ordnernamen."""
	return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)


def _build_run_label(config_source: str, experiment_name: str | None) -> str:
	"""Erzeugt ein Label für den Run-Ordner."""
	if experiment_name:
		return experiment_name
	return config_source.lower().replace(" ", "_").replace("+", "plus")


def _show_networks(config: Dict[str, Any], mode_label: str) -> None:
	"""Zeigt eine einfache Netzwerkvisualisierung und Basis-Metriken."""
	n_nodes = int(config["allgemein"]["N"])
	if n_nodes > 200:
		st.info("Visualisierung deaktiviert (N > 200).")
		return

	gp = create_gp_network(config, seed=int(config["allgemein"]["seed"]))
	st.subheader("GP")
	_plot_network(gp)
	_show_metrics(gp)

	if mode_label != "Konventionell":
		gc = create_gc_network(config, seed=int(config["allgemein"]["seed"]))
		st.subheader("GC")
		_plot_network(gc)
		_show_metrics(gc)


def _plot_network(graph: nx.Graph) -> None:
	"""Einfache Netzwerkdarstellung."""
	fig, ax = plt.subplots(figsize=(5, 4))
	pos = nx.spring_layout(graph, seed=42)
	nx.draw(graph, pos=pos, ax=ax, node_size=30, width=0.5)
	ax.set_axis_off()
	st.pyplot(fig)
	plt.close(fig)


def _show_metrics(graph: nx.Graph) -> None:
	"""Zeigt Basis-Metriken für das Netzwerk."""
	n_nodes = graph.number_of_nodes()
	n_edges = graph.number_of_edges()
	avg_degree = 2 * n_edges / n_nodes if n_nodes > 0 else 0.0
	clustering = nx.average_clustering(graph) if n_nodes > 1 else 0.0
	path_length = None
	if n_nodes > 1 and nx.is_connected(graph):
		path_length = nx.average_shortest_path_length(graph)

	st.write(
		{
			"Knoten": n_nodes,
			"Kanten": n_edges,
			"Durchschnittsgrad": round(avg_degree, 3),
			"Clustering": round(clustering, 3),
			"Mittlere Pfadlänge": round(path_length, 3) if path_length is not None else "n. a.",
		}
	)


if __name__ == "__main__":
	main()
