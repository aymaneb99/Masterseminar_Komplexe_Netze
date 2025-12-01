from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(path: str | Path) -> Dict[str, Any]:
    """
    Load a YAML configuration file and return it as a dictionary.
    Performs a light structural validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        # YAML sicher laden
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Top-level YAML content must be a mapping (dict).")

    _basic_validate_config(config)
    return config


def _basic_validate_config(config: Dict[str, Any]) -> None:
    required_top = ["graphs", "attacks", "fractions", "metrics"]
    for key in required_top:
        if key not in config:
            raise ValueError(f"Missing required top-level key in config: '{key}'")

    graphs = config["graphs"]
    if not isinstance(graphs, list) or not graphs:
        raise ValueError("'graphs' must be a non-empty list.")

    for g in graphs:
        if "id" not in g:
            raise ValueError("Each graph entry must have an 'id'.")
        if "type" not in g:
            raise ValueError("Each graph entry must have a 'type' ('synthetic' or 'real').")

    attacks = config["attacks"]
    if not isinstance(attacks, list) or not attacks:
        raise ValueError("'attacks' must be a non-empty list.")

    frac = config["fractions"]
    if isinstance(frac, dict):
        if "values" in frac:
            if not isinstance(frac["values"], list):
                raise ValueError("'fractions.values' must be a list.")
        else:
            for k in ("start", "end", "step"):
                if k not in frac:
                    raise ValueError(
                        "Fractions dict must contain 'start', 'end', 'step' or 'values'."
                    )
    elif isinstance(frac, list):
        pass  # Liste expliziter Fraktionen ist ok
    else:
        raise ValueError("'fractions' must be a dict or a list.")

    if "analysis" in config and not isinstance(config["analysis"], dict):
        raise ValueError("'analysis' must be a mapping if provided.")
