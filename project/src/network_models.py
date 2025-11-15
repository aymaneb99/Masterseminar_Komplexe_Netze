from __future__ import annotations

from typing import Any, Dict, Callable

import networkx as nx


def generate_synthetic_graph(model: str, params: Dict[str, Any], seed: int | None = None) -> nx.Graph:
    """
    Generate a synthetic graph using NetworkX based on model name.
    """
    model = model.lower()
    generators: Dict[str, Callable[[Dict[str, Any], int | None], nx.Graph]] = {
        "erdos_renyi": _erdos_renyi,
        "watts_strogatz": _watts_strogatz,
        "barabasi_albert": _barabasi_albert,
    }

    if model not in generators:
        raise ValueError(f"Unknown synthetic graph model: {model}")

    return generators[model](params, seed)


def _erdos_renyi(params: Dict[str, Any], seed: int | None) -> nx.Graph:
    n = int(params["n"])
    p = float(params["p"])
    return nx.erdos_renyi_graph(n, p, seed=seed)


def _watts_strogatz(params: Dict[str, Any], seed: int | None) -> nx.Graph:
    n = int(params["n"])
    k = int(params["k"])
    p = float(params["p"])
    return nx.watts_strogatz_graph(n, k, p, seed=seed)


def _barabasi_albert(params: Dict[str, Any], seed: int | None) -> nx.Graph:
    n = int(params["n"])
    m = int(params["m"])
    return nx.barabasi_albert_graph(n, m, seed=seed)
