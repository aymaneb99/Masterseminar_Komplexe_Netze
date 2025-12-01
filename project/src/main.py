from __future__ import annotations

import argparse
from pathlib import Path

from .config_loader import load_config
from .simulation import run_experiment
from .analysis import aggregate_and_compute_auc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Network robustness simulations for smart-grid-like networks."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="Path to a YAML configuration file.",
    )
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip post-hoc AUC (Robustness) analysis.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()  # CLI-Argumente lesen
    cfg_path = Path(args.config)
    config = load_config(cfg_path)  # YAML laden

    csv_path = run_experiment(config)  # Simulation ausführen
    print(f"[INFO] Simulation finished. Results written to: {csv_path}")

    if args.no_analysis:
        return

    analysis_cfg = config.get("analysis", {})
    metric_for_auc = analysis_cfg.get("metric_for_auc", "gcc_fraction")
    group_keys = analysis_cfg.get("aggregate_by", ["graph_id", "attack_id"])

    print(f"[INFO] Computing robustness AUC for metric '{metric_for_auc}'...")
    auc_df = aggregate_and_compute_auc(csv_path, metric_for_auc, group_keys)
    out = csv_path.parent / f"{config['experiment_name']}_robustness_auc_{metric_for_auc}.csv"
    auc_df.to_csv(out, index=False)
    print(f"[INFO] AUC (Robustheit) summary written to: {out}")


if __name__ == "__main__":
    main()
