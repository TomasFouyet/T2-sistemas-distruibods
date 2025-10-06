from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from utils import AlgorithmResult, File, clean_lines_with_index, gano_mayoria
from .essential import Nodo, start, choose_next_leader
from .event_handler import handle_stop, handle_start, handle_send, handle_spread, handle_log
from database import Database

@dataclass
class Raft:
    nodos: Dict[str, Nodo]
    timeouts: Dict[str, int]
    leader: Optional[str]
    term: int
    mayoria: int
    actions_consolidadas: List[str]
    accepted_at: List[int]
    logs: List[Tuple[int, str]]
    committed: int  # último índice consolidado (-1 si ninguno)
    database: Database

# Esta funcion de parser el header del archivo de entrada
# se realizo con copilot 
def _parse_header_nodes(line: str) -> List[Tuple[str, int]]:
    chunks = [p.strip() for p in line.split(";") if p.strip()]
    pairs: List[Tuple[str, int]] = []
    for ch in chunks:
        sid, to = ch.split(",", 1)
        pairs.append((sid.strip(), int(to.strip())))
    return pairs


def simulate(full_lines: List[str]) -> Tuple[AlgorithmResult, File, Database]:
    is_event_line, cleaned = clean_lines_with_index(full_lines)
    event_global_idx = [i for i, ok in enumerate(is_event_line) if ok]

    if not cleaned:
        # archivo vacío después de limpiar: retorna vacío
        file = File(lines=full_lines, line_event=is_event_line, header={})
        empty_db = Database()
        return AlgorithmResult(actions_accepted=[], consolidaciones=[], logs=[]), file, empty_db

    # Cabecera: nodos (id, timeout)
    id_time = _parse_header_nodes(cleaned[0])
    timeouts = {sid: to for sid, to in id_time}
    nodos = start(id_time)
    mayoria = gano_mayoria(len(nodos))

    # Líder elegido justo antes del primer evento (enunciado)
    leader = choose_next_leader(nodos, mayoria)

    if leader is not None:
        term = 1 
    else:
        term = 0

    ctx = Raft(
        nodos=nodos,
        timeouts=timeouts,
        leader=leader,
        term=term,
        mayoria=mayoria,
        actions_consolidadas=[],
        accepted_at=[],
        logs=[],
        committed=-1,
        database=Database(),
    )

    # Procesar eventos desde cleaned[1:]
    for cleaned_idx, ev in enumerate(cleaned[1:], start=1):
        global_line = event_global_idx[cleaned_idx]
        parts = ev.split(";", 1)
        cmd = parts[0].strip()

        match cmd:
            case "Stop":
                handle_stop(ctx, parts)
            case "Start":
                handle_start(ctx, parts)
            case "Send":
                handle_send(ctx, parts)
            case "Spread":
                handle_spread(ctx, parts, global_line)
            case "Log":
                handle_log(ctx, parts, global_line)
            case _:
                pass

    file = File(
        lines=full_lines,
        line_event=is_event_line,
        header={"nodos": list(nodos.keys()), "timeouts": timeouts},
    )
    sim = AlgorithmResult(
        actions_accepted=ctx.actions_consolidadas,
        consolidaciones=ctx.accepted_at,
        logs=ctx.logs,
    )
    return sim, file, ctx.database
