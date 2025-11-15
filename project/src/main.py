from __future__ import annotations

import argparse
from pathlib import Path

from .config_loader import load_config
from .simulation import run_experiment
from .analysis import aggregate_and_compute_auc, plot_robustness_curves


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Network robustness simulations for smart-grid-like networks."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip post-hoc analysis (AUC, plots).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)

    csv_path = run_experiment(config)
    print(f"[INFO] Simulation finished. Results written to: {csv_path}")

    if args.no_analysis:
        return

    analysis_cfg = config.get("analysis", {})
    metric_for_auc = analysis_cfg.get("metric_for_auc", "lcc_fraction")
    group_keys = analysis_cfg.get("aggregate_by", ["graph_id", "attack_id"])

    print(f"[INFO] Running analysis for metric: {metric_for_auc}")
    auc_df = aggregate_and_compute_auc(
        csv_path,
        metric_for_auc=metric_for_auc,
        group_keys=group_keys,
    )

    auc_out = csv_path.parent / f"{config['experiment_name']}_auc_{metric_for_auc}.csv"
    auc_df.to_csv(auc_out, index=False)
    print(f"[INFO] AUC summary written to: {auc_out}")

    # Plot robustness curves
    print("[INFO] Plotting robustness curves...")
    plot_robustness_curves(
        csv_path,
        metric=metric_for_auc,
        group_by=group_keys,
        output_dir=csv_path.parent,
    )
    print("[INFO] Plots written to:", csv_path.parent)


if __name__ == "__main__":
    main()
