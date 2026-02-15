# Praxisprojekt MSKN

Dieses Projekt simuliert die Robustheit eines Smart Grids.

Es gibt zwei Netze:
- `GP`: Stromnetz
- `GC`: Kommunikationsnetz

Das Projekt vergleicht Ausfälle in verschiedenen Szenarien, zum Beispiel zufällig oder gezielt.

## Inhaltsverzeichnis

1. [Projektziel](#projektziel)
2. [Projektstruktur](#projektstruktur)
3. [Voraussetzungen](#voraussetzungen)
4. [Installation](#installation)
5. [Start mit CLI](#start-mit-cli)
6. [Start mit Streamlit](#start-mit-streamlit)
7. [Konfiguration](#konfiguration)
8. [Ausgaben](#ausgaben)

## Projektziel

Ziel ist ein einfacher Vergleich der Netz-Robustheit:
- konventionelles Netz (nur `GP`)
- Smart Grid (`GP` + `GC` + Abhängigkeiten)

Bewertet wird mit:
- `GCC` (größte zusammenhängende Komponente)
- `AUC` (Fläche unter der Robustheitskurve)

## Projektstruktur

- [config/defaults.yaml](config/defaults.yaml): Standardwerte
- [config/experiment.yaml](config/experiment.yaml): Experimente
- [src/networks](src/networks): Netz-Erzeugung
- [src/interdependence](src/interdependence): Abhängigkeiten und Kaskade
- [src/scenarios](src/scenarios): Ausfallszenarien
- [src/metrics](src/metrics): GCC und AUC
- [src/sim](src/sim): Simulation und Aggregation
- [src/cli/run_simulation.py](src/cli/run_simulation.py): CLI-Start
- [app/streamlit_app.py](app/streamlit_app.py): Streamlit-App

## Voraussetzungen

- Python 3.11+
- pip

## Installation

Im Projektordner:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start mit CLI

Standardlauf:

```bash
python src/cli/run_simulation.py
```

Lauf mit Experiment aus [config/experiment.yaml](config/experiment.yaml):

```bash
python src/cli/run_simulation.py --experiment E1_er_random
```

Anderer Ausgabeordner:

```bash
python src/cli/run_simulation.py --outdir outputs
```

## Start mit Streamlit

Im Projektordner:

```bash
streamlit run app/streamlit_app.py
```

Dann im Browser Parameter setzen und Run starten.

## Konfiguration

- Standardwerte stehen in [config/defaults.yaml](config/defaults.yaml).
- Experimente stehen in [config/experiment.yaml](config/experiment.yaml).
- In der Streamlit-App können Werte manuell geändert werden.

## Ausgaben

Die Ergebnisse landen im Ordner `outputs/`.

Typische Dateien:
- `curves.csv`
- `auc_summary.csv`
- `meta.json`
- `robustheitskurven.png`

## 12. Typische Workflows
Diese Workflows lassen sich über [config/experiment.yaml](config/experiment.yaml) direkt anstoßen:
- **Baseline (konventionell):** `konventionell_gp_only`
- **Smart Grid (mit Interdependenz):** `smartgrid_mit_interdependenz`
- **Angriff auf GP vs. GC (random):** `angriff_gp_random` und `angriff_gc_random`
- **Random vs. targeted:** `smartgrid_mit_interdependenz` kombiniert mit `targeted_degree_gp` oder `targeted_betweenness_gp`
- **Variation von Kopplung und Redundanz:** `q_niedrig` / `q_hoch`, sowie `redundanz_1` / `redundanz_3`