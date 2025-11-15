
---

## 15. `docs/DESIGN.md` (sehr knapp; kannst du erweitern)

```markdown
# Design und Methodik

Dieses Dokument beschreibt die methodischen Entscheidungen des Implementierungsprojekts.

## Netzwerkmodelle

- **Synthetische Netze**
  - Erdős–Rényi (ER)
  - Watts–Strogatz (WS)
  - Barabási–Albert (BA)

- **Reale Netze**
  - Unterstützung für GraphML-basierte reale Netze (z. B. SciGRID Deutschland).
  - Preprocessing:
    - Beschränkung auf die größte verbundene Komponente
    - Umbenennung der Knoten auf Ganzzahlen

## Störungsszenarien

- **Random Failures**: zufällige Entfernung von Knoten.
- **Targeted Attacks**:
  - nach Knotengrad (Degree)
  - nach Zwischenzentralität (Betweenness Centrality)

Die Reihenfolge der zu entfernenden Knoten wird einmal pro Graph und Angriffsszenario
berechnet und anschließend für verschiedene Entfernungsanteile (Fractions) verwendet.

## Resilienzmetriken

Für jeden Zustand des beschädigten Netzwerks werden berechnet:

- Anteil der größten verbundenen Komponente (LCC)
- durchschnittliche Pfadlänge auf der LCC
- globale Effizienz (global efficiency)

## Robustheitskurven und AUC

Aus den Werten der LCC-Fraktion in Abhängigkeit vom Anteil der entfernten Knoten
werden Robustheitskurven erzeugt. Die Fläche unter der Robustheitskurve (AUC) wird
mittels Trapezregel berechnet und dient als skalare Robustheitskennzahl.

## Reale Daten

Reale Netze können z. B. aus

- **SciGRID** (Übertragungsnetz Deutschland/Europa)
- weiteren Open-Data-Quellen im Energiebereich

geladen werden. Die Daten werden im GraphML-Format abgelegt und unter
`data/real/` bereitgestellt.

## Reproduzierbarkeit

- Konfiguration über YAML
- fixer Zufalls-Seed
- automatische Speicherung aller Simulationsergebnisse
- optionale Sensitivitätsanalysen über Parameter-Variation in den YAML-Dateien
