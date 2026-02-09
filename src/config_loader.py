from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml


def load_yaml_config(
	defaults: str | Path,
	experiment: str | Path | None = None,
	experiment_name: str | None = None,
) -> Dict[str, Any]:
	"""Lädt defaults.yaml und wendet optional Experiment-Overrides an."""
	defaults_data = _read_yaml(defaults)
	result = copy.deepcopy(defaults_data)

	if experiment_name is None:
		return result
	if experiment is None:
		raise ValueError("experiment.yaml fehlt, obwohl ein Experiment gewählt wurde.")

	experiments = _read_yaml(experiment).get("experiments", [])
	selected = _find_experiment(experiments, experiment_name)
	overrides = selected.get("override", {})

	_apply_overrides(result, overrides)
	return result


def list_experiments(experiment: str | Path) -> List[str]:
	"""Liefert die Namen der verfügbaren Experimente."""
	experiments = _read_yaml(experiment).get("experiments", [])
	return [exp.get("name") for exp in experiments if exp.get("name")]


def _read_yaml(path: str | Path) -> Dict[str, Any]:
	"""Liest eine YAML-Datei sicher ein."""
	path = Path(path)
	if not path.exists():
		raise FileNotFoundError(f"Datei nicht gefunden: {path}")
	return yaml.safe_load(path.read_text()) or {}


def _find_experiment(experiments: Iterable[Mapping[str, Any]], name: str) -> Dict[str, Any]:
	"""Sucht ein Experiment nach Name."""
	for exp in experiments:
		if exp.get("name") == name:
			return dict(exp)
	raise ValueError(f"Experiment nicht gefunden: {name}")


def _apply_overrides(config: Dict[str, Any], overrides: Dict[str, Any]) -> None:
	"""Wendet Overrides per Punkt-Notation oder verschachtelten Dicts an."""
	for key, value in overrides.items():
		if isinstance(value, dict):
			_set_nested_dict(config, key.split("."), value)
		else:
			_set_nested_value(config, key.split("."), value)


def _set_nested_value(config: Dict[str, Any], keys: List[str], value: Any) -> None:
	"""Setzt einen Wert in einem verschachtelten Dict."""
	target = config
	for key in keys[:-1]:
		if key not in target or not isinstance(target[key], dict):
			target[key] = {}
		target = target[key]
	target[keys[-1]] = value


def _set_nested_dict(config: Dict[str, Any], keys: List[str], value: Dict[str, Any]) -> None:
	"""Führt einen Deep-Merge an der Zielstelle aus."""
	target = config
	for key in keys:
		if key not in target or not isinstance(target[key], dict):
			target[key] = {}
		target = target[key]
	_deep_merge(target, value)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
	"""Deep-Merge in-place für verschachtelte Dicts."""
	for key, value in override.items():
		if isinstance(value, dict) and isinstance(base.get(key), dict):
			_deep_merge(base[key], value)
		else:
			base[key] = value