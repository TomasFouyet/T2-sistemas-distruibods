# https://github.com/cocagne/paxos/blob/master/paxos/essential.py
# Utilizamos como referencia para estructurar el codigo de este github
# El separa en distintas clases, los diferentes "roles" que puede tener un nodo
# No se copio su codigo, solo se utilizo como referencia para tenerlo organizado
from __future__ import annotations
from typing import Dict, List, Tuple

from dataclasses import dataclass

from utils import AlgorithmResult, File, clean_lines_with_index, gano_mayoria
from paxos.essential import Acceptor, Proposer, start_acceptors, start_proposers
from paxos.event_handler import (
    handle_stop, handle_start, handle_prepare, handle_accept,
    handle_learn, handle_log
)
from database import Database

@dataclass
class Paxos:
    A: Dict[str, Acceptor]
    P: Dict[str, Proposer]
    majority_needed: int
    actions_consolidadas: List[str]
    accepted_at: List[int]
    logs: List[Tuple[int, str]]
    database: Database

# generado con copilot para parsear los headers del archivo de lectura
def _parse_headers(cleaned: List[str]) -> tuple[list[str], list[str], list[str]]:
    if len(cleaned) < 2:
        raise ValueError("Archivo invalido")
    acceptors = [x.strip() for x in cleaned[0].split(";") if x.strip()] # Aceptor en linea 0
    proposers = [x.strip() for x in cleaned[1].split(";") if x.strip()] # Proposer en linea 1
    return acceptors, proposers, cleaned[2:]


# Simula la ejecucion de Paxos con las lineas del archivo de test
def simulate(full_lines: List[str]) -> Tuple[AlgorithmResult, File, Database]:
    is_event_line, cleaned = clean_lines_with_index(full_lines)
    event_global_idx = [i for i, ok in enumerate(is_event_line) if ok]

    acceptor_ids, proposer_ids, evs = _parse_headers(cleaned)
    Acceptors = start_acceptors(acceptor_ids)
    Proposers = start_proposers(proposer_ids)
    majority_needed = gano_mayoria(len(acceptor_ids))

    # Contexto de la simulacion
    ctx = Paxos(
        A=Acceptors, P=Proposers, majority_needed=majority_needed,
        actions_consolidadas=[], accepted_at=[], logs=[], database=Database()
    )

    # Procesar eventos
    for cleaned_idx, ev in enumerate(evs, start=2):
        global_line = event_global_idx[cleaned_idx]
        parts = ev.split(";", 3)
        event = parts[0].strip()

        match event:
            case "Stop":
                handle_stop(ctx, parts)
            case "Start":
                handle_start(ctx, parts)
            case "Prepare":
                handle_prepare(ctx, parts)
            case "Accept":
                handle_accept(ctx, parts)
            case "Learn":
                handle_learn(ctx, global_line)
            case "Log":
                handle_log(ctx, parts, global_line)
            case _:
                pass

    # Preparar resultados
    file = File(
        lines=full_lines,
        line_event=is_event_line,
        header={"acceptors": acceptor_ids, "proposers": proposer_ids},
    )
    simulation = AlgorithmResult(
        actions_accepted=ctx.actions_consolidadas,
        consolidaciones=ctx.accepted_at,
        logs=ctx.logs,
    )
    return simulation, file, ctx.database