from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from .graphs import GraphSpec
from .simulate import ExperimentSpec


@dataclass(frozen=True)
class Scenario:
    experiment: ExperimentSpec
    output_dir: Optional[Path] = None


def _load_raw(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("pyyaml wird benötigt, um YAML-Szenariodateien zu laden")
        data = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Nicht unterstütztes Szenarioformat: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError("Das Szenario muss als Mapping (Schlüssel/Werte) definiert sein")
    return data


def load_scenario(path_like: str | Path) -> Scenario:
    path = Path(path_like)
    data = _load_raw(path)

    exp = data.get("experiment", {})
    graphs_raw = exp.get("graphs", [])
    strategies = exp.get("strategies", ["random", "degree", "betweenness"])
    step = float(exp.get("step", 0.02))
    repeats = int(exp.get("repeats", 1))
    seed = exp.get("seed", 42)

    specs: List[GraphSpec] = []
    for g in graphs_raw:
        kind = g.get("kind")
        params = g.get("params", {})
        if not kind:
            raise ValueError("Eintrag für Graph fehlt: 'kind'")
        specs.append(GraphSpec(kind=str(kind), params=dict(params)))

    experiment = ExperimentSpec(
        graph_specs=specs,
        strategies=list(map(str, strategies)),
        step=step,
        repeats=repeats,
        seed=seed,
    )

    out_root = data.get("output", {}).get("dir") if isinstance(data.get("output"), dict) else None
    out_dir = Path(out_root) if out_root else None

    return Scenario(experiment=experiment, output_dir=out_dir)
