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

# Elige como lider al nodod activo con menor time y si hay
# empate, el de menor id
def choose_next_leader(nodos: Dict[str, Nodo]) -> Optional[str]:

    activos = []
    for nodo in nodos.values():
        if nodo.activo:
            activos.append(nodo)
    if not activos:
        return None
    activos.sort(key=lambda nodo: (nodo.time, nodo.id))
    return activos[0].id