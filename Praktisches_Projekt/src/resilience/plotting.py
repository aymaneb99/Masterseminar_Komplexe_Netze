from __future__ import annotations
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt


def save_robustness_plot(df: pd.DataFrame, out_path: str, title: Optional[str] = None) -> None:
    plt.figure(figsize=(8, 5))
    # Erwartete df-Spalten: graph_label, strategy, fraction_removed, lcc_frac
    for (graph_label, strategy), g in df.groupby(["graph_label", "strategy"], sort=False):
        g = g.sort_values("fraction_removed")
        label = f"{graph_label} – {strategy}"
        plt.plot(g["fraction_removed"], g["lcc_frac"], label=label)

    plt.xlabel("Entfernter Anteil")
    plt.ylabel("Anteil LCC")
    if title:
        plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8, loc="best")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
