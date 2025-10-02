from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Acceptor:
    promesa_acordada: int | None = None
    propuesta_aceptada: int | None = None
    accepted_value: str | None = None
    active: bool = True

@dataclass
class Proposer:
    accepted_majority: Dict[int, bool]
    forced_value: Dict[int, str | None]



def start_acceptors(ids: List[str]) -> Dict[str, Acceptor]:
    acceptors = {}
    for i in ids:
        acceptors[i] = Acceptor()
    return acceptors

def start_proposers(ids: List[str]) -> Dict[str, Proposer]:
    proposers = {}
    for p in ids:
        proposers[p] = Proposer(prepared_majority={}, forced_value_by_n={})
    return proposers
