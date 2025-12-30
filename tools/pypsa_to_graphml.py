import pandas as pd
import networkx as nx
from pathlib import Path
from pandas.errors import ParserError

def pypsa_to_graphml(
    buses_path: str,
    lines_path: str,
    out_path: str = "data/real/pypsa_eur.graphml",
):
    # CSV laden
    buses = pd.read_csv(buses_path)

    
    try:
        lines = pd.read_csv(lines_path, quotechar="'", engine="python")
    except ParserError:
        # Fallback: versuche ohne Quotechar 
        print("[WARN] ParserError mit quotechar='\''. Versuche Fallback ohne quotechar …")
        lines = pd.read_csv(lines_path, engine="python", error_bad_lines=False)

    G = nx.Graph()  # ungerichteter Graph

    # Knoten hinzufügen
    id_col = "bus_id" if "bus_id" in buses.columns else "name"

    for _, row in buses.iterrows():
        bus_id = row[id_col]
        attrs = {
            "x": float(row.get("x", 0.0)),
            "y": float(row.get("y", 0.0)),
            "country": row.get("country", ""),
        }
        v_nom = row.get("v_nom", None)
        if v_nom is not None:
            attrs["v_nom"] = v_nom
        G.add_node(bus_id, **attrs)

    # Kanten hinzufügen
    required_cols = ["bus0", "bus1"]
    for col in required_cols:
        if col not in lines.columns:
            raise ValueError(f"Erwartete Spalte '{col}' fehlt in lines.csv. Gefundene Spalten: {list(lines.columns)}")

    for _, row in lines.iterrows():
        u = row["bus0"]
        v = row["bus1"]

        # Sicherheitshalber nur Kanten hinzufügen, wenn beide Knoten existieren
        if u not in G or v not in G:
            continue

        edge_attrs = {}
        length = row.get("length", None)
        if length is not None:
            try:
                edge_attrs["length"] = float(length)
            except (TypeError, ValueError):
                pass
        etype = row.get("type", None)
        if etype is not None:
            edge_attrs["type"] = etype
        G.add_edge(u, v, **edge_attrs)

    # Nur größte Komponente behalten (optional, macht das Netz sauberer)
    if G.number_of_nodes() > 0:
        gcc_nodes = max(nx.connected_components(G), key=len)
        G = G.subgraph(gcc_nodes).copy()

    # Zielordner erstellen
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Als GraphML speichern
    nx.write_graphml(G, out_path)  # Export als GraphML
    print(f"[OK] GraphML gespeichert unter: {out_path}")

if __name__ == "__main__":
    pypsa_to_graphml(
        "data/pypsa/buses.csv",
        "data/pypsa/lines.csv",
        "data/real/pypsa_eur.graphml",
    )
