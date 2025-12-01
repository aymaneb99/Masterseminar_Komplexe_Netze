from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import matplotlib.pyplot as plt

from .utils import trapezoidal_auc


def aggregate_and_compute_auc(
    csv_path: str | Path,
    metric_for_auc: str = "gcc_fraction",
    group_keys: List[str] | None = None,
) -> pd.DataFrame:
    """
    Load results CSV, aggregate over repetitions, and compute AUC
    for each (graph, attack, ...) group.

    Im Kontext der Arbeit:
      - AUC über S(q) (hier z.B. gcc_fraction) entspricht Rob (Robustheit).
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)  # Ergebnisse laden

    if group_keys is None:
        group_keys = ["graph_id", "attack_id"]

    grouped = df.groupby(group_keys + ["repetition"])  # je Gruppe/Rep

    auc_rows = []
    for key, sub in grouped:
        sub_sorted = sub.sort_values("fraction_removed")  # Kurve in q-Reihenfolge
        x = sub_sorted["fraction_removed"].values
        y = sub_sorted[metric_for_auc].values
        auc = trapezoidal_auc(x, y)
        auc_rows.append(
            {
                **{k: v for k, v in zip(group_keys + ["repetition"], key)},
                "robustness_auc_" + metric_for_auc: auc,
            }
        )

    auc_df = pd.DataFrame(auc_rows)
    agg = (
        auc_df.groupby(group_keys)
        .agg(
            robustness_auc_mean=(f"robustness_auc_{metric_for_auc}", "mean"),
            robustness_auc_std=(f"robustness_auc_{metric_for_auc}", "std"),
            n_reps=("repetition", "nunique"),
        )
        .reset_index()
    )
    return agg


def plot_robustness_curve(
    df: pd.DataFrame,
    graph_id: str,
    attack_id: str,
    metric: str,
) -> plt.Figure:
    """
    Plot a robustness curve for the given graph/attack combination.

    Die x-Achse entspricht q (Anteil entfernte Knoten),
    die y-Achse z.B. S(q) = gcc_fraction.
    """
    subset = df[(df["graph_id"] == graph_id) & (df["attack_id"] == attack_id)]
    curve_df = (
        subset.groupby("fraction_removed")[metric]
        .mean()
        .reset_index()
        .sort_values("fraction_removed")
    )

    fig, ax = plt.subplots()
    ax.plot(curve_df["fraction_removed"], curve_df[metric], marker="o")
    ax.set_xlabel("Fraction of removed nodes q")
    ax.set_ylabel(metric)
    ax.set_title(f"Robustness curve – {graph_id} / {attack_id}")
    ax.grid(True)
    fig.tight_layout()
    return fig
