from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plot robustness curve S(q) from experiment_results.csv (supports survivor-normalization)."
    )
    p.add_argument(
        "--csv",
        type=str,
        default="results/experiment/experiment_results.csv",
        help="Path to experiment_results.csv",
    )
    p.add_argument(
        "--out",
        type=str,
        default="figures/abb5_random_failures_curves.pdf",
        help="Output file path (recommended: .pdf).",
    )
    p.add_argument(
        "--attack-id",
        type=str,
        default="random_failures",
        help="attack_id to plot (default: random_failures).",
    )
    p.add_argument(
        "--label-mode",
        type=str,
        choices=["graph_id", "model"],
        default="model",
        help="Legend labels: 'model' or 'graph_id'.",
    )
    p.add_argument(
        "--metric",
        type=str,
        choices=["gcc_fraction", "gcc_fraction_survivors"],
        default="gcc_fraction_survivors",
        help=(
            "Which robustness metric to plot. "
            "'gcc_fraction' = gcc_size / N0, "
            "'gcc_fraction_survivors' = gcc_size / (N0 - removed)."
        ),
    )
    return p.parse_args()


def _require_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")


def _infer_n0_by_graph(df: pd.DataFrame) -> dict:
    """
    Infer original node count N0 per graph_id from rows with fraction_removed == 0.
    We use gcc_size at q=0 as proxy for N0 (assuming the initial graph is connected
    or at least GCC is the intended baseline size).
    """
    base = df[df["fraction_removed"] == 0.0].copy()
    if base.empty:
        raise ValueError("Cannot infer N0: no rows with fraction_removed == 0.0 found.")
    n0 = base.groupby("graph_id")["gcc_size"].max().to_dict()
    return n0


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    _require_columns(
        df,
        [
            "graph_id",
            "attack_id",
            "fraction_removed",
            "repetition",
            "model",
            "gcc_fraction",
            "gcc_size",
            "nodes_removed",
        ],
    )

    # Filter to the requested attack
    df = df[df["attack_id"] == args.attack_id].copy()
    if df.empty:
        raise ValueError(
            f"No rows found for attack_id='{args.attack_id}'. "
            f"Available attack_id values: {sorted(pd.read_csv(csv_path)['attack_id'].unique())}"
        )

    # Ensure numeric fields
    for col in ["fraction_removed", "gcc_fraction", "repetition", "gcc_size", "nodes_removed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["fraction_removed", "repetition", "gcc_size", "nodes_removed"])

    # Choose label field
    label_field = "model" if args.label_mode == "model" else "graph_id"

    # Build the metric to plot
    if args.metric == "gcc_fraction":
        df["S_plot"] = pd.to_numeric(df["gcc_fraction"], errors="coerce")
        ylabel = "Relative size of largest connected component S(q) = |GCC| / N"
    else:
        # survivor-normalized: |GCC| / (N0 - removed)
        n0_map = _infer_n0_by_graph(df)
        df["N0"] = df["graph_id"].map(n0_map)
        df["survivors"] = df["N0"] - df["nodes_removed"]
        df.loc[df["survivors"] <= 0, "survivors"] = pd.NA
        df["S_plot"] = df["gcc_size"] / df["survivors"]
        ylabel = "Connectivity among survivors S_surv(q) = |GCC| / (N - removed)"

    df = df.dropna(subset=["S_plot"])

    # Aggregate over repetitions: mean S(q) per (label, q)
    agg = (
        df.groupby([label_field, "fraction_removed"], as_index=False)["S_plot"]
        .mean()
        .rename(columns={"S_plot": "S"})
        .sort_values([label_field, "fraction_removed"])
    )

    # Plot
    plt.figure()

    for label in sorted(agg[label_field].unique()):
        sub = agg[agg[label_field] == label]
        plt.plot(sub["fraction_removed"], sub["S"], label=str(label))

    plt.xlabel("Fraction of removed nodes q")
    plt.ylabel(ylabel)
    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.02)
    plt.legend(title="Network", fontsize=9)
    plt.tight_layout()

    plt.savefig(out_path, bbox_inches="tight")
    print(f"[OK] Saved: {out_path}")


if __name__ == "__main__":
    main()
