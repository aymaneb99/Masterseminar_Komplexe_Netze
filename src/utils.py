from __future__ import annotations

from typing import Sequence, Any, Dict

import numpy as np
import hashlib
import json


def trapezoidal_auc(x: Sequence[float], y: Sequence[float]) -> float:
    """
    Compute the area under a curve using the trapezoidal rule.

    Im Kontext unseres Projekts entspricht dies:
      Rob = ∫ S(q) dq
    wobei S(q) z.B. die gcc_fraction nach Entfernung des Anteils q darstellt.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")
    if len(x) < 2:
        return 0.0

    x_arr = np.array(x, dtype=float)
    y_arr = np.array(y, dtype=float)
    # Fläche unter der Kurve per Trapezregel
    trapezoid_fn = getattr(np, "trapezoid", None)
    if trapezoid_fn is None:
        trapezoid_fn = getattr(np, "trapz", None)
    if trapezoid_fn is not None:
        return float(trapezoid_fn(y_arr, x_arr))

    # Extremely defensive fallback (in case NumPy API differs): manual trapezoid.
    dx = np.diff(x_arr)
    return float(np.sum((y_arr[1:] + y_arr[:-1]) * 0.5 * dx))


def hash_config(config: Dict[str, Any]) -> str:
    """
    Create a stable hash for a configuration dict, useful to detect
    when a simulation needs to be re-run.
    """
    # Dict deterministisch serialisieren
    json_str = json.dumps(config, sort_keys=True)
    # Stabiler SHA-256 Hash für Wiedererkennungen/Caching
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
