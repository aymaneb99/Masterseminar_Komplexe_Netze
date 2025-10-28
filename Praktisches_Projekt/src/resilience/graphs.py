from __future__ import annotations
import networkx as nx
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class GraphSpec:
    kind: str  # 'ER' | 'WS' | 'BA' (Grapharten)
    params: Dict[str, Any]

    def label(self) -> str:
        p = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.kind}({p})"


def make_graph(spec: GraphSpec, seed: Optional[int] = None) -> nx.Graph:
    kind = spec.kind.upper()
    p = dict(spec.params)
    if seed is not None:
        p.setdefault("seed", seed)

    if kind == "ER":
        # Parameter: n, p[, seed]
        return nx.fast_gnp_random_graph(**p)
    if kind == "WS":
        # Parameter: n, k, p[, seed]
        return nx.watts_strogatz_graph(**p)
    if kind == "BA":
        # Parameter: n, m[, seed]
        return nx.barabasi_albert_graph(**p)

    raise ValueError(f"Unknown graph kind: {spec.kind}")
