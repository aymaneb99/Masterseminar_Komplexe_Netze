from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

# Ensure src on path when running directly
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resilience.graphs import GraphSpec
from resilience.simulate import ExperimentSpec, run_experiment, summarize
from resilience.config import load_scenario

st.set_page_config(page_title="Netzwerk-Resilienz – Simulator", layout="wide")

st.title("Netzwerk-Resilienz – Interaktive Simulation")

with st.sidebar:
    st.header("Konfiguration")
    mode = st.radio("Eingabemodus", ["Manuell", "Szenario-Datei"], horizontal=True)

    if mode == "Szenario-Datei":
        file = st.file_uploader("YAML- oder JSON-Szenario hochladen", type=["yaml", "yml", "json"])
        run_btn = st.button("Szenario ausführen")
        if run_btn and file is not None:
            # Save to a temp file to reuse existing loader
            tmp_path = ROOT / "_uploaded_scenario.yaml"
            tmp_path.write_bytes(file.getvalue())
            scenario = load_scenario(tmp_path)
            spec = scenario.experiment
            out_dir = scenario.output_dir or (ROOT / "outputs" / "interactive")
            out_dir.mkdir(parents=True, exist_ok=True)

            with st.spinner("Simulation wird ausgeführt…"):
                df = run_experiment(spec)
                summary = summarize(df)
            st.success("Fertig")
    else:
        # Manual controls
        n = st.number_input("Knoten (n)", min_value=20, max_value=5000, value=300, step=20)
        graph_type = st.selectbox("Graph-Typ", ["ER", "WS", "BA"], index=0)
        col1, col2 = st.columns(2)
        if graph_type == "ER":
            p = col1.number_input("p (ER Kantenwahrscheinlichkeit)", min_value=0.0, max_value=1.0, value=0.01, step=0.005, format="%.3f")
            params = {"n": int(n), "p": float(p)}
        elif graph_type == "WS":
            k = col1.number_input("k (WS nächste Nachbarn)", min_value=2, max_value=max(2, int(n)-1), value=max(2, int(0.02*n)//2*2), step=2)
            p = col2.number_input("p (WS Umverdrahtungswahrscheinlichkeit)", min_value=0.0, max_value=1.0, value=0.1, step=0.05, format="%.2f")
            params = {"n": int(n), "k": int(k), "p": float(p)}
        else:
            m = col1.number_input("m (BA neue Kanten pro Knoten)", min_value=1, max_value=max(1, int(n)-1), value=3, step=1)
            params = {"n": int(n), "m": int(m)}

        strategies = st.multiselect("Strategien", ["random", "degree", "betweenness"], default=["random", "degree", "betweenness"]) 
        step = st.slider("Entfernungsschritt (Anteil)", min_value=0.01, max_value=0.20, value=0.02, step=0.01)
        repeats = st.number_input("Wiederholungen", min_value=1, max_value=10, value=1)
        seed = st.number_input("Seed (Zufall)", min_value=0, max_value=1000000, value=42)
        run_btn = st.button("Simulation starten")

        if run_btn:
            spec = ExperimentSpec(
                graph_specs=[GraphSpec(graph_type, params)],
                strategies=list(strategies),
                step=float(step),
                repeats=int(repeats),
                seed=int(seed),
            )
            with st.spinner("Simulation wird ausgeführt…"):
                df = run_experiment(spec)
                summary = summarize(df)
            st.success("Fertig")

# Display results if available in session state
if "df" in locals():
    st.subheader("Robustheitskurven")
    # Plot LCC fraction curve(s)
    fig = px.line(df, x="fraction_removed", y="lcc_frac", color="strategy", line_group="graph_label",
                  title="Anteil LCC vs. entfernter Anteil")
    st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Zeitreihe (erste 10 Zeilen)")
        st.dataframe(df.head(10))
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Zeitreihe als CSV herunterladen", data=csv_bytes, file_name="results_timeseries.csv", mime="text/csv")
    with colB:
        st.subheader("Zusammenfassung")
        st.dataframe(summary)
        csv2 = summary.to_csv(index=False).encode("utf-8")
        st.download_button("Zusammenfassung als CSV herunterladen", data=csv2, file_name="results_summary.csv", mime="text/csv")

    st.caption("Tipp: Verwenden Sie eine Szenario-YAML, um mehrere Graphen und Strategien gebündelt auszuführen.")
