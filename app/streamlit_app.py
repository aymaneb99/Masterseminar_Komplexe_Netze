from __future__ import annotations

from pathlib import Path
import sys
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

"""
Ensure the project root (one level above this file) is on sys.path so that
`import src.*` works when Streamlit runs the app from the `app/` directory.
"""
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config_loader import load_config
from src.simulation import run_experiment
from src.analysis import aggregate_and_compute_auc, plot_robustness_curve
from src.graph_factory import build_graph_from_config
from src.dynamic_visualization import compute_dynamic_states, draw_graph_state
from src.utils import hash_config



# Session State Setup (persistente UI-Zustände)
def ensure_session_state() -> None:
    if "last_run" not in st.session_state:
        st.session_state["last_run"] = None
    if "vis_cache" not in st.session_state:
        st.session_state["vis_cache"] = {}


def store_last_run(mode: str, config: Dict[str, Any], csv_path: Path) -> None:
    st.session_state["last_run"] = {
        "mode": mode,
        "config": config,
        "config_hash": hash_config(config),
        "csv_path": str(csv_path),
    }


def get_last_run() -> Dict[str, Any] | None:
    return st.session_state.get("last_run")


# Helper (kleine Hilfsfunktionen für UI/Config)

def list_config_files(config_dir: str | Path = "configs") -> List[Path]:
    cfg_dir = Path(config_dir)
    if not cfg_dir.exists():
        return []
    return sorted(cfg_dir.glob("*.yaml"))


def build_manual_config(
    graph_cfg: Dict[str, Any],
    attacks: List[Dict[str, Any]],
    step: float,
    seed: int,
    repetitions: int,
) -> Dict[str, Any]:

    fractions_cfg = {"start": 0.0, "end": 1.0, "step": float(step)}  # q-Schritte
    graph_cfg = dict(graph_cfg)
    graph_cfg["repetitions"] = int(repetitions)

    return {
        "experiment_name": "manual_ui_experiment",
        "output_dir": "results",
        "random_seed": int(seed),
        "graphs": [graph_cfg],
        "attacks": attacks,
        "fractions": fractions_cfg,
        "metrics": [
            "gcc_fraction",
            "gcc_size",
            "avg_path_length_gcc",
            "diameter_gcc",
            "global_efficiency",
            "global_clustering",
            "avg_local_clustering",
            "mean_degree",
            "max_degree",
            "degree_std",
        ],
        "analysis": {
            "metric_for_auc": "gcc_fraction",
            "aggregate_by": ["graph_id", "attack_id"],
        },
    }



# MAIN STREAMLIT APP (Routing & Seitenaufbau)

def main() -> None:
    st.set_page_config(
        page_title="Netzwerk-Resilienz – Interaktive Simulation",
        layout="wide",
    )
    ensure_session_state()

    st.title("Netzwerk-Resilienz – Interaktive Simulation")

    st.sidebar.header("Konfiguration")
    mode = st.sidebar.radio("Eingabemodus", ["Manuell", "Szenario-Datei"], index=0)

    if mode == "Manuell":
        run_manual_mode()
    else:
        run_config_file_mode()

    last_run = get_last_run()
    if last_run is not None:
        show_results_section(last_run)


# MANUAL MODE (interaktiv konfigurieren)

def run_manual_mode() -> None:

    n = st.sidebar.number_input(
        "Knoten (n)", min_value=10, max_value=20000, step=10, value=300,
    )

    graph_label = st.sidebar.selectbox(
        "Graph-Typ",
        options=["ER (Erdős–Rényi)", "WS (Watts–Strogatz)", "BA (Barabási–Albert)"],
        index=0,
    )

    graph_cfg: Dict[str, Any] = {"type": "synthetic"}

    if graph_label.startswith("ER"):
        model = "erdos_renyi"
        p = st.sidebar.number_input(
            "p (ER Kantenwahrscheinlichkeit)",
            min_value=0.0, max_value=1.0, value=0.01, step=0.001, format="%.3f",
        )
        graph_cfg.update({"model": model, "n": int(n), "p": float(p), "id": f"ER_n{n}_p{p:.3f}"})

    elif graph_label.startswith("WS"):
        model = "watts_strogatz"
        k = st.sidebar.number_input(
            "k (WS Anzahl Nachbarn)",
            min_value=2, max_value=int(n) - 1, value=10, step=1,
        )
        p = st.sidebar.number_input(
            "p (WS Rewire-Wahrscheinlichkeit)",
            min_value=0.0, max_value=1.0, value=0.1, step=0.01, format="%.2f",
        )
        graph_cfg.update({
            "model": model,
            "n": int(n),
            "k": int(k),
            "p": float(p),
            "id": f"WS_n{n}_k{k}_p{p:.2f}"
        })

    else:  # BA
        model = "barabasi_albert"
        m = st.sidebar.number_input(
            "m (BA neue Kanten pro Knoten)",
            min_value=1, max_value=int(n) - 1, value=3, step=1,
        )
        graph_cfg.update({
            "model": model,
            "n": int(n),
            "m": int(m),
            "id": f"BA_n{n}_m{m}"
        })

    # --- ATTACKS --- (Auswahl der Strategien)
    st.sidebar.write("Strategien (Ausfall-/Angriffsszenarien)")
    selected_strategies = st.sidebar.multiselect(
        " ", ["random", "degree", "betweenness"],
        default=["random", "degree", "betweenness"],
    )

    attacks: List[Dict[str, Any]] = []
    if "random" in selected_strategies:
        attacks.append({"id": "random_failures", "type": "random"})
    if "degree" in selected_strategies:
        attacks.append({"id": "targeted_degree", "type": "targeted", "strategy": "degree"})
    if "betweenness" in selected_strategies:
        attacks.append({"id": "targeted_betweenness", "type": "targeted", "strategy": "betweenness"})

    step = st.sidebar.slider(
        "Entfernungsschritt (q)",
        min_value=0.01, max_value=0.5, value=0.02, step=0.01,
    )

    repetitions = st.sidebar.number_input(
        "Wiederholungen", min_value=1, max_value=50, value=1, step=1,
    )

    seed = st.sidebar.number_input(
        "Seed", min_value=0, max_value=1_000_000, value=42, step=1,
    )

    if st.sidebar.button("Simulation starten", type="primary"):
        config = build_manual_config(graph_cfg, attacks, step, int(seed), int(repetitions))
        with st.spinner("Simulation läuft..."):
            try:
                csv_path = run_experiment(config)
            except Exception as e:
                st.error(f"Fehler bei Simulation: {e}")
                return

        store_last_run("manual", config, csv_path)
        st.success("Simulation abgeschlossen. Ergebnisse unten sichtbar.")


# CONFIG FILE MODE (Konfigurationsdatei verwenden)

def run_config_file_mode() -> None:

    cfg_files = list_config_files("configs")
    if not cfg_files:
        st.sidebar.warning("Keine YAML-Konfigurationen in /configs gefunden.")
        return

    selected_cfg = st.sidebar.selectbox(
        "Szenario-Datei wählen",
        options=cfg_files,
        format_func=lambda p: p.name,
    )

    if selected_cfg is None:
        return

    try:
        config = load_config(selected_cfg)
        st.subheader("Konfigurationsvorschau")
        st.json(config)
    except Exception as e:
        st.error(f"Fehler beim Laden der YAML: {e}")
        return

    if st.sidebar.button("Simulation starten", type="primary"):
        with st.spinner("Simulation läuft..."):
            try:
                csv_path = run_experiment(config)
            except Exception as e:
                st.error(f"Fehler bei der Simulation: {e}")
                return
        store_last_run("config_file", config, csv_path)
        st.success("Simulation abgeschlossen. Ergebnisse unten sichtbar.")


# RESULTS & VISUALISATION SECTION (Tabellen, Kurven, Visualisierung)

def show_results_section(last_run: Dict[str, Any]) -> None:

    csv_path = Path(last_run["csv_path"])
    config = last_run["config"]

    if not csv_path.exists():
        st.warning("Ergebnisdatei nicht gefunden. Bitte erneut simulieren.")
        return

    df = pd.read_csv(csv_path)

    st.markdown("---")
    st.subheader("Simulationsergebnisse")

    st.caption(f"Experiment: {config.get('experiment_name')} – Datei: {csv_path.name}")
    st.dataframe(df.head(50))

    # METRIK AUSWAHL (welche Spalte für S(q)/AUC)
    metrics_available = [m for m in config.get("metrics", []) if m in df.columns]
    if not metrics_available:
        fallback = ["gcc_fraction", "avg_path_length_gcc", "diameter_gcc",
                    "global_efficiency", "global_clustering",
                    "avg_local_clustering", "mean_degree", "max_degree", "degree_std"]
        metrics_available = [m for m in fallback if m in df.columns]

    metric = st.selectbox("Metrik für Robustheitsanalyse S(q)", metrics_available)

    # AUC (Robustheit) berechnen und anzeigen
    st.subheader("Robustheit (AUC über S(q) )")
    group_keys = config.get("analysis", {}).get("aggregate_by", ["graph_id", "attack_id"])
    auc_df = aggregate_and_compute_auc(csv_path, metric_for_auc=metric, group_keys=group_keys)
    st.dataframe(auc_df)

    # ROBUSTHEITSKURVE (mittlere Kurve je Angriff)
    st.subheader("Robustheitskurven")

    graph_ids = sorted(df["graph_id"].unique())
    selected_graph = st.selectbox("Graph auswählen", graph_ids)

    subset = df[df["graph_id"] == selected_graph]
    attack_ids = sorted(subset["attack_id"].unique())
    selected_attack = st.selectbox("Angriff auswählen", attack_ids)

    fig_curve = plot_robustness_curve(df, selected_graph, selected_attack, metric)
    st.pyplot(fig_curve)

    # NEU: Dynamische Visualisierung für ALLE Modi (manuell + YAML)
    show_dynamic_visualization(config, selected_attack)


# DYNAMIC VISUALIZATION FOR ALL MODES (Layout + Zustände)

def show_dynamic_visualization(config: Dict[str, Any], attack_id: str) -> None:

    st.markdown("---")
    st.subheader("Interaktive Netzvisualisierung (Strukturzerfall)")

    graph_cfg = config["graphs"][0]
    attacks = config["attacks"]
    attack_cfg = next((a for a in attacks if a["id"] == attack_id), None)
    if attack_cfg is None:
        st.info("Für dieses Angriffsszenario keine Visualisierung verfügbar.")
        return

    # Lade Basisgraph
    seed = int(config.get("random_seed", 42))
    base_graph = build_graph_from_config(graph_cfg, seed=seed)

    n = base_graph.number_of_nodes()
    if n > 6000:
        st.warning(
            f"Achtung: Das Netz ist sehr groß ({n} Knoten). "
            "Die Visualisierung kann langsam sein."
        )

    # Fractions (aus Config ableiten)
    frac_cfg = config["fractions"]
    if isinstance(frac_cfg, dict) and "step" in frac_cfg:
        step = float(frac_cfg["step"])
        fractions = list(np.arange(0.0, 1.0 + 1e-9, step))
    elif isinstance(frac_cfg, dict) and "values" in frac_cfg:
        fractions = [float(v) for v in frac_cfg["values"]]
    else:
        fractions = [0.0, 0.25, 0.5, 0.75, 1.0]

    # Caching der Layouts/Zustände für schnelle Navigation
    cache_key = f"{graph_cfg['id']}__{attack_cfg['id']}__{seed}__{len(fractions)}"
    vis_cache = st.session_state["vis_cache"]

    if cache_key in vis_cache:
        positions, states = vis_cache[cache_key]
    else:
        with st.spinner("Berechne Netzlayout und Zerstörungsschritte..."):
            positions, states = compute_dynamic_states(
                base_graph,
                attack_cfg=attack_cfg,
                fractions=fractions,
                seed=seed,
            )
        vis_cache[cache_key] = (positions, states)
        st.session_state["vis_cache"] = vis_cache

    if not states:
        st.info("Keine Visualisierungszustände verfügbar.")
        return

    step_index = st.slider(
        "Simulationsschritt (q)", 
        min_value=0, 
        max_value=len(states) - 1, 
        value=0,
        key="vis_step_slider"
    )

    fig = draw_graph_state(base_graph, positions, states[step_index])
    st.pyplot(fig)



if __name__ == "__main__":
    main()
