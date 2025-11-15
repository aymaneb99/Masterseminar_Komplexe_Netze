from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import csv
import math

import numpy as np

from .graph_factory import build_graph_from_config
from .attacks import compute_attack_order
from .metrics import compute_metrics


def _build_fraction_list(fractions_cfg: Any) -> List[float]:
    """
    Convert 'fractions' section in config into a sorted list [0,1].
    Supports:
      - dict with 'start', 'end', 'step'
      - dict with 'values': [...]
      - direct list of values
    """
    if isinstance(fractions_cfg, dict):
        if "values" in fractions_cfg:
            vals = [float(v) for v in fractions_cfg["values"]]
            return sorted(max(0.0, min(1.0, v)) for v in vals)

        start = float(fractions_cfg["start"])
        end = float(fractions_cfg["end"])
        step = float(fractions_cfg["step"])
        if step <= 0:
            raise ValueError("'fractions.step' must be > 0.")

        vals = list(np.arange(start, end + 1e-9, step))
        return [max(0.0, min(1.0, float(v))) for v in vals]

    if isinstance(fractions_cfg, list):
        vals = [float(v) for v in fractions_cfg]
        return sorted(max(0.0, min(1.0, v)) for v in vals)

    raise ValueError("Unsupported 'fractions' format.")


def run_experiment(config: Dict[str, Any]) -> Path:
    """
    Run the full experiment and write a CSV file with all simulation results.
    """
    experiment_name = config.get("experiment_name", "experiment")
    base_output_dir = Path(config.get("output_dir", "results"))
    output_dir = base_output_dir / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)

    random_seed_base = int(config.get("random_seed", 42))
    fractions = _build_fraction_list(config["fractions"])
    metrics_requested = config.get(
        "metrics",
        ["lcc_fraction", "average_path_length_lcc", "global_efficiency"],
    )

    rows: List[Dict[str, Any]] = []

    for graph_cfg in config["graphs"]:
        graph_id = graph_cfg["id"]
        repetitions = int(graph_cfg.get("repetitions", 1))

        for rep in range(repetitions):
            seed = random_seed_base + rep
            graph = build_graph_from_config(graph_cfg, seed=seed)
            original_n = graph.number_of_nodes()

            for attack_cfg in config["attacks"]:
                attack_id = attack_cfg["id"]
                attack_type = attack_cfg["type"]
                strategy = attack_cfg.get("strategy", "")

                attack_order = compute_attack_order(graph, attack_cfg, seed=seed)

                for frac in fractions:
                    frac_clamped = max(0.0, min(1.0, float(frac)))
                    k = int(round(frac_clamped * original_n))
                    k = min(k, original_n)

                    damaged = graph.copy()
                    damaged.remove_nodes_from(attack_order[:k])

                    m_all = compute_metrics(damaged, original_n)

                    row: Dict[str, Any] = {
                        "experiment": experiment_name,
                        "graph_id": graph_id,
                        "graph_type": graph_cfg["type"],
                        "model": graph_cfg.get("model", ""),
                        "repetition": rep,
                        "attack_id": attack_id,
                        "attack_type": attack_type,
                        "strategy": strategy,
                        "fraction_removed": frac_clamped,
                        "nodes_removed": k,
                    }

                    for m in metrics_requested:
                        row[m] = m_all.get(m, math.nan)

                    rows.append(row)

    if not rows:
        raise RuntimeError("No results produced. Check your config.")

    csv_path = output_dir / f"{experiment_name}_results.csv"
    fieldnames = list(rows[0].keys())

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return csv_path
