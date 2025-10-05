from __future__ import annotations
from typing import List, Optional
from paxos.utils import gano_mayoria
from .essential import Nodo, choose_next_leader, Line

def _have_majority(ctx, index: int, entry: Line) -> bool:
    replicas = 0
    for s in ctx.nodos.values():
        if index < len(s.log):
            e = s.log[index]
            if e.action == entry.action and e.term == entry.term:
                replicas += 1
    return replicas >= ctx.mayoria

def _recompute_commit(ctx, global_line: int) -> None:
    """
    Regla de Raft:
      - Se puede COMMIT un índice m si:
           1) mayoría de nodos tienen la entrada del líder en m, y
           2) la entrada en m es del término ACTUAL del líder.
      - Cuando se committea m (de término actual), también se consideran
        COMMIT todas las entradas previas (< m) aunque sean de términos anteriores
        (consolidación indirecta), siempre manteniendo el orden.
    """
    if ctx.leader is None:
        return
    L = ctx.nodos[ctx.leader].log
    if not L:
        return

    # buscar el mayor índice 'm' ≥ committed+1 que cumpla (mayoría) y (term actual)
    m = None
    i = max(ctx.committed + 1, 0)
    while i < len(L):
        e = L[i]
        if e.term == ctx.term and _have_majority(ctx, i, e):
            m = i  # candidato
        i += 1

    if m is None or m <= ctx.committed:
        return

    # Commit secuencial desde committed+1 hasta m (incluye indirectos)
    for k in range(ctx.committed + 1, m + 1):
        entry = L[k]
        ctx.actions_consolidadas.append(entry.action)
        ctx.accepted_at.append(global_line)
    ctx.committed = m


def handle_stop(ctx, parts: List[str]) -> None:
    if len(parts) >= 2:
        nodo_id = parts[1].strip()
        nodo = ctx.nodos.get(nodo_id)
        if not nodo:
            return
        nodo.activo = False
        if ctx.leader == nodo_id:
            new_leader = choose_next_leader(ctx.nodos)
            if new_leader is not None:
                ctx.term += 1
            ctx.leader = new_leader

def handle_start(ctx, parts: List[str]) -> None:
    if len(parts) >= 2:
        nodo_id = parts[1].strip()
        svr = ctx.nodos.get(nodo_id)
        if not svr:
            return
        svr.activo = True
        if ctx.leader is None:
            new_leader = choose_next_leader(ctx.nodos)
            if new_leader is not None:
                ctx.term += 1
            ctx.leader = new_leader

def handle_send(ctx, parts: List[str]) -> None:
    if ctx.leader is None:
        return
    leader = ctx.nodos[ctx.leader]
    if not leader.activo:
        return
    if len(parts) >= 2:
        action = parts[1].strip()
        leader.log.append(Line(action=action, term=ctx.term))

def handle_spread(ctx, parts: List[str], global_line: int) -> None:
    if ctx.leader is None:
        return
    leader = ctx.nodos[ctx.leader]
    if not leader.activo:
        return

    targets = []
    if len(parts) >= 2:
        s = parts[1].strip()
        if s.startswith('[') and s.endswith(']'):
            inner = s[1:-1].strip()
            targets = [p.strip() for p in inner.split(',')] if inner else []

    leader_copy = leader.log[:]
    for nodo_id in targets:
        nodo = ctx.nodos.get(nodo_id)
        if nodo and nodo.activo:
            nodo.log = leader_copy[:]

    _recompute_commit(ctx, global_line)

def handle_log(ctx, parts: List[str], global_line: int) -> None:
    if len(parts) >= 2:
        var = parts[1].strip()
        ctx.logs.append((global_line, var))
