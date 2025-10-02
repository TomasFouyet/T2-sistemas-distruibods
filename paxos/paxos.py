# https://github.com/cocagne/paxos/blob/master/paxos/essential.py
# Utilizamos como referencia para estructurar el codigo de este github
# El separa en distintas clases, los diferentes "roles" que puede tener un nodo
# No se copio su codigo, solo se utilizo como referencia para tenerlo organizado
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from collections import Counter

from utils import AlgorithmResult, File, clean_lines_with_index, gano_mayoria
from essential import Acceptor, Proposer, start_acceptors, start_proposers

def _parse_headers(cleaned: List[str]) -> tuple[list[str], list[str], list[str]]:
    if len(cleaned) < 2:
        raise ValueError("Archivo inválido: faltan cabeceras de aceptantes/proponentes")
    acceptors = [x.strip() for x in cleaned[0].split(";") if x.strip()]
    proposers = [x.strip() for x in cleaned[1].split(";") if x.strip()]
    return acceptors, proposers, cleaned[2:]

def simulate(full_lines: List[str]) -> Tuple[SimulationResult, ParseEnvelope]:
    # Limpieza + mapeo de índices globales
    is_event_line, cleaned = clean_lines_with_index(full_lines)
    event_global_idx = [i for i, ok in enumerate(is_event_line) if ok]

    # Cabeceras
    acceptor_ids, proposer_ids, evs = _parse_headers(cleaned)
    A: Dict[str, AcceptorState] = init_acceptors(acceptor_ids)
    P: Dict[str, ProposerState] = init_proposers(proposer_ids)

    total_acceptors = len(acceptor_ids)
    need = majority(total_acceptors)

    accepted_actions: List[str] = []
    accepted_at: List[int] = []
    log_queries: List[Tuple[int, str]] = []

    # Recorremos eventos (los cleaned_idx 0 y 1 son cabeceras)
    for cleaned_idx, ev in enumerate(evs, start=2):
        global_line = event_global_idx[cleaned_idx]
        parts = ev.split(";", 3)  # Accept puede traer 4 piezas
        cmd = parts[0].strip()

        # ---------------- Stop;ID ----------------
        if cmd == "Stop":
            if len(parts) >= 2:
                aid = parts[1].strip()
                if aid in A:
                    A[aid].active = False
            continue

        # ---------------- Start;ID ----------------
        if cmd == "Start":
            if len(parts) >= 2:
                aid = parts[1].strip()
                if aid in A:
                    A[aid].active = True   # conserva promised/accepted previos
            continue

        # ------------- Prepare;PROPOSER;N -------------
        if cmd == "Prepare":
            if len(parts) < 3:
                continue
            proposer = parts[1].strip()
            if proposer not in P:
                continue
            try:
                n = int(parts[2].strip())
            except ValueError:
                continue
            if n < 1:
                continue

            oks = 0
            best_acc_n = -1
            forced_val: Optional[str] = None

            for aid, st in A.items():
                if not st.active:
                    continue
                if st.promised_n is None or n > st.promised_n:
                    st.promised_n = n
                    oks += 1
                    if st.accepted_n is not None and st.accepted_value is not None:
                        if st.accepted_n > best_acc_n:
                            best_acc_n = st.accepted_n
                            forced_val = st.accepted_value
                # else: reject

            if oks >= need:
                P[proposer].prepared_majority[n] = True
                P[proposer].forced_value_by_n[n] = forced_val
            continue

        # -------- Accept;PROPOSER;N;ACTION --------
        if cmd == "Accept":
            if len(parts) < 4:
                continue
            proposer = parts[1].strip()
            if proposer not in P:
                continue
            try:
                n = int(parts[2].strip())
            except ValueError:
                continue
            action = parts[3].strip()

            if not P[proposer].prepared_majority.get(n, False):
                continue

            effective = P[proposer].forced_value_by_n.get(n) or action

            for aid, st in A.items():
                if not st.active:
                    continue
                # Acepta si promised_n <= n
                if st.promised_n is None or n >= st.promised_n:
                    st.accepted_n = n
                    st.accepted_value = effective
            continue

        # ------------------- Learn -------------------
        if cmd == "Learn":
            # mayoría por valor aceptado (independiente de n)
            counter = Counter()
            for st in A.values():
                if st.accepted_value is not None:
                    counter[st.accepted_value] += 1
            if not counter:
                continue
            value, count = counter.most_common(1)[0]
            if count >= need:
                # consolida
                accepted_actions.append(value)
                accepted_at.append(global_line)
                # reset de aceptantes ACTIVOS
                for st in A.values():
                    if st.active:
                        st.promised_n = None
                        st.accepted_n = None
                        st.accepted_value = None
                # proponentes “olvidan” prepares
                for pp in P.values():
                    pp.prepared_majority.clear()
                    pp.forced_value_by_n.clear()
            continue

        # ------------------- Log;Var -------------------
        if cmd == "Log":
            if len(parts) >= 2:
                var = parts[1].strip()
                log_queries.append((global_line, var))
            continue

        # Comando desconocido → ignorar
        continue

    env = ParseEnvelope(
        full_lines=full_lines,
        is_event_line=is_event_line,
        header_meta={"acceptors": acceptor_ids, "proposers": proposer_ids},
    )
    sim = SimulationResult(
        accepted_actions=accepted_actions,
        accepted_consolidated_at=accepted_at,
        log_queries=log_queries,
    )
    return sim, env