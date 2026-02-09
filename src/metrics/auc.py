from __future__ import annotations

from typing import List, Tuple


def compute_auc(fractions: List[float], values: List[float]) -> float:
	"""Berechnet die AUC der Robustheitskurve über f in [0, 1]."""
	if len(fractions) != len(values):
		raise ValueError("fractions und values müssen gleich lang sein.")
	if not fractions:
		raise ValueError("fractions darf nicht leer sein.")

	for v in values:
		if not 0.0 <= v <= 1.0:
			raise ValueError("Alle Werte müssen in [0, 1] liegen.")

	pairs = _sorted_pairs(fractions, values)
	_validate_fractions([f for f, _ in pairs])

	pairs = _ensure_endpoints(pairs)
	auc = _trapezoidal_integral(pairs)

	if all(v == 0.0 for _, v in pairs):
		return 0.0

	assert 0.0 <= auc <= 1.0, "AUC muss in [0, 1] liegen."
	return auc


def _sorted_pairs(fractions: List[float], values: List[float]) -> List[Tuple[float, float]]:
	"""Sortiert Messpunkte nach Anteil."""
	return sorted(zip(fractions, values), key=lambda item: item[0])


def _validate_fractions(fractions: List[float]) -> None:
	"""Prüft die Gültigkeit der Anteile."""
	for f in fractions:
		if not 0.0 <= f <= 1.0:
			raise ValueError("Alle Anteile müssen in [0, 1] liegen.")


def _ensure_endpoints(pairs: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
	"""Ergänzt fehlende Randpunkte bei 0 oder 1 mit einfachen Werten."""
	if not pairs:
		return pairs

	first_f, first_v = pairs[0]
	last_f, last_v = pairs[-1]

	result = list(pairs)
	if first_f > 0.0:
		result.insert(0, (0.0, first_v))
	if last_f < 1.0:
		result.append((1.0, last_v))

	return result


def _trapezoidal_integral(pairs: List[Tuple[float, float]]) -> float:
	"""Integriert über die Trapezregel."""
	area = 0.0
	for (f0, v0), (f1, v1) in zip(pairs, pairs[1:]):
		width = f1 - f0
		area += width * (v0 + v1) / 2.0
	return area
