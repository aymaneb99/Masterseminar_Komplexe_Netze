from __future__ import annotations

from pathlib import Path
from typing import List
import sys

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config_loader import load_config
from src.simulation import run_experiment
from src.analysis import aggregate_and_compute_auc
from src.graph_factory import build_graph_from_config
from src.dynamic_visualization import compute_dynamic_states, draw_graph_state


# ------------- Hilfsfunktionen -----------------


def list_config_files(config_dir: str | Path = "configs") -> List[Path]:
    cfg_dir = Path(config_dir)
    if not cfg_dir.exists():
        return []
    return sorted(cfg_dir.glob("*.yaml"))


def run_simulation_with_config(config_path: Path):
    config = load_config(config_path)
    csv_path = run_experiment(config)
    df = pd.read_csv(csv_path)
    return config, csv_path, df


def run_simulation_with_manual_config(config: dict):
    csv_path = run_experiment(config)
    df = pd.read_csv(csv_path)
    return csv_path, df


def show_config_preview(config) -> None:
    st.subheader("Konfigurationsvorschau")
    st.json(config)


def show_results_ui(config, csv_path: Path, df: pd.DataFrame) -> None:
    st.success(f"Simulation abgeschlossen. Ergebnisse unter: {csv_path}")

    st.subheader("Rohdaten (erste Zeilen)")
    st.dataframe(df.head(50))

    available_metrics = [m for m in config.get("metrics", []) if m in df.columns]
    if not available_metrics:
        fallback = ["lcc_fraction", "average_path_length_lcc", "global_efficiency"]
        available_metrics = [m for m in fallback if m in df.columns]

    if not available_metrics:
        st.warning("Keine bekannten Metriken in den Ergebnissen gefunden.")
        return

    metric = st.selectbox(
        "Metrik für Robustheitsanalyse",
        options=available_metrics,
        index=0,
    )

    group_keys = config.get("analysis", {}).get("aggregate_by", ["graph_id", "attack_id"])

    st.subheader("AUC-Übersicht (Fläche unter der Robustheitskurve)")
    auc_df = aggregate_and_compute_auc(
        csv_path,
        metric_for_auc=metric,
        group_keys=group_keys,
    )
    st.dataframe(auc_df)

    st.subheader("Robustheitskurven")

    graph_ids = sorted(df["graph_id"].unique())
    selected_graph = st.selectbox("Graph auswählen", options=graph_ids)

    subset = df[df["graph_id"] == selected_graph]
    attack_ids = sorted(subset["attack_id"].unique())
    selected_attack = st.selectbox("Angriffsszenario auswählen", options=attack_ids)

    curve_df = (
        subset[subset["attack_id"] == selected_attack]
        .groupby("fraction_removed")[metric]
        .mean()
        .reset_index()
        .sort_values("fraction_removed")
    )

    if curve_df.empty:
        st.info("Keine Daten für diese Kombination vorhanden.")
        return

    fig, ax = plt.subplots()
    ax.plot(curve_df["fraction_removed"], curve_df[metric], marker="o")
    ax.set_xlabel("Anteil entfernte Knoten")
    ax.set_ylabel(metric)
    ax.set_title(f"Robustheitskurve – {selected_graph} / {selected_attack}")
    ax.grid(True)

    st.pyplot(fig)


# ------------- Streamlit-Layout -----------------


def main() -> None:
    st.set_page_config(
        page_title="Netzwerk-Resilienz – Interaktive Simulation",
        layout="wide",
    )

    st.title("Netzwerk-Resilienz – Interaktive Simulation")

    st.sidebar.header("Konfiguration")

    mode = st.sidebar.radio(
        "Eingabemodus",
        ["Manuell", "Szenario-Datei"],
        index=0,
    )

    if mode == "Manuell":
        run_manual_mode()
    else:
        run_config_file_mode()


# ---------- MANUELLER MODUS ---------------------


def run_manual_mode() -> None:
    # Knotenanzahl
    n = st.sidebar.number_input(
        "Knoten (n)",
        min_value=10,
        max_value=20000,
        step=10,
        value=300,
    )

    # Graph-Typ Auswahl
    graph_label = st.sidebar.selectbox(
        "Graph-Typ",
        options=[
            "ER (Erdős–Rényi)",
            "WS (Watts–Strogatz)",
            "BA (Barabási–Albert)",
        ],
        index=0,
    )

    graph_cfg = {"type": "synthetic", "repetitions": 1}

    if graph_label.startswith("ER"):
        model = "erdos_renyi"
        p = st.sidebar.number_input(
            "p (ER Kantenwahrscheinlichkeit)",
            min_value=0.0,
            max_value=1.0,
            value=0.01,
            step=0.001,
            format="%.3f",
        )
        graph_cfg.update({"model": model, "n": int(n), "p": float(p), "id": f"ER_n{n}_p{p:.3f}"})

    elif graph_label.startswith("WS"):
        model = "watts_strogatz"
        k = st.sidebar.number_input(
            "k (WS Anzahl Nachbarn)",
            min_value=2,
            max_value=int(n) - 1,
            value=10,
            step=1,
        )
        p = st.sidebar.number_input(
            "p (WS Rewire-Wahrscheinlichkeit)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.2f",
        )
        graph_cfg.update(
            {
                "model": model,
                "n": int(n),
                "k": int(k),
                "p": float(p),
                "id": f"WS_n{n}_k{k}_p{p:.2f}",
            }
        )

    else:  # BA
        model = "barabasi_albert"
        m = st.sidebar.number_input(
            "m (BA neue Kanten pro Knoten)",
            min_value=1,
            max_value=int(n) - 1,
            value=3,
            step=1,
        )
        graph_cfg.update(
            {
                "model": model,
                "n": int(n),
                "m": int(m),
                "id": f"BA_n{n}_m{m}",
            }
        )

    # Angriffstrategien
    st.sidebar.write("Strategien")
    selected_strategies = st.sidebar.multiselect(
        " ",
        options=["random", "degree", "betweenness"],
        default=["random", "degree", "betweenness"],
    )

    attacks = []
    if "random" in selected_strategies:
        attacks.append({"id": "random_failures", "type": "random"})
    if "degree" in selected_strategies:
        attacks.append({"id": "targeted_degree", "type": "targeted", "strategy": "degree"})
    if "betweenness" in selected_strategies:
        attacks.append({"id": "targeted_betweenness", "type": "targeted", "strategy": "betweenness"})

    if not attacks:
        st.sidebar.warning("Bitte mindestens eine Strategie auswählen.")
        return

    # Entfernungsschritt
    step = st.sidebar.slider(
        "Entfernungsschritt (Anteil)",
        min_value=0.01,
        max_value=0.5,
        value=0.02,
        step=0.01,
    )

    # Wiederholungen
    repetitions = st.sidebar.number_input(
        "Wiederholungen",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
    )
    graph_cfg["repetitions"] = int(repetitions)

    # Seed
    seed = st.sidebar.number_input(
        "Seed (Zufall)",
        min_value=0,
        max_value=1_000_000,
        value=42,
        step=1,
    )

    if st.sidebar.button("Simulation starten"):
        experiment_name = "manual_ui_experiment"

        fractions = list(np.arange(0.0, 1.0 + 1e-9, float(step)))

        config = {
            "experiment_name": experiment_name,
            "output_dir": "results",
            "random_seed": int(seed),
            "graphs": [graph_cfg],
            "attacks": attacks,
            "fractions": {"start": 0.0, "end": 1.0, "step": float(step)},
            "metrics": [
                "lcc_fraction",
                "average_path_length_lcc",
                "global_efficiency",
            ],
            "analysis": {
                "metric_for_auc": "lcc_fraction",
                "aggregate_by": ["graph_id", "attack_id"],
            },
        }

        with st.spinner("Simulation läuft..."):
            try:
                csv_path, df = run_simulation_with_manual_config(config)
            except Exception as e:
                st.error(f"Fehler bei der Simulation: {e}")
                return

        # Ergebnisse (Tabellen/Plots)
        show_results_ui(config, csv_path, df)

        # -------- Interaktive Netzvisualisierung --------
        st.markdown("---")
        st.subheader("Interaktive Netzvisualisierung")

        if graph_cfg["model"] == "barabasi_albert" and int(graph_cfg["n"]) > 3000:
            st.info("Graph ist sehr groß – Visualisierung könnte langsam werden.")
        # Auswahl, welche Strategie visualisiert werden soll
        vis_attack_ids = [a["id"] for a in attacks]
        vis_attack_id = st.selectbox(
            "Strategie für Visualisierung auswählen",
            options=vis_attack_ids,
        )

        attack_cfg = next(a for a in attacks if a["id"] == vis_attack_id)

        # Graph erneut erzeugen (frischer Zustand)
        base_graph = build_graph_from_config(graph_cfg, seed=int(seed))

        # Dynamische Zustände berechnen
        with st.spinner("Berechne Layout und Simulationsschritte für Visualisierung..."):
            positions, states = compute_dynamic_states(
                base_graph,
                attack_cfg=attack_cfg,
                fractions=fractions,
                seed=int(seed),
            )

        if not states:
            st.warning("Keine Zustände für die Visualisierung vorhanden.")
            return

        # Slider für Schritt
        step_index = st.slider(
            "Simulationsschritt auswählen",
            min_value=0,
            max_value=len(states) - 1,
            value=0,
        )
        state = states[step_index]
        fig = draw_graph_state(base_graph, positions, state)
        st.pyplot(fig)


# ---------- MODUS: SZENARIO-DATEI ---------------------


def run_config_file_mode() -> None:
    cfg_files = list_config_files("configs")

    if not cfg_files:
        st.warning(
            "Keine YAML-Konfigurationen gefunden. "
            "Lege Dateien unter `configs/` an (z. B. `synthetic_vs_synthetic.yaml`)."
        )
        return

    selected_cfg = st.sidebar.selectbox(
        "Szenario-Datei wählen",
        options=cfg_files,
        format_func=lambda p: p.name,
    )

    if selected_cfg is None:
        st.info("Bitte eine Konfigurationsdatei auswählen.")
        return

    try:
        config = load_config(selected_cfg)
        show_config_preview(config)
    except Exception as e:
        st.error(f"Fehler beim Laden der Konfiguration: {e}")
        return

    if st.button("Simulation starten"):
        with st.spinner("Simulation läuft..."):
            try:
                config, csv_path, df = run_simulation_with_config(selected_cfg)
            except Exception as e:
                st.error(f"Fehler bei der Simulation: {e}")
                return

        show_results_ui(config, csv_path, df)


if __name__ == "__main__":
    main()
