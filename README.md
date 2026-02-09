# Robustheit und Fehlertoleranz eines Smart Grids 

Dieses Projekt untersucht die **strukturelle Robustheit** eines Smart Grids als **zweischichtiges Netzwerk**:
- **GP**: physisches Stromnetz (Power Grid)
- **GC**: Kommunikationsnetz (Communication Grid)

Im Smart-Grid-Fall werden Abhängigkeiten zwischen beiden Schichten modelliert (Interdependenz). Als Referenz dient der konventionelle Fall (nur GP).

## 1. Einordnung & Zielsetzung
- Stromnetze sind kritische Infrastrukturen: Ausfälle einzelner Komponenten können die Konnektivität und damit die Versorgungssicherheit beeinträchtigen.
- Smart Grids erweitern das konventionelle Stromnetz um Kommunikations- und Steuerungsebene. Damit entstehen zusätzliche Abhängigkeiten und potenziell neue Ausfallpfade.
- Ein reines Modell des physischen Netzes (nur GP) greift deshalb zu kurz, wenn Kommunikationsausfälle indirekt die Funktionsfähigkeit von Stromkomponenten beeinflussen.
- Eine netzwerkbasierte Analyse ist sinnvoll, wenn die Fragestellung auf **Topologie, Konnektivität, Knotenbedeutung** und **Ausfallmechanismen** fokussiert (statt auf detaillierter Physik).

## 2. Modellidee 
### Zweischichtiges Modell
- **GP (physisch):** Knoten und Kanten repräsentieren Komponenten und Verbindungen des Stromnetzes.
- **GC (kommunikativ):** Knoten und Kanten repräsentieren Kommunikations- bzw. IT-Strukturen.

### Interdependenz (hier konkret)
- Ein GP-Knoten kann von einem oder mehreren GC-Knoten abhängig sein.
- Die Abhängigkeit ist **binär**: Ein GP-Knoten gilt als funktionsfähig, wenn **mindestens eine** seiner zugeordneten GC-Abhängigkeiten funktionsfähig ist.
- Fallen die zugeordneten GC-Knoten aus, gilt der GP-Knoten als ausgefallen.

### Binär funktionsfähig / nicht funktionsfähig
- Knoten werden nur als „aktiv“ oder „ausgefallen“ betrachtet.
- Es werden keine Teilzustände, Lastgrenzen oder Überlastungen modelliert.

### Abgrenzung (bewusst modelliert / bewusst nicht modelliert)
**Modelliert:**
- Topologische Netzstrukturen (ER/WS/BA)
- Zufällige und gezielte Knotenausfälle
- GC → GP Abhängigkeiten (optional, anteilig gekoppelt, optional redundant)
- Auswertung der Konnektivität im GP über GCC und AUC

**Nicht modelliert:**
- Lastflüsse, Spannung, Leitungsparameter und physikalische Stabilität
- Schutz- und Regelungstechnik im Detail
- Datenflüsse, Latenzen oder Protokolle im Kommunikationsnetz
- Rückkopplung GP → GC (keine dynamische Kaskade zwischen Schichten)

## 3. Abgrenzung: Konventionelles Netz vs. Smart Grid
### Konventioneller Fall (nur GP)
- Es wird ausschließlich das physische Netz erzeugt und durch Ausfälle gestört.
- Die Robustheit wird direkt auf dem verbleibenden GP ausgewertet.

### Smart-Grid-Fall (GP + GC + Abhängigkeiten)
- Zusätzlich zum GP wird ein Kommunikationsnetz GC erzeugt.
- Optional werden Dependency Links erzeugt: ein Anteil der GP-Knoten hängt von GC ab.

### Qualitativ andere Ausfallmechanismen
- Im konventionellen Fall wirken Ausfälle direkt auf GP.
- Im Smart-Grid-Fall kann ein Ausfall im GC **indirekt** Ausfälle im GP verursachen, ohne dass im GP selbst zunächst etwas „angegriffen“ wurde.

### Relevanz eines Angriffs auf GC
- Das Kommunikationsnetz kann strukturell zentrale Knoten besitzen (z. B. Steuerungsknoten). 
- Ein Angriff oder Ausfall in GC kann dadurch eine überproportionale Wirkung auf die Funktionsfähigkeit des GP entfalten, wenn viele GP-Knoten von wenigen GC-Knoten abhängen.

## 4. Störszenarien
### Zufällige Ausfälle (random)
- Motivation: ungeplante, nicht zielgerichtete Störungen (z. B. Wetter, Alterung, zufällige Defekte).
- Umsetzung: Knoten werden in reproduzierbarer Zufallsreihenfolge entfernt; für steigende Entfernungsanteile wachsen die Ausfallmengen monoton.

### Gezielte Angriffe (targeted)
- Motivation: bewusste Angriffe auf strukturell wichtige Knoten (z. B. Hubs, zentrale Steuerknoten).
- Umsetzung: Knoten werden anhand einer Zentralität im Ausgangsgraphen sortiert und dann schrittweise entfernt.

### Zentralitätsmaße (intuitiv)
- **Degree:** Knoten mit vielen direkten Nachbarn gelten als wichtig, da sie viele Verbindungen bündeln.
- **Betweenness:** Knoten, die häufig auf kürzesten Wegen liegen, gelten als wichtig, da sie „Vermittler“ zwischen Bereichen des Netzes sind.

### Angriffspunkte (GP vs. GC)
- Der Angriff kann auf dem physischen Netz (GP) oder – im Smart-Grid-Fall – auf dem Kommunikationsnetz (GC) definiert werden.
- Bei Angriff auf GC können zusätzliche GP-Ausfälle durch Interdependenzen ausgelöst werden.

## 5. Robustheitsmetriken
### Größte Zusammenhangskomponente (GCC)
- Misst, wie groß der größte zusammenhängende Teil des Netzes ist.
- Hier als **Anteil der Knoten** in der größten Komponente im verbleibenden GP.
- Sinnvoll, weil Konnektivität eine Grundvoraussetzung für funktionale Netzstrukturen ist (ohne physikalische Details zu modellieren).

### Robustheitskurve
- Aufgetragen wird: **entfernter Anteil** (x-Achse) gegen **GCC-Anteil im GP** (y-Achse).
- Eine Kurve, die langsam abfällt, deutet auf höhere strukturelle Robustheit hin.

### AUC (Fläche unter der Kurve)
- Eine einzelne Kennzahl erleichtert den Vergleich über viele Runs hinweg.
- Höhere AUC bedeutet, dass über den gesamten Entfernungsbereich hinweg im Mittel mehr Konnektivität im GP erhalten bleibt.

## 6. Projektstruktur
Die Struktur ist modular, damit Netzgenerierung, Szenarien, Interdependenz und Auswertung getrennt bleiben.

### Strukturdiagramm (ASCII)
```
						  +----------------------------+
						  |  config/defaults.yaml     |
						  +-------------+--------------+
										|
										v
						  +----------------------------+
						  |  config/experiment.yaml   |
						  |  (Overrides, optional)    |
						  +-------------+--------------+
										|
										v
  +----------------+   +----------------------------+   +------------------+
  | gp.py          |   | sim/simulation.py         |   | metrics (GCC/AUC)|
  | (GP-Generator) +-->| - Netze erzeugen          +-->| Auswertung GP     |
  +----------------+   | - Ausfälle + Propagation  |   +------------------+
  +----------------+   | - GCC-Kurve berechnen     |
  | gc.py          |   +-------------+--------------+
  | (GC-Generator) +-----------------+              
  +----------------+                 |
  +----------------+                 v
  | links.py       |      +----------------------------+
  | (Interdepend.) +----->| sim/orchestrator.py        |
  +----------------+      | - Runs aggregieren         |
						  | - AUC-Statistik            |
						  +-------------+--------------+
										|
						 +--------------+--------------+
						 |                             |
						 v                             v
			+-----------------------+      +-----------------------+
			| cli/run_simulation.py |      | app/streamlit_app.py  |
			| CSV/PNG/JSON-Export   |      | GUI + Export          |
			+-----------------------+      +-----------------------+
```

### Konfiguration
- [config/defaults.yaml](config/defaults.yaml): Standardparameter (Seed, Runs, Topologien, Interdependenz, Szenario, Metriken).
- [config/experiment.yaml](config/experiment.yaml): Beispiel-Experimente als Overrides (ohne Duplikation der Defaults).

### Netzwerke
- [src/networks/gp.py](src/networks/gp.py): Erzeugt GP (ER/WS/BA), stellt Zusammenhängigkeit sicher.
- [src/networks/gc.py](src/networks/gc.py): Erzeugt GC (ER/WS/BA), stellt Zusammenhängigkeit sicher.

### Interdependenz
- [src/interdependence/links.py](src/interdependence/links.py): Erzeugt Dependency Links (Partial Coupling + Redundanz) und propagiert GC → GP-Ausfälle.

### Störszenarien
- [src/scenarios/random_failures.py](src/scenarios/random_failures.py): Reproduzierbare Zufallsausfälle als Ausfallmengen pro Anteil.
- [src/scenarios/targeted_failures.py](src/scenarios/targeted_failures.py): Gezielte Ausfälle nach Degree oder Betweenness (einmalige Berechnung auf Ausgangsgraph).

### Metriken
- [src/metrics/gcc.py](src/metrics/gcc.py): GCC-Anteil im GP.
- [src/metrics/auc.py](src/metrics/auc.py): AUC der Robustheitskurve (Trapezregel; ergänzt Randpunkte bei Bedarf).

### Simulation
- [src/sim/simulation.py](src/sim/simulation.py): Einzelrun (Netze → Ausfälle → Propagation → GCC-Kurve).
- [src/sim/orchestrator.py](src/sim/orchestrator.py): Mehrfachruns, sammelt Kurvendaten und aggregiert AUC (Mittelwert/Std).

### Ausführung
- [src/cli/run_simulation.py](src/cli/run_simulation.py): CLI/Demo-Run (Config laden, Orchestrator starten, CSV/PNG/JSON exportieren).
- [app/streamlit_app.py](app/streamlit_app.py): Streamlit-Oberfläche (Parameter, Run, Plot, Tabellen, Downloads, optional Netzvisualisierung).

## 7. Parameter-Referenz (Konfiguration)
Die Parameter werden in [config/defaults.yaml](config/defaults.yaml) definiert und optional in [config/experiment.yaml](config/experiment.yaml) überschrieben. In der GUI können die Werte zusätzlich manuell angepasst werden (GUI hat Priorität).

### 7.1 Allgemein (allgemein)
- **seed**: Startwert für den Zufallszahlengenerator (Reproduzierbarkeit).
- **runs**: Anzahl der Wiederholungen pro Experiment (für Mittelwerte/Std).
- **schrittweite**: Anteil der Knoten, der pro Schritt entfernt wird (z. B. 0.05 = 5 %).
- **N**: Anzahl der Knoten pro Netz (GP und GC).

### 7.2 Netzwerkgenerierung GP (gp)
- **topologie**: Netzwerkmodell für das physische Netz (ER, WS, BA).
- **parameter.ER.p**: Kantenwahrscheinlichkeit im Erdős–Rényi‑Modell.
- **parameter.WS.k**: Anzahl der Nachbarn im Ringgitter (gerade Zahl empfohlen).
- **parameter.WS.beta**: Rewiring‑Wahrscheinlichkeit im Watts–Strogatz‑Modell.
- **parameter.BA.m**: Anzahl neuer Kanten pro hinzugefügtem Knoten im Barabási–Albert‑Modell.

### 7.3 Netzwerkgenerierung GC (gc)
- **topologie**: Netzwerkmodell für das Kommunikationsnetz (ER, WS, BA).
- **parameter**: Analog zu GP (ER/WS/BA) mit denselben Bedeutungen.

### 7.4 Interdependenz (interdependenz)
- **aktiv**: Schaltet Abhängigkeiten GC → GP ein oder aus.
- **q**: Anteil der GP‑Knoten, die von GC abhängig sind (0–1).
- **r**: Redundanz pro abhängigem GP‑Knoten (Anzahl GC‑Abhängigkeiten, r ≥ 1).
- **GC_to_GP**: Richtung der Abhängigkeit (Standard: true).

### 7.5 Störszenarien (stoerszenarien)
- **szenario_typ**: "random" oder "targeted".
- **targeted_metrik**: "degree" oder "betweenness" (nur bei targeted).
- **angreifbares_netz**: "GP" oder "GC" (GC nur im Smart‑Grid‑Modus sinnvoll).

### 7.6 Modi (modi)
- **modi**: Liste der auszuführenden Modi, z. B. [konventionell, smart_grid].
	Wird nicht gesetzt, laufen standardmäßig beide Modi.
	Für GC‑Angriffe sollte **modi: [smart_grid]** gesetzt werden.

## 8. Installation & Voraussetzungen
- Python: **3.11 oder neuer**
- Empfohlen: virtuelle Umgebung

Beispiel (macOS/Linux):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 9. Ausführen des Projekts
### 9.1 CLI / Demo-Run
Start im Projektverzeichnis:
```bash
python src/cli/run_simulation.py
```

Optional mit Experiment aus [config/experiment.yaml](config/experiment.yaml):
```bash
python src/cli/run_simulation.py --experiment smartgrid_mit_interdependenz
```

Optional mit anderem Output-Verzeichnis:
```bash
python src/cli/run_simulation.py --outdir outputs
```

Erzeugte Dateien im Output-Verzeichnis:
- `curves.csv` (Kurvendaten pro Run und Anteil)
- `auc_summary.csv` (AUC-Mittelwert/Std über Runs)
- `meta.json` (Metadaten, z. B. Runs, Seed-Basis, Laufzeit)
- `robustheitskurven.png` (Plot der Robustheitskurven)

### 9.2 Grafische Oberfläche (Streamlit)
Start im Projektverzeichnis:
```bash
streamlit run app/streamlit_app.py
```

**Sidebar-Parameter (kurz):**
- Modus: Konventionell / Smart Grid / Vergleich
- Allgemein: N, Seed, Runs, Schrittweite
- GP/GC: Topologie und Parameter
- Interdependenz: aktiv, q, r, Richtung (GC → GP)
- Szenario: random oder targeted; bei targeted zusätzlich Metrik
- Angriffsziel: GP oder (im Smart-Grid/Vergleich) GC

**Tabs:**
- *Ergebnisse:* Robustheitskurven (Plot) und AUC-Tabelle
- *Daten:* vollständige DataFrames + Download als CSV
- *Netzwerk:* einfache Visualisierung von GP/GC **nur bei N ≤ 200**; bei größeren N wird die Visualisierung deaktiviert
- *Info:* kurze Modellannahmen

**Export:**
- Die App schreibt CSV/PNG/JSON nach `outputs/` (analog zur CLI).

## 10. Interpretation der Ergebnisse
- Der zentrale Vergleich ist **Konventionell vs. Smart Grid** bei gleicher Parametrisierung von GP (und ggf. GC).
- Wenn Smart-Grid-Kurven schneller abfallen, deutet das darauf hin, dass **zusätzliche Abhängigkeiten** die strukturelle Robustheit reduzieren.
- Unterschiede zwischen random und targeted zeigen, ob die Robustheit stark von wenigen „wichtigen“ Knoten abhängt.
- Ein Angriff auf GC ist besonders relevant, wenn bei aktivierter Interdependenz viele GP-Knoten von wenigen GC-Knoten abhängen (hohes q, geringe Redundanz r).
- AUC dient als kompaktes Maß: höhere AUC bedeutet im Mittel höhere Konnektivität im GP über alle Entfernungsgrade.

## 11. Reproduzierbarkeit
- Der Seed wird zentral über die Konfiguration gesteuert.
- Mehrfachläufe werden reproduzierbar erzeugt, indem pro Run der Seed als `seed_base + run_id` verwendet wird.
- Vergleichbarkeit ergibt sich aus gleicher Schrittweite, gleicher Netzgenerierung und identischen Szenario-Definitionen.

## 12. Typische Workflows
Diese Workflows lassen sich über [config/experiment.yaml](config/experiment.yaml) direkt anstoßen:
- **Baseline (konventionell):** `konventionell_gp_only`
- **Smart Grid (mit Interdependenz):** `smartgrid_mit_interdependenz`
- **Angriff auf GP vs. GC (random):** `angriff_gp_random` und `angriff_gc_random`
- **Random vs. targeted:** `smartgrid_mit_interdependenz` kombiniert mit `targeted_degree_gp` oder `targeted_betweenness_gp`
- **Variation von Kopplung und Redundanz:** `q_niedrig` / `q_hoch`, sowie `redundanz_1` / `redundanz_3`

## 13. Einschränkungen & Modellgrenzen
- Die Ergebnisse sind **topologisch** zu interpretieren: Es geht um Konnektivität, nicht um reale Netzphysik.
- GCC kann Robustheit im Sinne „zusammenhängender Struktur“ abbilden, sagt aber nichts über Spannungsstabilität oder Lastflüsse aus.
- Interdependenz wirkt nur in Richtung GC → GP; Rückwirkungen, dynamische Kaskaden oder zeitliche Prozesse werden nicht abgebildet.
- Die Netzmodelle (ER/WS/BA) sind abstrakt und ersetzen keine realen Netzpläne.

## 14. Erweiterungsmöglichkeiten
- Dynamische Kaskaden (mehrstufige Propagation und Rückkopplungen)
- Physikalische Modelle (Lastfluss, Überlast, Schutzmechanismen)
- Weitere Interdependenzrichtungen und -regeln (z. B. GP → GC oder bidirektional)
- Weitere Robustheitsmetriken (z. B. Effizienz, Fragmentierung, Pfadlängen-basierte Maße)


Command liste: 

python src/cli/run_simulation.py experiment_E1_baseline.yaml E1_baseline_random_gp
python src/cli/run_simulation.py experiment_E1_baseline.yaml E1_baseline_targeted_gp

python src/cli/run_simulation.py experiment_E3_attack_on_gc.yaml E3_attack_gc_random

python src/cli/run_simulation.py experiment_E4_random_vs_targeted.yaml E4_random_gc
python src/cli/run_simulation.py experiment_E4_random_vs_targeted.yaml E4_targeted_gc_betweenness

python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q0_r1
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q0_r2
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q03_r1
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q03_r2
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q06_r1
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q06_r2
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q10_r1
python src/cli/run_simulation.py experiment_E5_interdependence_sweep.yaml E5_q10_r2

python src/cli/run_simulation.py experiment_E6_topology_effect.yaml E6_gp_er
python src/cli/run_simulation.py experiment_E6_topology_effect.yaml E6_gp_ba