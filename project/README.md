# Smart-Grid Network Robustness Toolkit

Dieses Projekt implementiert den praktischen Teil einer Masterseminararbeit zur
**Fehlertoleranz und Robustheit komplexer Smart-Grid-Netzwerke**.

Es ermöglicht:

- Erzeugung synthetischer Netzwerke (Erdős–Rényi, Watts–Strogatz, Barabási–Albert)
- Einbindung realer Netzmodelle (z. B. SciGRID im GraphML-Format)
- Simulation von Angriffsszenarien (Random Failures, Targeted Attacks)
- Berechnung von Resilienzmetriken (LCC-Anteil, mittlere Pfadlänge, globale Effizienz)
- Auswertung von Robustheitskurven und Fläche unter der Robustheitskurve (AUC)
- YAML-basierte Konfiguration ohne Codeänderung
- **Grafische Oberfläche mit Streamlit zur interaktiven Exploration der Experimente**

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
