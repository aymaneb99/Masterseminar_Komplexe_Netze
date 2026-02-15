#!/usr/bin/env python3
"""Erstellt einen gemeinsamen Plot aus mehreren Experiment-Ordnern."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd


def load_experiment_data(output_dir: Path) -> Tuple[pd.DataFrame, Dict]:
    """Lädt Kurvendaten und Metadaten aus einem Experiment-Ordner."""
    curves_path = output_dir / "curves.csv"
    meta_path = output_dir / "meta.json"
    
    if not curves_path.exists():
        raise FileNotFoundError(f"curves.csv nicht gefunden in {output_dir}")
    
    curves = pd.read_csv(curves_path)
    
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)
    
    return curves, meta


def extract_label_from_dir(dir_name: str, param: str = "auto") -> str:
    """Ermittelt ein Label aus dem Ordnernamen."""
    parts = dir_name.split("_")
    
    r_val = None
    q_val = None
    
    for part in parts:
        # r-Wert lesen
        if part.startswith("r") and len(part) >= 2 and part[1:].isdigit():
            r_val = part[1:]
        # q-Wert lesen
        if part.startswith("q") and len(part) >= 2:
            val = part[1:]
            if val == "10":
                q_val = "1.0"
            elif val == "06":
                q_val = "0.6"
            elif val == "08":
                q_val = "0.8"
            elif val == "03":
                q_val = "0.3"
            elif len(val) == 2 and val.isdigit():
                q_val = f"0.{val[0]}"
    
    # Label nach Modus wählen
    if param == "r" and r_val:
        return f"r={r_val}"
    elif param == "q" and q_val:
        return f"q={q_val}"
    elif param == "auto":
        # Automatisch aus dem ersten Segment ableiten
        if len(parts) >= 2:
            first_param = parts[1]
            if first_param.startswith("r"):
                return f"r={r_val}" if r_val else dir_name
            elif first_param.startswith("q"):
                return f"q={q_val}" if q_val else dir_name
    
    # Standardfall
    if r_val:
        return f"r={r_val}"
    if q_val:
        return f"q={q_val}"
    return dir_name


def compute_mean_curve(curves: pd.DataFrame) -> pd.DataFrame:
    """Berechnet die gemittelte Kurve über alle Runs."""
    return curves.groupby("removed_frac").agg(
        gcc_mean=("gcc_frac", "mean"),
        gcc_std=("gcc_frac", "std")
    ).reset_index()


def plot_combined_curves(
    data: List[Tuple[str, pd.DataFrame]],
    title: str,
    output_path: Path,
    show_std: bool = True,
):
    """Erstellt einen kombinierten Plot mit mehreren Kurven."""

    # Farben für die Kurven
    colors = ["#E64A19", "#1976D2", "#388E3C", "#7B1FA2", "#FBC02D", "#00796B"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for idx, (label, curves) in enumerate(data):
        mean_curve = compute_mean_curve(curves)
        color = colors[idx % len(colors)]
        
        # Mittelwertkurve
        ax.plot(
            mean_curve["removed_frac"],
            mean_curve["gcc_mean"],
            label=label,
            color=color,
            linewidth=2,
            marker="o",
            markersize=4,
        )
        
        # Streuung als Fläche
        if show_std and "gcc_std" in mean_curve.columns:
            ax.fill_between(
                mean_curve["removed_frac"],
                mean_curve["gcc_mean"] - mean_curve["gcc_std"],
                mean_curve["gcc_mean"] + mean_curve["gcc_std"],
                color=color,
                alpha=0.15,
            )
    
    ax.set_xlabel("Anteil entfernter Knoten", fontsize=12)
    ax.set_ylabel("GCC-Anteil im GP", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"✓ Plot gespeichert: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Kombinierte Visualisierung mehrerer Robustheitskurven"
    )
    parser.add_argument(
        "directories",
        nargs="+",
        help="Pfade zu den Output-Verzeichnissen der Experimente"
    )
    parser.add_argument(
        "--title", "-t",
        default="Robustheitskurven – Parameter-Sweep",
        help="Titel des Plots"
    )
    parser.add_argument(
        "--output", "-o",
        default="combined_plot.png",
        help="Ausgabepfad für den Plot"
    )
    parser.add_argument(
        "--no-std",
        action="store_true",
        help="Keine Standardabweichung anzeigen"
    )
    
    args = parser.parse_args()
    
    # Daten sammeln
    data: List[Tuple[str, pd.DataFrame]] = []
    
    for dir_path in args.directories:
        path = Path(dir_path)
        if not path.exists():
            print(f"⚠ Verzeichnis nicht gefunden: {path}", file=sys.stderr)
            continue
        
        try:
            curves, meta = load_experiment_data(path)
            label = extract_label_from_dir(path.name)
            data.append((label, curves))
            print(f"✓ Geladen: {path.name} → Label: {label}")
        except Exception as e:
            print(f"⚠ Fehler beim Laden von {path}: {e}", file=sys.stderr)
    
    if not data:
        print("Keine Daten geladen. Abbruch.", file=sys.stderr)
        sys.exit(1)
    
    # Nach Label sortieren
    data.sort(key=lambda x: x[0])
    
    # Plot erstellen
    output_path = Path(args.output)
    plot_combined_curves(data, args.title, output_path, show_std=not args.no_std)


if __name__ == "__main__":
    main()
