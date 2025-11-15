from __future__ import annotations

from typing import Sequence

import numpy as np


def trapezoidal_auc(x: Sequence[float], y: Sequence[float]) -> float:
    """
    Compute the area under a curve using the trapezoidal rule.

    Assumes x is sorted and of same length as y.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")
    if len(x) < 2:
        return 0.0

    x_arr = np.array(x, dtype=float)
    y_arr = np.array(y, dtype=float)

    return float(np.trapz(y_arr, x_arr))
