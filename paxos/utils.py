from __future__ import annotations
from sys import argv
import os
from typing import List, Tuple, Dict
import collections
import itertools
from dataclasses import dataclass
import enum

@dataclass
class AlgorithmResult:
    actions_accepted: List[str] # Se guardan en orden para su buen registro
    consolidaciones: List[int]
    logs: List[Tuple[int, str]]

@dataclass
class File:
    lines: List[str]
    line_event: List[bool]
    header: Dict[str, object]
    

def gano_mayoria(n_total: int) -> int:
    return (n_total // 2) + (n_total % 2)

def strip_line(line: str) -> str:
    i = line.find("#")
    return line if i == -1 else line[:i]


def clean_lines_with_index(lines: List[str]) -> Tuple[List[bool], List[str]]:
    is_event = []
    events = []
    for raw in lines:
        new_line = strip_line(raw).strip() # elimina comentarios y espacios
        if new_line:
            is_event.append(True)
            events.append(new_line)
        else:
            is_event.append(False)
    return is_event, events