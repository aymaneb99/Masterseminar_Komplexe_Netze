# Netzwerk-Resilienz – Praktisches Projekt

Dieses Projekt implementiert die im Exposé beschriebenen Analysen zur Resilienz komplexer Netzwerke.

Funktionen:
- Erzeugung von Beispielnetzwerken (Erdős–Rényi, Watts–Strogatz, Barabási–Albert)
- Störungsszenarien: zufällige Ausfälle und gezielte Angriffe (Grad, Zwischenzentralität)
- Kennzahlen: Größe der größten verbundenen Komponente (LCC), mittlere Pfadlänge (auf LCC), globale Effizienz
- Zusammenfassungen: Fläche unter der Robustheitskurve (AUC), kritischer Anteil (LCC ≤ 0.5)
- CSV-Exports und Plot der Robustheitskurven

## Installation

Benötigt Python 3.10+.

1) (Optional) Virtuelle Umgebung erstellen und aktivieren
2) Abhängigkeiten installieren:

```
pip install -r requirements.txt
```

## Kurzanleitung

Minimalbeispiel ausführen (erzeugt CSVs und Plots in `outputs/`):

```
python main.py
```

Optionen anzeigen:

```
python main.py -h
```

Beispiel mit größerem Graphen und mehreren Wiederholungen:

```
python main.py --n 500 --repeats 2 --step 0.02 --out outputs
```

## Szenario-Dateien (YAML/JSON)

Statt Parameter in der CLI zu setzen, können Szenariodateien genutzt werden:

Beispiel: `scenarios/demo.yaml`

```
experiment:
	seed: 42
	step: 0.05
	repeats: 1
	strategies: [random, degree, betweenness]
	graphs:
		- kind: ER
			params: { n: 300, p: 0.01 }
		- kind: WS
			params: { n: 300, k: 6, p: 0.1 }
		- kind: BA
			params: { n: 300, m: 3 }
output:
	dir: outputs/scenario_demo
```

Ausführung:

```
python main.py --config scenarios/demo.yaml
```

Die `output.dir` aus der Datei überschreibt `--out`.

## Interaktive Visualisierung (Streamlit)

Eine interaktive App ist enthalten. Sie erlaubt:
- Parametrisierung (n, Graph-Typ, Strategien, Schrittweite, Seed)
- Ausführung von Simulationen
- Plot der Robustheitskurven
- Download der CSVs
- Laden einer Szenario-Datei

Starten der App:

```
streamlit run app_streamlit.py
```

Hinweis: Die App nutzt Plotly zur interaktiven Darstellung.

## Dateien

- `main.py` – CLI-Einstieg, führt Experimente und Export durch
- `src/resilience/graphs.py` – Generatoren für ER/WS/BA
- `src/resilience/metrics.py` – Metriken (LCC, Pfadlänge, Effizienz, AUC, kritischer Anteil)
- `src/resilience/attacks.py` – Simulation von Ausfällen/Angriffen
- `src/resilience/simulate.py` – Orchestrierung, DataFrame-Build
- `src/resilience/plotting.py` – Robustheitskurven als Plot speichern

## Annahmen

- Ziel ist eine demonstrative, reproduzierbare Analyse; gezielte Angriffe werden adaptiv berechnet (Zentralitäten werden nach jedem Schritt neu berechnet). Das ist korrekt, aber bei sehr großen Graphen rechenintensiv; für große Instanzen kann statisches Ranking (einmalige Sortierung) schneller sein.
- Mittlere Pfadlänge wird auf der LCC berechnet. Für leere oder triviale Graphen werden NaN-Werte gesetzt.


