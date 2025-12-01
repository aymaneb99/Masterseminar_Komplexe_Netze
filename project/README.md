# Praktischer Teil der Masterseminararbeit – Fehlertoleranz und Robustheit eines komplexen Smart‑Grid‑Netzwerks

Dieses Projekt ist der praktische Teil unserer Masterseminararbeit zum Thema
„Fehlertoleranz und Robustheit eines komplexen Smart‑Grid‑Netzwerks“.
Es erlaubt, Netzwerke (synthetisch und real) zu laden, Störszenarien zu simulieren
und die Robustheit anhand etablierter Metriken auszuwerten, wahlweise über eine
grafische Oberfläche (Streamlit) oder eine Kommandozeile.


## Inhaltsverzeichnis

1. [Einführung](#einfuehrung)
2. [Funktionsumfang](#funktionsumfang)
3. [Quickstart (Windows PowerShell)](#quickstart)
4. [Bedienung](#bedienung)
  - [Streamlit‑App](#bedienung-streamlit)
  - [CLI‑Modus](#bedienung-cli)
5. [Konfiguration (YAML)](#konfiguration)
  - [Graphs](#konfiguration-graphs)
  - [Attacks](#konfiguration-attacks)
  - [Fractions](#konfiguration-fractions)
  - [Metrics](#konfiguration-metrics)
  - [Analysis](#konfiguration-analysis)
6. [Daten, Metriken und KPIs](#daten-metriken)
7. [Detaillierte Metriken (mit Beispielen)](#metriken-detail)
8. [Architekturüberblick](#architektur)
  - [Ordnerstruktur](#ordnerstruktur)
    - [PyPSA‑EUR → GraphML](#pypsa-konvertierung)
9. [Implementierungsdetails](#implementierung)
---

<a id="einfuehrung"></a>
## 1) Einführung 

Moderne Stromnetze sind große vernetzte Systeme. Fällt ein wichtiger Knoten aus,
z. B. ein Umspannwerk, so kann das Auswirkungen auf das gesamte Netz haben. Mit diesem
Projekt kann man untersuchen, wie robust eine bestimmte Netzstruktur gegenüber Ausfällen
ist: Wir entfernen schrittweise Knoten (zufällig oder gezielt) und messen, wie stark das
Netz „zusammenhält“. Daraus entstehen sogenannte Robustheitskurven und Kennzahlen
wie die „Fläche unter der Robustheitskurve (AUC)“.

Die Ergebnisse helfen zu verstehen, welche Netzstrukturen widerstandsfähiger sind und
welche Knoten besonders kritisch sein könnten.

### Seminarkontext und Zielsetzung

- Praktischer Nachweis und Vergleich der Robustheit typischer Netzwerktopologien (ER/WS/BA) sowie eines realen Stromnetz‑Topologiemodells (PYPSA EUR).
- Reproduzierbare Experimente über YAML‑Konfigurationen (Parameter, Angriffe, Fraktionen, Wiederholungen) mit konsistenter Ergebnisablage unter `results/`.
- Kennzahlenbasierte Bewertung (GCC‑Fraction/GCC‑Size, mittlere Pfadlänge und Durchmesser in der GCC, globale Effizienz, Clustering, Gradstatistiken) und Zusammenfassung über AUC.
- Nachvollziehbarer Codeaufbau (Loader, Generatoren, Angriffe, Metriken, Orchestrierung) als Basis für Erweiterungen (z. B. Kaskaden/Lastfluss) in späteren Arbeiten.


<a id="funktionsumfang"></a>
## 2) Funktionsumfang
Der Funktionsumfang bildet einen vollständigen Analyse‑Workflow von der Generierung bzw. Konvertierung von Netztopologien über die Simulation verschiedener Ausfallszenarien bis zur Auswertung und Visualisierung ab.

### 2.1 Netzwerk‑Erzeugung & ‑Import
Synthetische Modelle:
  - Erdős–Rényi (ER): zufällige Kanten; Parameter n, p.
  - Watts–Strogatz (WS): Small‑World mit lokaler Clusterung; Parameter n, k, p.
  - Barabási–Albert (BA): skalenfreie Hubs; Parameter n, m.
Reale Topologien:
  - Laden von GraphML (z. B. SciGRID, konvertiertes PyPSA‑EUR).
  - Optionales Preprocessing: nur größte Komponente, integer Re‑Labeling.
  - Konvertierung PyPSA‑EUR CSV → GraphML mittels `tools/pypsa_to_graphml.py` (robustes Parsing der Geometrie).

### 2.2 Störungsszenarien ("Angriffe")
  - Random Failures: uniforme Zufallsreihenfolge der Knoten.
  - Targeted Degree: jeweils aktuell höchster Grad (dynamisch neu bewertet, falls Implementierung erweitert wird).
  - Targeted Betweenness: Knoten mit höchster Vermittlerrolle; bei großen Graphen Sampling zur Beschleunigung.
Erweiterbar: Neue Strategien durch Hinzufügen einer Funktion in `attacks.py`, die eine Reihenfolge (List[int]) für Knoten liefert.

### 2.3 Simulationsablauf
  1. Graph erzeugen/laden (ggf. preprocess).
  2. Angriffsliste vorbereiten.
  3. Für jeden Entfernungsanteil f: Anzahl zu entfernender Knoten bestimmen und entfernen (Anteil bezieht sich immer auf Ursprung N0).
  4. Metriken auf dem beschädigten Graph berechnen (siehe 2.4).
  5. Zeile in Ergebnis‑CSV schreiben.
  6. Wiederholungen aggregieren; AUC berechnen (Trapezregel) pro Graph/Angriff.
  7. Optionale Analyse/Plots (Streamlit oder Skript in `analysis.py`).

### 2.4 Metriken & KPIs
Struktur‑ und Resilienzmetriken (spaltenweise Ausgabe):
  - GCC‑Fraction, GCC‑Size (Größte zusammenhängende Komponente)
  - avg_path_length_gcc, diameter_gcc (Erreichbarkeit & Ausdehnung des Kerns)
  - global_efficiency (Abfall früh bei Fragmentierung)
  - global_clustering, avg_local_clustering (Redundanz lokal/global)
  - mean_degree, max_degree, degree_std (Topologiesignatur / Hubs / Streuung)
  - AUC als zusammenfassender Robustheitsindikator über Fraktionen
Erweiterbar: Neue Metrik durch Funktion in `metrics.py` + Eintrag im Dispatcher + YAML‑Liste ergänzen.

### 2.5 Ergebnisse & Dateien
Automatische Ablage unter `results/<experiment_name>/`:
  - `<experiment>_results.csv`: Zeilen je (Graph, Angriff, Wiederholung, Fraction).
  - `<experiment>_auc_<metric>.csv`: Zusammenfassung über Aggregation (z. B. Graph, Angriff).
  

### 2.6 Interaktive Oberfläche (Streamlit)
  - Auswahl einer YAML‑Konfiguration in der Sidebar.
  - Start/Stop der Simulation, Fortschrittsfeedback.
  - Anzeige einer Vorschau der Konfigurationsparameter (Graphen, Angriffe, Fraktionen, Metriken).
  - Dynamische Auswahl der zu visualisierenden Metrik (Robustheitskurve, AUC‑Tabelle).
  - Export/Download der Roh‑CSV direkt aus der UI (Gilt es noch zu implementieren).


### 2.7 CLI‑Modus (Batch & Skriptintegration)
  - Aufruf `python -m src.main -c <config.yaml>`.
  - Ideal für automatisierte Serien (verschiedene Konfigs, Seeds) via Shell‑Skripte.
  - `--no-analysis` Flag zur Beschleunigung, wenn AUC später separat berechnet wird.

### 2.8 Erweiterbarkeit & Wartbarkeit
  - Neue Graphmodelle: Funktion in `network_models.py` + Parametervalidierung.
  - Neue reale Formate: Loader in `real_network_loader.py` (z. B. JSON, Geopackage) + Parser.
  - Weitere Angriffe: Strategie in `attacks.py` (z. B. eigenvector, k‑core, community‑targeting).
  - Weitere Metriken: Implementieren in `metrics.py`; geringe Kopplung über zentrale Berechnungsroutine.
  - Analysepipelines: Zusätzliche KPIs (z. B. Resilience Index, Perkolationsschwelle) in `analysis.py` ergänzbar.

### 2.9 Performance & Skalierung
  - Betweenness: Sampling bei großen N reduziert Laufzeit drastisch.
  - Fraktionsschritte steuerbar (gröbere Schritte für sehr große Graphen).
  - Wiederholungen (repetitions) balancieren statistische Stabilität vs. Laufzeit.
  - Potenziale für Parallelisierung: unabhängige Wiederholungen könnten per Multiprocessing/Joblib ausgeführt werden (aktuell seriell, um Determinismus und Einfachheit zu wahren).

### 2.10 Qualität & Validierung
  - Konsistenz: GCC‑Fraction immer gegen ursprüngliches N0 normiert -> vergleichbare Kurven.
  - Fehlervermeidung: Robustes CSV‑Parsing beim PyPSA‑Konverter; Entfernen von `None` vor GraphML‑Export.
  - Reproduzierbarkeit: Fester Seed + klar nachvollziehbarer Angriffspfad.
  - Transparenz: Vollständige Parameterausgabe/Logging (kann künftig noch erweitert werden).

---

<a id="quickstart"></a>
## 3) Quickstart (Windows PowerShell)

Voraussetzungen: Python 3.12 wird empfohlen. Ein virtuelles Umfeld (.venv) hält
das System sauber.

```powershell
# 1) Im Projektordner eine virtuelle Umgebung anlegen
python -m venv .venv

# 2) Aktivieren
.venv\Scripts\Activate.ps1

# 3) Abhängigkeiten installieren
pip install --upgrade pip # (optional)
pip install -r requirements.txt

# 4a) Streamlit‑App starten
streamlit run app/streamlit_app.py

# 4b) (Alternative) CLI‑Modus mit Beispielkonfiguration
python -m src.main -c "configs\synthetic_vs_synthetic.yaml"
```

Hinweise:
- Falls dein globales Python 3.13 ist und es zu WebSocket‑Warnungen kommt, nutze eine
  .venv mit Python 3.12 (empfohlen) oder aktualisiere Streamlit.
- Beim Start der Streamlit‑App öffnet sich der Browser automatisch. In der App eine
  YAML‑Konfiguration auswählen und Simulation starten.

---

<a id="bedienung"></a>
## 4) Bedienung

<a id="bedienung-streamlit"></a>
### 4.1 Streamlit‑App

1. Starte die App: `streamlit run app/streamlit_app.py`
2. Wähle in der Sidebar eine YAML‑Datei unter `configs/` aus.
3. Vorschau prüfen (Konfigurationsvorschau im Hauptbereich).
4. „Simulation starten“ klicken.
5. Nach Abschluss:
   - Rohdaten‑Tabelle (erste Zeilen)
   - Auswahl der Metrik für AUC und Kurven
   - AUC‑Tabelle (aggregiert, z. B. pro Graph und Angriff)
   - Interaktive Robustheitskurven mit Auswahl von Graph‑ und Angriffsszenario

Die Ergebnisse (CSV) werden unter `results/<experiment_name>/` abgelegt.

<a id="bedienung-cli"></a>
### 4.2 CLI‑Modus

```powershell
python -m src.main -c "configs\synthetic_vs_synthetic.yaml"
```

Optionen:
- `-c/--config`: Pfad zur YAML‑Konfiguration
- `--no-analysis`: AUC‑Nachanalyse überspringen

Ausgaben:
- `<experiment_name>_results.csv`: alle Messpunkte
- Optional: `<experiment_name>_auc_<metric>.csv`: AUC‑Zusammenfassung

---

<a id="konfiguration"></a>
## 5) Konfiguration (YAML)

Top‑Level‑Schlüssel (Pflicht):

```yaml
experiment_name: "synthetic_comparison"
output_dir: "results"
random_seed: 42
graphs: [ ... ]        # Liste von Graphdefinitionen (mind. 1)
attacks: [ ... ]       # Liste von Angriffsszenarien (mind. 1)
fractions: { ... }     # Entfernungsanteile (0..1) als Liste oder als start/end/step
metrics: [ ... ]       # Metriken für die Ausgabe/CSV
```

Optional:

```yaml
analysis:
  metric_for_auc: "gcc_fraction"
  aggregate_by: ["graph_id", "attack_id"]
```

<a id="konfiguration-graphs"></a>
### 5.1 Graphs

Synthetisch (`type: synthetic`) – unterstützte Modelle und Parameter:

- Erdős–Rényi (`model: erdos_renyi`): `n` (Knoten), `p` (Kantenwahrscheinlichkeit)
- Watts–Strogatz (`model: watts_strogatz`): `n`, `k` (Nachbarn), `p` (Rewire‑Prob.)
- Barabási–Albert (`model: barabasi_albert`): `n`, `m` (Kanten je neuem Knoten)

Zusätzlich: `repetitions` (Anzahl Wiederholungen pro Graph)

Beispiel:

```yaml
graphs:
  - id: "ER_n1000_p0.01"
    type: "synthetic"
    model: "erdos_renyi"
    n: 1000
    p: 0.01
    repetitions: 5
```

Reale Netze (`type: real`) – aktuell GraphML‑Dateien:

```yaml
graphs:
  - id: "SciGRID_DE"
    type: "real"
    model: "real_graphml"
    path: "data/real/scigrid_germany.graphml"
    repetitions: 3
    preprocess:
      giant_component_only: true    # optional, Voreinstellung: true
      relabel_to_integers: true     # optional, Voreinstellung: true
```

<a id="konfiguration-attacks"></a>
### 5.2 Attacks

Angriffstypen:

- `type: random` – zufällige Reihenfolge der zu entfernenden Knoten
- `type: targeted` – gezielte Reihenfolge nach Zentralitätsmaß, `strategy`:
  - `degree`
  - `betweenness` (für große Netze automatisch approximiert)

Beispiele:

```yaml
attacks:
  - id: "random_failures"
    type: "random"

  - id: "targeted_degree"
    type: "targeted"
    strategy: "degree"

  - id: "targeted_betweenness"
    type: "targeted"
    strategy: "betweenness"
```

<a id="konfiguration-fractions"></a>
### 5.3 Fractions

Entfernungsanteile in [0, 1]. Zwei Varianten:

```yaml
fractions:
  start: 0.0
  end: 1.0
  step: 0.05
```

oder

```yaml
fractions:
  values: [0.0, 0.1, 0.2, 0.3, 0.5, 1.0]
```

<a id="konfiguration-metrics"></a>
### 5.4 Metrics

Verfügbare Metriken (werden als Spalten in die CSV geschrieben):

- `gcc_fraction` – Anteil der größten zusammenhängenden Komponente relativ zur ursprünglichen Knotenzahl
- `gcc_size` – absolute Größe der größten zusammenhängenden Komponente
- `avg_path_length_gcc` – mittlere kürzeste Pfadlänge innerhalb der GCC
- `diameter_gcc` – Durchmesser der GCC (bei Nicht‑Zusammenhang: GCC‑Durchmesser)
- `global_efficiency` – globale Effizienz des (beschädigten) Graphen
- `global_clustering` – globaler Clustering‑Koeffizient (Transitivität)
- `avg_local_clustering` – mittlerer lokaler Clustering‑Koeffizient
- `mean_degree`, `max_degree`, `degree_std` – Kenngrößen der Gradverteilung

<a id="konfiguration-analysis"></a>
### 5.5 Analysis

Konfiguration der AUC‑Auswertung und Aggregation:

```yaml
analysis:
  metric_for_auc: "gcc_fraction"
  aggregate_by: ["graph_id", "attack_id"]
```

---

<a id="daten-metriken"></a>
## 6) Daten, Metriken und KPIs

### 6.1 Was sind die Daten?

Für synthetische Netze werden Graphen on‑the‑fly erzeugt. Für reale Netze
werden GraphML‑Dateien geladen. 

### 6.2 Welche Metriken werden berechnet?

Für jeden „Beschädigungszustand“ (d. h. nach Entfernen eines Anteils der Knoten):

- GCC‑Fraction & GCC‑Size – Anteil und Größe der größten zusammenhängenden Komponente
- Avg Path Length (GCC): `avg_path_length_gcc`
- Durchmesser (GCC): `diameter_gcc`
- Globale Effizienz: `global_efficiency`
- Clustering: `global_clustering`  und `avg_local_clustering`
- Gradverteilung: `mean_degree`, `max_degree`, `degree_std` 

### 6.3 Was ist AUC (Fläche unter der Robustheitskurve)?

Wir plotten die Metrik (z. B. GCC‑Fraction) gegen den Anteil entfernter Knoten.
Die AUC fasst die gesamte Kurve in einer Zahl zusammen: Höhere AUC = robuster.
Die AUC wird pro Wiederholung berechnet und über Wiederholungen gemittelt.

---

<a id="metriken-detail"></a>
## 7) Detaillierte Metriken (mit einfachen Beispielen)

Im Folgenden werden alle Metriken mit:
- kurzer Definition
- anschaulichem Mini‑Beispiel mit Kleingraph
- praktischer Bedeutung für Robustheit

Zur Veranschaulichung nutzen wir diesen Startgraph (G0):

```
   A -- B -- C
  |    \
  D     E
```

Knoten: A,B,C,D,E. Kanten: AB, BC, BD, CE. (C und E sind verbunden, D hängt an B.)

Nach Entfernung verschiedener Knoten schauen wir, wie sich die Metriken verändern.

### 1) gcc_fraction (Anteil größte Komponente)
Definition: Größe der größten zusammenhängenden Komponente dividiert durch die ursprüngliche Knotenzahl N0.
Formel: `gcc_fraction = |GCC_current| / N0`.
Beispiel: In G0 sind alle 5 Knoten über Pfade verbunden ⇒ gcc_fraction = 5/5 = 1. Entfernen wir C, verbleiben A,B,D (verbunden) und E (isoliert): größte Komponente hat 3 Knoten ⇒ 3/5 = 0.6.
Bedeutung: Basismaß für „Zusammenhalt“. Je höher über viele Entfernungsgrade hinweg, desto robuster.

### 2) gcc_size (absolute Größe größte Komponente)
Definition: Anzahl Knoten der GCC (ohne Normierung).
Beispiel: Nach Entfernen von C ist gcc_size = 3.
Bedeutung: Ergänzt gcc_fraction, besonders relevant bei Vergleich unterschiedlicher N0.

### 3) avg_path_length_gcc (mittlere kürzeste Pfadlänge in der GCC)
Definition: Mittelwert der Längen aller kürzesten Wege zwischen Knotenpaaren innerhalb der GCC.
Beispiel (G0): Paare (A,B=1; A,C=2; A,D=2; A,E=3; B,C=1; B,D=1; B,E=2; C,D=2; C,E=1; D,E=3) → Summe=18, Paare=10 ⇒ 1.8. Nach Entfernen von C: GCC {A,B,D}: (A,B=1; A,D=2; B,D=1) ⇒ (1+2+1)/3=1.33.
Bedeutung: Zeigt, wie „kompakt“ der verbleibende Kern ist. Steigt oft bevor das Netz zerfällt (Umwege entstehen).

### 4) diameter_gcc (Durchmesser der GCC)
Definition: Länge des längsten kürzesten Weges innerhalb der GCC.
Beispiel: G0 Durchmesser = Distanz A<-> E = 3. Nach Entfernen von C: Durchmesser {A,B,D} = 2.
Bedeutung: Extremmaß – hoher Wert weist auf langgezogene, potenziell fragilere Struktur hin.

### 5) global_efficiency
Definition: Durchschnitt der inversen kürzesten Distanzen aller ungeordneten Knotenpaare; nicht erreichbare Paare tragen 0 bei.
Formel: `E_global = (1/(N*(N-1))) * Σ_{i≠j} 1/d(i,j)`.
Beispiel: Wenn E isoliert wird, alle Paare mit E liefern 0 -> deutlicher Effizienzabfall obwohl gcc_fraction evtl. noch moderat.
Bedeutung: Sensitiver Indikator für Fragmentierung früh im Prozess.

### 6) global_clustering (Transitivität)
Definition: Verhältnis geschlossener Dreiecke zu allen verbundenen Triples (Pfadlänge 2). Formel: `3 * (#Dreiecke) / (#Triples)`.
Beispiel: G0 hat keine Dreiecke ⇒ 0. Falls A‑C und C‑B und A‑B vorhanden wären -> Dreieck -> Wert steigt.
Bedeutung: Lokale Redundanz; höhere Werte mindern Risiko durch einzelne Ausfälle in dicht gekoppelten Segmenten.

### 7) avg_local_clustering
Definition: Mittelwert der lokalen Clusterungskoeffizienten jedes Knotens (tatsächliche Dreiecke / mögliche Dreiecke unter seinen Nachbarn).
Beispiel: Knoten mit Nachbarn X,Y,Z und zwei existierenden Dreiecken -> 2/3.
Bedeutung: Feingranular – deckt heterogene lokale Struktur auf, die global_clustering glättet.

### 8) mean_degree
Definition: Durchschnittliche Anzahl Nachbarn pro Knoten.
Beispiel G0 Grade: A=1,B=3,C=2,D=1,E=1 -> Summe=8 -> 8/5=1.6.
Bedeutung: Grober Dichteindikator; bei gezielten Angriffen auf Hubs fällt er langsamer als max_degree.

### 9) max_degree
Definition: Höchster Grad eines Knotens.
Beispiel: In G0 max_degree=3 (B). Entfernen von B reduziert Struktur drastisch.
Bedeutung: Marker für Hubs; schnelles Sinken zeigt Angriffseffekt auf zentrale Knoten.

### 10) degree_std (Standardabweichung der Grade)
Definition: Streuung der Gradverteilung. Hoch = ungleich verteilt (Hubs + viele Low‑Degree‑Knoten).
Beispiel: Grade {1,3,2,1,1} heterogener als {1,2,1,1} nach Entfernen von B.
Bedeutung: Korrelierte Verwundbarkeit gegenüber gezielten Angriffen – hohe Streuung = potenziell fragil unter Targeted Degree.

### 11) AUC (Area Under Curve)
Definition: Integral einer ausgewählten Metrik (z. B. gcc_fraction) über Entfernten‑Anteil 0 -> 1.
Beispiel: Kurve bleibt lange hoch -> AUC nahe 1; früh abfallende Kurve -> kleine AUC.
Bedeutung: Ein‑Zahl‑Vergleich für gesamte Robustheitsentwicklung.

### Kombination der Metriken
- Frühe Phase: max_degree und degree_std reagieren bei targeted Angriffen zuerst.
- Mittelphase: avg_path_length_gcc & diameter_gcc steigen; global_efficiency fällt.
- Spätphase: gcc_fraction bricht ein; AUC finalisiert Vergleich.

### Typische Muster
- ER: moderate degree_std; kontinuierlicher Zerfall.
- WS: höheres Clustering -> lokale Redundanz; Pfadlängen stabil länger.
- BA: hohe degree_std; robust bei zufälligen Ausfällen, empfindlich bei targeted degree.

Gemeinsame Interpretation verhindert Fehlurteile: Hohe gcc_fraction allein kann täuschen, wenn Effizienz schon stark gefallen ist.

---

<a id="architektur"></a>
## 8) Architekturüberblick

Strukturdiagramm:

```
             +-------------------+
             |   configs/*.yaml  |
             +---------+---------+
                       |
                       v
               (src.config_loader)
                       |
                       v
 +----------------- Experiment Orchestrierung ------------------+
 |                    (src.simulation)                          |
 |                                                              |
 |   +--------------+      +----------------------+             |
 |   | Graph Factory|----->|  synthetic models    |             |
 |   |(graph_factory)      |  (network_models)    |             |
 |   +--------------+      +----------------------+             |
 |          |                         ^                         |
 |          v                         |                         |
 |   +--------------+      +----------------------+             |
 |   | real loader  |<-----|   data/real/*.graphml|             |
 |   | (real_... )  |      +----------------------+             |
 |   +--------------+                                      +---+---+
 |          |                                             |attacks |
 |          v                                             |(order) |
 |   +--------------+                                     +---+---+
 |   |  metrics     |  -> gcc_fraction, avg_path_length_gcc,    |
 |   |              |     diameter_gcc, global_efficiency,      |
 |   |              |     clustering, degree_stats              |
 |   +------+-------+                                           |
 |          |                                                   |
 |          v                                                   v
 |     CSV writer ------------------------------------> results/<exp>/*.csv
 +---------------------------------------------------------------+

           ^                                     ^
           |                                     |
   Streamlit UI (app/)                     CLI (src.main)
```

<a id="ordnerstruktur"></a>
### Ordnerstruktur

```
project/
├─ app/                      # Streamlit‑App
├─ configs/                  # YAML‑Konfigurationen
├─ data/
│  ├─ real/                  # z. B. SciGRID GraphML
│  ├─ pypsa/                 # Rohdaten (buses.csv, lines.csv) aus PyPSA‑EUR
│  └─ synthetic/             # optional: gespeicherte Beispielgraphen
├─ tools/                    # Hilfsskripte (z. B. PyPSA‑Konvertierung)
├─ docs/                     # Design‑Notizen
├─ results/                  # Ausgaben pro Experiment
├─ src/                      # Python‑Quellcode (Paket)
│  ├─ analysis.py            # AUC/Plots für Auswertung
│  ├─ attacks.py             # Angriffreihenfolgen
│  ├─ config_loader.py       # YAML laden/validieren
│  ├─ graph_factory.py       # Auswahl synthetic/real
│  ├─ metrics.py             # Metriken
│  ├─ network_models.py      # ER/WS/BA‑Generatoren
│  ├─ real_network_loader.py # GraphML‑Loader + Preprocessing
│  ├─ simulation.py          # Orchestrierung + CSV‑Export
│  ├─ utils.py               # Hilfsfunktionen (AUC)
│  └─ main.py                # CLI‑Einstiegspunkt
├─ requirements.txt
└─ README.md
```

---

<a id="pypsa-konvertierung"></a>
### PyPSA‑EUR -> GraphML (Konvertierung mit `tools/pypsa_to_graphml.py`)

Dieses Projekt bringt ein Hilfsskript mit, um die PyPSA‑EUR‑CSV‑Dateien
(`data/pypsa/buses.csv`, `data/pypsa/lines.csv`) in eine GraphML‑Datei zu
überführen. Hintergrund: In `lines.csv` steckt eine Geometrie‑Spalte mit
WKT‑Strings wie `'LINESTRING (x y, …)'`, die sehr viele Kommata enthält und
einfaches CSV‑Parsing leicht aus dem Tritt bringt.

Was das Skript macht:
- Robustes Einlesen von `lines.csv` mit `quotechar='\''` und `engine='python'`,
  damit die gesamte Geometrie‑Spalte korrekt als ein Feld behandelt wird.
- Validiert Pflichtspalten (`bus0`, `bus1`).
- Fügt Knoten/Attribute aus `buses.csv` hinzu; optional fehlende Werte werden
  nicht in GraphML geschrieben (Workaround gegen „NoneType in GraphML“).
- Fügt Kanten aus `lines.csv` hinzu (Length soweit möglich numerisch).


So nutzt du es (aus dem Projekt‑Root):

```powershell
# Sicherstellen, dass die Rohdaten liegen unter:
#   data\pypsa\buses.csv
#   data\pypsa\lines.csv

# Konvertierung starten (speichert nach data\real\pypsa_eur.graphml)
python tools/pypsa_to_graphml.py
```

Ergebnis:
- `data/real/pypsa_eur.graphml` – bereit, in Konfigurationen als `type: real`
  genutzt zu werden.


Beispiel‑Konfiguration, um die erzeugte Datei zu analysieren:

```yaml
graphs:
  - id: "PyPSA_EUR"
    type: "real"
    model: "real_graphml"
    path: "data/real/pypsa_eur.graphml"
    repetitions: 1
```

<a id="implementierung"></a>
## 9) Implementierungsdetails

### 9.1 Komponentenübersicht (Wer macht was?)

- `src/main.py` – CLI‑Einstiegspunkt: parst Argumente (`-c/--config`, `--no-analysis`) und startet die Simulation.
- `src/config_loader.py` – lädt/validiert YAML: Pfade, Typen, Defaults (z. B. `giant_component_only=true`). Liefert eine strukturierte Konfiguration.
- `src/graph_factory.py` – wählt anhand der Konfig einen Graphlieferanten: synthetisch (`network_models.py`) oder real (`real_network_loader.py`).
- `src/network_models.py` – Generatoren für ER/WS/BA: deterministisch via `random_seed`, Rückgabe: `networkx.Graph`.
- `src/real_network_loader.py` – lädt GraphML, optional Preprocessing: nur größte Komponente, integer Re‑Labels; gibt `Graph` zurück.
- `src/attacks.py` – erzeugt Angriffsreihenfolgen (Listen von Knoten‑IDs): `random`, `targeted degree`, `targeted betweenness` (ggf. Sampling bei großen Netzen).
- `src/metrics.py` – berechnet Metriken auf dem beschädigten Graphen bzw. der GCC: `gcc_fraction/size`, `avg_path_length_gcc`, `diameter_gcc`, `global_efficiency`, `global/avg_local_clustering`, `mean/max/degree_std`.
- `src/simulation.py` – Orchestrator: iteriert über Graph‑Definitionen, Angriffe, Fraktionen und Wiederholungen; entfernt Knoten, ruft Metriken auf, schreibt CSV.
- `src/analysis.py` – AUC‑ und Aggregationslogik (Trapezregel), optional Visualisierungen/Tabellen.
- `src/utils.py` – Hilfsfunktionen (z. B. Trapezintegral, sichere Division, Seed‑Handling).
- `app/streamlit_app.py` – UI: Konfig auswählen, Simulation starten, Kurven/AUC‑Tabellen anzeigen; fügt den Projekt‑Root zu `sys.path` hinzu, damit `src` importierbar ist.
- `tools/pypsa_to_graphml.py` – separates Konverter‑Skript: PyPSA‑EUR CSVs -> GraphML (robustes CSV‑Parsing, None‑Filterung vor Export).

### 9.2 Datenfluss (End‑to‑End)

1) Konfiguration laden -> 2) Graph erzeugen/lesen (optional preprocess) ->
3) Angriffsliste bestimmen -> 4) Für jede Fraction f Knoten entfernen ->
5) Metriken berechnen -> 6) Zeile in `<experiment>_results.csv` schreiben ->
7) Optional: AUC/Analyse erzeugen (`<experiment>_auc_<metric>.csv`).





