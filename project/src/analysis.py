from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import matplotlib.pyplot as plt

from .utils import trapezoidal_auc


def aggregate_and_compute_auc(
    csv_path: str | Path,
    metric_for_auc: str = "lcc_fraction",
    group_keys: List[str] | None = None,
) -> pd.DataFrame:
    """
    Load results CSV, aggregate over repetitions, and compute AUC for each
    (graph, attack, ...) group with respect to metric_for_auc.

    Returns a DataFrame with group keys, mean curves, and AUC values.
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    if group_keys is None:
        group_keys = ["graph_id", "attack_id"]

    # group by graph/attack and repetition; sort by fraction
    grouped = df.groupby(group_keys + ["repetition"])

    # for each repetition: compute AUC
    auc_rows = []
    for key, sub in grouped:
        sub_sorted = sub.sort_values("fraction_removed")
        x = sub_sorted["fraction_removed"].values
        y = sub_sorted[metric_for_auc].values
        auc = trapezoidal_auc(x, y)

        auc_rows.append(
            {
                **{k: v for k, v in zip(group_keys + ["repetition"], key)},
                "auc_" + metric_for_auc: auc,
            }
        )

    auc_df = pd.DataFrame(auc_rows)

    # aggregate AUC over repetitions (mean, std)
    agg = (
        auc_df.groupby(group_keys)
        .agg(
            auc_mean=(f"auc_{metric_for_auc}", "mean"),
            auc_std=(f"auc_{metric_for_auc}", "std"),
            n_reps=("repetition", "nunique"),
        )
        .reset_index()
    )

    return agg


def plot_robustness_curves(
    csv_path: str | Path,
    metric: str = "lcc_fraction",
    group_by: List[str] | None = None,
    output_dir: str | Path | None = None,
) -> None:
    """
    Plot mean robustness curves with respect to the given metric for each group.

    E.g. group_by = ["graph_id", "attack_id"].
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    if group_by is None:
        group_by = ["graph_id", "attack_id"]

    if output_dir is None:
        output_dir = csv_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # compute mean over repetitions for each fraction
    group_cols = group_by + ["fraction_removed"]
    agg = df.groupby(group_cols)[metric].mean().reset_index()

    # now group by (graph, attack) to plot curves
    curve_groups = agg.groupby(group_by)

    for key, sub in curve_groups:
        sub_sorted = sub.sort_values("fraction_removed")
        x = sub_sorted["fraction_removed"].values
        y = sub_sorted[metric].values

        label = "_".join(str(k) for k in key)
        plt.figure()
        plt.plot(x, y, marker="o")
        plt.xlabel("Fraction of removed nodes")
        plt.ylabel(metric)
        plt.title(f"Robustness curve – {label}")
        plt.grid(True)

        filename = f"robustness_{metric}_" + "_".join(str(k) for k in key) + ".png"
        plt.tight_layout()
        plt.savefig(output_dir / filename)
        plt.close()
