from __future__ import annotations  # Solo lo dejo por si lo necesitan. Lo pueden eliminar
from sys import argv

# Librerías adicionales por si las necesitan
# No son obligatorias y no tampoco tienen que usarlas todas
# No pueden agregar ningun otro import que no esté en esta lista
import os
import typing
import collections
import itertools
import dataclasses
import enum

# Recuerda que no se permite importar otros módulos/librerías a excepción de los creados
# por ustedes o las ya incluidas en este main.py

# Importamos los modulos de paxos y raft
import paxos.paxos as paxos_module
import raft.raft as raft_module

def run_algorithm(algorithm: str, test_file_path: str) -> None:
    # Ejecutamos el algoritmo especificado en el archivo de test y generamos el archivo de log
    # Leemos el archivo de test
    with open(test_file_path, 'r', encoding='UTF-8') as f:
        lines = f.readlines()
    
    # Eliminamos las nuevas lineas pero mantenemos la estructura
    lines = [line.rstrip('\n\r') for line in lines]
    
    # Ejecutamos el algoritmo apropiado
    if algorithm.lower() == 'paxos':
        simulation_result, file_result, database = paxos_module.simulate(lines)
    elif algorithm.lower() == 'raft':
        simulation_result, file_result, database = raft_module.simulate(lines)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    # Generamos y guardamos el archivo de log
    database.save_to_file(algorithm, test_file_path)

if __name__ == "__main__":
    if len(argv) != 3:
        print("Usage: python3 main.py <ALGORITHM> <TEST_FILE_PATH>")
        print("Example: python3 main.py Paxos casos_Paxos/test_01.txt")
        exit(1)
    
    algorithm = argv[1]
    test_file_path = argv[2]
    
    # Validamos el algoritmo
    if algorithm not in ['Paxos', 'Raft']:
        print(f"Error: Unknown algorithm '{algorithm}'. Must be 'Paxos' or 'Raft'")
        exit(1)
    
    # Validamos que el archivo exista
    if not os.path.exists(test_file_path):
        print(f"Error: Test file '{test_file_path}' not found")
        exit(1)
    
    try:
        run_algorithm(algorithm, test_file_path)
        print(f"Successfully executed {algorithm} on {test_file_path}")
    except Exception as e:
        print(f"Error executing {algorithm}: {e}")
        exit(1)
