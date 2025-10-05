from collections import Counter
from typing import List, Optional
from paxos.essential import Acceptor, Proposer

def handle_stop(ctx, parts: List[str]) -> None:
    if len(parts) >= 2:
        aid = parts[1].strip()
        st = ctx.A.get(aid)
        if st:
            st.active = False

def handle_start(ctx, parts: List[str]) -> None:
    if len(parts) >= 2:
        aid = parts[1].strip()
        st = ctx.A.get(aid)
        if st:
            st.active = True

def handle_prepare(ctx, parts: List[str]) -> None:
    if len(parts) < 3:
        return
    proposer = parts[1].strip()
    Pst = ctx.P.get(proposer)
    if not Pst:
        return
    try:
        n = int(parts[2].strip())
    except ValueError:
        return
    if n < 1:
        return

    oks = 0
    best_acc_n = -1
    forced_val: Optional[str] = None

    for st in ctx.A.values():
        if not st.active:
            continue
        if st.promesa_acordada is None or n > st.promesa_acordada:
            st.promesa_acordada = n
            oks += 1
            if st.propuesta_aceptada is not None and st.accepted_value is not None:
                if st.propuesta_aceptada > best_acc_n:
                    best_acc_n = st.propuesta_aceptada
                    forced_val = st.accepted_value

    if oks >= ctx.majority_needed:
        Pst.accepted_majority[n] = True
        Pst.forced_value[n] = forced_val

def handle_accept(ctx, parts: List[str]) -> None:
    if len(parts) < 4:
        return
    proposer = parts[1].strip()
    Pst = ctx.P.get(proposer)
    if not Pst:
        return
    try:
        n = int(parts[2].strip())
    except ValueError:
        return
    action = parts[3].strip()

    if not Pst.accepted_majority.get(n, False):
        return

    effective = Pst.forced_value.get(n) or action

    for st in ctx.A.values():
        if not st.active:
            continue
        if st.promesa_acordada is None or n >= st.promesa_acordada:
            st.propuesta_aceptada = n
            st.accepted_value = effective

def handle_learn(ctx, global_line: int) -> None:
    counter = Counter()
    for st in ctx.A.values():
        if st.accepted_value is not None:
            counter[st.accepted_value] += 1
    if not counter:
        return
    value, count = counter.most_common(1)[0]
    if count >= ctx.majority_needed:
        ctx.actions_consolidadas.append(value)
        ctx.accepted_at.append(global_line)
        # resetiamos los activos
        for st in ctx.A.values():
            if st.active:
                st.promesa_acordada = None
                st.propuesta_aceptada = None
                st.accepted_value = None
        # Aqui los propontnetes de olvidan de lo que habian aceptado
        # Como lo piden en esta ejecucion de paxos
        for p in ctx.P.values():
            p.accepted_majority.clear()
            p.forced_value.clear()

def handle_log(ctx, parts: List[str], global_line: int) -> None:
    if len(parts) >= 2:
        var = parts[1].strip()
        ctx.logs.append((global_line, var))