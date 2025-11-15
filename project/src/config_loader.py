from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(path: str | Path) -> Dict[str, Any]:
    """
    Load a YAML configuration file and return it as a dictionary.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Top-level YAML content must be a mapping.")

    _basic_validate_config(config)
    return config


def _basic_validate_config(config: Dict[str, Any]) -> None:
    """
    Minimal structural validation of the config.
    Extend this as needed in the thesis.
    """
    required_top = ["graphs", "attacks", "fractions", "metrics"]
    for key in required_top:
        if key not in config:
            raise ValueError(f"Missing required top-level key: '{key}'")

    graphs = config["graphs"]
    if not isinstance(graphs, list) or len(graphs) == 0:
        raise ValueError("'graphs' must be a non-empty list.")

    for g in graphs:
        if "id" not in g:
            raise ValueError("Each graph entry must have an 'id'.")
        if "type" not in g:
            raise ValueError("Each graph entry must have a 'type' (synthetic|real).")

    attacks = config["attacks"]
    if not isinstance(attacks, list) or len(attacks) == 0:
        raise ValueError("'attacks' must be a non-empty list.")

    frac = config["fractions"]
    if isinstance(frac, dict):
        if "values" in frac:
            if not isinstance(frac["values"], list):
                raise ValueError("'fractions.values' must be a list.")
        else:
            for k in ("start", "end", "step"):
                if k not in frac:
                    raise ValueError("Fractions dict must contain 'start', 'end', 'step' or 'values'.")
    elif isinstance(frac, list):
        pass
    else:
        raise ValueError("'fractions' must be dict or list.")

    # Optional: analysis block
    if "analysis" in config:
        analysis = config["analysis"]
        if not isinstance(analysis, dict):
            raise ValueError("'analysis' must be a mapping if provided.")
