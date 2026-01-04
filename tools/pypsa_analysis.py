import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from pathlib import Path

# ---------------------------------------------------
# Laden des Graphen
# ---------------------------------------------------

def load_graph(graphml_path: str):
    print(f"[INFO] Lade GraphML: {graphml_path}")
    G = nx.read_graphml(graphml_path)
    print(f"[OK] Knoten: {G.number_of_nodes()}, Kanten: {G.number_of_edges()}")
    return G


# ---------------------------------------------------
# A: Gradverteilung + Log-Log Plot
# ---------------------------------------------------

def plot_degree_distribution(G, outdir):
    degrees = [d for _, d in G.degree()]
    degrees = np.array(degrees)

    Path(outdir).mkdir(parents=True, exist_ok=True)

    # Histogramm
    plt.figure(figsize=(6, 4))
    plt.hist(degrees, bins=50, color="steelblue")
    plt.xlabel("Degree k")
    plt.ylabel("Count")
    plt.title("Degree Distribution")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{outdir}/degree_distribution.png", dpi=200)
    plt.close()

    # Log-Log Plot
    deg, cnt = np.unique(degrees, return_counts=True)

    plt.figure(figsize=(6, 4))
    plt.scatter(deg, cnt, color="darkred", s=12)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Degree k (log)")
    plt.ylabel("P(k) (log)")
    plt.title("Degree Distribution (Log-Log)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{outdir}/degree_distribution_loglog.png", dpi=200)
    plt.close()

    print("[OK] Gradverteilungsplots gespeichert.")


# ---------------------------------------------------
# B: Clustering-Auswertung
# ---------------------------------------------------

def analyze_clustering(G, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)

    global_c = nx.transitivity(G)
    local_c = nx.average_clustering(G)

    with open(f"{outdir}/clustering_stats.txt", "w") as f:
        f.write(f"Global Clustering: {global_c:.4f}\n")
        f.write(f"Average Local Clustering: {local_c:.4f}\n")

    print(f"[OK] Clustering:\n Global: {global_c:.4f}\n Local: {local_c:.4f}")


# ---------------------------------------------------
# C: Vergleich Robustheit PyPSA vs synthetische Netze
# ---------------------------------------------------

def compare_robustness(pypsa_csv, synthetic_csv, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)

    df_p = pd.read_csv(pypsa_csv)
    df_s = pd.read_csv(synthetic_csv)

    # Nur random failures als Baseline für fairen Vergleich
    df_p = df_p[df_p["attack_id"] == "random_failures"]
    df_s = df_s[df_s["attack_id"] == "random_failures"]

    metric = "gcc_fraction"

    # Mittelwert über Wiederholungen bilden
    curve_p = df_p.groupby("fraction_removed")[metric].mean().reset_index()
    curve_s = df_s.groupby("fraction_removed")[metric].mean().reset_index()

    plt.figure(figsize=(6, 4))
    plt.plot(curve_p["fraction_removed"], curve_p[metric], label="PyPSA-Eur (real)", lw=2)
    plt.plot(curve_s["fraction_removed"], curve_s[metric], label="Synthetic (avg)", lw=2)
    plt.xlabel("Fraction removed q")
    plt.ylabel("GCC fraction S(q)")
    plt.title("Robustness Comparison: PyPSA vs Synthetic")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{outdir}/robustness_comparison.png", dpi=200)
    plt.close()

    print("[OK] Robustheitsvergleich gespeichert.")


# ---------------------------------------------------
# Main
# ---------------------------------------------------

if __name__ == "__main__":
    graph_path = "data/real/pypsa_eur.graphml"
    outdir = "analysis_results"

    G = load_graph(graph_path)

    plot_degree_distribution(G, outdir)
    analyze_clustering(G, outdir)

    print("\n[HINWEIS] Für Robustheitsvergleich benötigst du 2 Resultate:")
    print("- CSV aus PyPSA-Simulation")
    print("- CSV aus synthetischer Simulation")
    print("→ Danach compare_robustness(pypsa_csv, synthetic_csv, outdir)")
