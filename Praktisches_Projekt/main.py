from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from src.resilience.graphs import GraphSpec
from src.resilience.simulate import ExperimentSpec, run_experiment, summarize
from src.resilience.plotting import save_robustness_plot
from src.resilience.config import load_scenario


def build_default_graphs(n: int):
    return [
        GraphSpec("ER", {"n": n, "p": 0.01}),
        GraphSpec("WS", {"n": n, "k": max(2, int(0.02 * n) // 2 * 2), "p": 0.1}),
        GraphSpec("BA", {"n": n, "m": 3}),
    ]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simulation der Netzwerk-Resilienz")
    p.add_argument("--n", type=int, default=300, help="Anzahl Knoten für Demo-Graphen")
    p.add_argument("--repeats", type=int, default=1, help="Anzahl Wiederholungen pro Graph")
    p.add_argument("--step", type=float, default=0.02, help="Schrittweite des Entfernungsanteils")
    p.add_argument("--out", type=str, default="outputs", help="Ausgabeverzeichnis")
    p.add_argument("--seed", type=int, default=42, help="Basis-Zufallssamen")
    p.add_argument(
        "--strategies",
        type=str,
        default="random,degree,betweenness",
        help="Kommaseparierte Strategien: random,degree,betweenness",
    )
    p.add_argument(
        "--config",
        type=str,
        default=None,
        help="Pfad zu YAML/JSON-Szenariodatei (überschreibt CLI-Defaults)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.out)

    if args.config:
        scenario = load_scenario(args.config)
        spec = scenario.experiment
        # scenario output dir overrides --out if provided in file
        if scenario.output_dir is not None:
            out_dir = scenario.output_dir
    else:
        graphs = build_default_graphs(args.n)
        strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]
        spec = ExperimentSpec(
            graph_specs=graphs,
            strategies=strategies,
            step=args.step,
            repeats=args.repeats,
            seed=args.seed,
        )

    # Ausgabeverzeichnis nach möglicher Szenario-Überschreibung erstellen
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = run_experiment(spec)
    df.to_csv(out_dir / "results_timeseries.csv", index=False)

    summary = summarize(df)
    summary.to_csv(out_dir / "results_summary.csv", index=False)

    # One combined plot
    save_robustness_plot(df, str(out_dir / "robustness_curves.png"), title="Robustheitskurven")

    print(f"Geschrieben: {out_dir / 'results_timeseries.csv'}")
    print(f"Geschrieben: {out_dir / 'results_summary.csv'}")
    print(f"Geschrieben: {out_dir / 'robustness_curves.png'}")


if __name__ == "__main__":
    main()
