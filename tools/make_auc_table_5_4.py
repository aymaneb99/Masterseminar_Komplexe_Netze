from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Create a compact LaTeX table from robustness AUC CSV (for Kapitel 5.4)."
    )
    p.add_argument(
        "--csv",
        type=str,
        default="results/experiment/synthetic_robustness_comparison_robustness_auc_gcc_fraction.csv",
        help="Path to *_robustness_auc_*.csv produced by src.main analysis step.",
    )
    p.add_argument(
        "--out",
        type=str,
        default="results/experiment/auc_table_5_4.tex",
        help="Output .tex file path (LaTeX snippet, no preamble).",
    )
    p.add_argument(
        "--metric",
        type=str,
        default="gcc_fraction",
        help="Metric name used for AUC (only used to locate the AUC column if needed).",
    )
    return p.parse_args()


def _infer_auc_column(df: pd.DataFrame) -> str:
    """
    Try to find the AUC column robustly.
    Common names: 'auc', 'AUC', 'robustness_auc', 'auc_gcc_fraction', etc.
    """
    candidates = [
        "auc",
        "AUC",
        "robustness_auc",
        "auc_value",
        "area_under_curve",
    ]
    for c in candidates:
        if c in df.columns:
            return c

    # fallback: any column containing 'auc'
    for c in df.columns:
        if "auc" in c.lower():
            return c

    raise ValueError(
        f"Could not infer AUC column. Columns are: {list(df.columns)}"
    )


def _infer_attack_label(attack_id: str, attack_type: str | None, strategy: str | None) -> str:
    """
    Map attack rows into the three columns we want.
    """
    s = (strategy or "").lower()
    aid = (attack_id or "").lower()
    at = (attack_type or "").lower() if attack_type is not None else ""

    if "random" in aid or "random" in at:
        return "Random Failures"
    if "degree" in aid or s == "degree":
        return "Targeted (Degree)"
    if "between" in aid or "betweenness" in aid or "between" in s or "betweenness" in s:
        return "Targeted (Betweenness)"

    # fallback
    return attack_id


def _infer_model_label(model: str, graph_id: str) -> str:
    m = (model or "").lower()
    gid = (graph_id or "").lower()

    if "erdos" in m or "er" == m or "erdos" in gid:
        return "Erd\\H{o}s--R\\'enyi (ER)"
    if "watts" in m or "strogatz" in m or "ws" == m or "watts" in gid or "strogatz" in gid:
        return "Watts--Strogatz (WS)"
    if "barabasi" in m or "albert" in m or "ba" == m or "barabasi" in gid or "albert" in gid:
        return "Barab\\'asi--Albert (BA)"

    return model if model else graph_id


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"AUC CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # expected columns (but be lenient)
    for col in ["graph_id", "attack_id"]:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {csv_path}. Columns: {list(df.columns)}")

    auc_col = _infer_auc_column(df)

    # optional fields
    if "model" not in df.columns:
        df["model"] = ""
    if "attack_type" not in df.columns:
        df["attack_type"] = ""
    if "strategy" not in df.columns:
        df["strategy"] = ""

    # build pretty labels
    df["AttackLabel"] = df.apply(
        lambda r: _infer_attack_label(str(r["attack_id"]), str(r.get("attack_type", "")), str(r.get("strategy", ""))),
        axis=1,
    )
    df["ModelLabel"] = df.apply(
        lambda r: _infer_model_label(str(r.get("model", "")), str(r["graph_id"])),
        axis=1,
    )

    # Reduce to the three attacks we care about (if present)
    wanted = ["Random Failures", "Targeted (Degree)", "Targeted (Betweenness)"]
    df = df[df["AttackLabel"].isin(wanted)].copy()
    if df.empty:
        raise ValueError(
            "After filtering to Random/Degree/Betweenness, no rows left. "
            "Check attack_id/strategy names in your AUC CSV."
        )

    # If multiple graphs per model exist, take mean AUC (and keep also std for transparency)
    df[auc_col] = pd.to_numeric(df[auc_col], errors="coerce")
    df = df.dropna(subset=[auc_col])

    summary = (
        df.groupby(["ModelLabel", "AttackLabel"], as_index=False)[auc_col]
        .agg(["mean", "std", "count"])
        .reset_index()
    )

    # pivot into wide format
    wide_mean = summary.pivot(index="ModelLabel", columns="AttackLabel", values=("mean"))
    wide_std = summary.pivot(index="ModelLabel", columns="AttackLabel", values=("std"))
    wide_n = summary.pivot(index="ModelLabel", columns="AttackLabel", values=("count"))

    # Ensure column order
    for w in [wide_mean, wide_std, wide_n]:
        for c in wanted:
            if c not in w.columns:
                w[c] = pd.NA
        w = w[wanted]

    # Build LaTeX table snippet
    lines: list[str] = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{AUC der Robustheitskurven (größere Werte $\Rightarrow$ höhere Robustheit). "
                 r"Die Werte sind über Wiederholungen gemittelt; in Klammern steht die Standardabweichung.}")
    lines.append(r"\label{tab:auc_summary}")
    lines.append(r"\begin{tabular}{lccc}")
    lines.append(r"\hline")
    lines.append(r"Netzwerk & Random Failures & Targeted (Degree) & Targeted (Betweenness) \\")
    lines.append(r"\hline")

    for model_label in wide_mean.index:
        row = [model_label]
        for attack in wanted:
            m = wide_mean.loc[model_label, attack]
            s = wide_std.loc[model_label, attack]
            n = wide_n.loc[model_label, attack]

            if pd.isna(m):
                cell = r"--"
            else:
                # format: mean (std), keep 3 decimals; if n==1, std may be NaN
                if pd.isna(s) or (isinstance(n, (int, float)) and int(n) <= 1):
                    cell = f"{m:.3f}"
                else:
                    cell = f"{m:.3f} ({s:.3f})"
            row.append(cell)

        lines.append(" & ".join(row) + r" \\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    tex = "\n".join(lines) + "\n"

    out_path.write_text(tex, encoding="utf-8")
    print(f"[OK] Wrote LaTeX table: {out_path}")


if __name__ == "__main__":
    main()
