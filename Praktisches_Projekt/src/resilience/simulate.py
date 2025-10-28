from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import networkx as nx

from .graphs import GraphSpec, make_graph
from .attacks import simulate_progressive_node_removal
from .metrics import auc_trapz, critical_fraction


@dataclass(frozen=True)
class ExperimentSpec:
    graph_specs: List[GraphSpec]
    strategies: List[str]
    step: float = 0.02
    repeats: int = 1
    seed: Optional[int] = None


def run_experiment(spec: ExperimentSpec) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    base_seed = spec.seed if spec.seed is not None else 42

    for gi, gspec in enumerate(spec.graph_specs):
        for rep in range(spec.repeats):
            gseed = base_seed + gi * 1000 + rep
            G = make_graph(gspec, seed=gseed)

            for strategy in spec.strategies:
                sseed = base_seed + gi * 1000 + rep * 10 + hash(strategy) % 1000
                sim_rows = simulate_progressive_node_removal(
                    G, strategy=strategy, step=spec.step, seed=sseed
                )
                for r in sim_rows:
                    rows.append({
                        "graph": gspec.kind,
                        "graph_label": gspec.label(),
                        "strategy": strategy,
                        "repeat": rep,
                        **r,
                    })

    df = pd.DataFrame(rows)
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet AUC und kritischen Anteil (f_crit) pro Graph/Strategie/Wiederholung."""
    summaries: List[Dict[str, Any]] = []

    for (graph_label, strategy, repeat), g in df.groupby(["graph_label", "strategy", "repeat"], sort=False):
        xs = g["fraction_removed"].values
        ys = g["lcc_frac"].values
        auc = auc_trapz(xs, ys)
        fc = critical_fraction(xs, ys, threshold=0.5)
        summaries.append({
            "graph_label": graph_label,
            "strategy": strategy,
            "repeat": repeat,
            "auc": auc,
            "f_crit_lcc<=0.5": fc,
        })

    return pd.DataFrame(summaries)
