from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class Line:
    action: int
    term: str


@dataclass
class Nodo:
    id: str
    time: int
    activo: bool = True
    log: List[Line] = field(default_factory=list)


# Crear nodos a partir del input
def start(parejas: List[Tuple[str, int]]) -> Dict[str, Nodo]:

    nodos = {}
    for id, t in parejas:
        nodos[id] = Nodo(id=id, time=t)

    return nodos

def _last_term_index(n: Nodo) -> Tuple[int, int]:
    if not n.log:
        return (0, -1)
    return (n.log[-1].term, len(n.log) - 1)


def choose_next_leader(nodos: Dict[str, Nodo], mayoria: Optional[int] = None) -> Optional[str]:
    activos = [n for n in nodos.values() if n.activo]
    if not activos:
        return None
    req = mayoria if mayoria is not None else (len(nodos) // 2) + 1

    # candidatos por timeout luego id (tie-breaker)
    candidatos = sorted(activos, key=lambda n: (n.time, n.id))
    votantes = activos

    for cand in candidatos:
        lt_cand = _last_term_index(cand)
        votos = 0
        for v in votantes:
            lt_v = _last_term_index(v)
            if lt_cand >= lt_v:
                votos += 1
        if votos >= req:
            return cand.id

    return candidatos[0].id