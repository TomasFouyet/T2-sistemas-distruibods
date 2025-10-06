from __future__ import annotations
from typing import List, Tuple
from collections import OrderedDict
import os

class Database:
    
    def __init__(self):
        self.variables: OrderedDict[str, str] = OrderedDict()
        self.log_events: List[Tuple[str, str]] = []
    
    def apply_action(self, action: str) -> None:
        if not action:
            return
            
        # Formato de la accion: SET-variable-value, ADD-variable-value, o DEL-variable
        if action.startswith("SET-"):
            parts = action[4:].split("-", 1)
            if len(parts) == 2:
                var_name, value = parts
                self.variables[var_name] = value
        elif action.startswith("ADD-"):
            parts = action[4:].split("-", 1)
            if len(parts) == 2:
                var_name, value = parts
                if var_name in self.variables:
                    self.variables[var_name] += value
                else:
                    self.variables[var_name] = value
        elif action.startswith("DEL-"):
            var_name = action[4:]
            if var_name in self.variables:
                del self.variables[var_name]
    
    def log_variable(self, variable_name: str) -> None:
        # Logueamos el valor actual de la variable a la base de datos
        if variable_name in self.variables:
            self.log_events.append((variable_name, self.variables[variable_name]))
        else:
            self.log_events.append((variable_name, "Variable no existe"))
    
    def generate_log_file_content(self) -> str:
        # Generamos el contenido del archivo de log segun las especificaciones
        lines = []
        
        # Part 1: LOGS section
        lines.append("LOGS")
        if not self.log_events:
            lines.append("No hubo logs")
        else:
            for var_name, value in self.log_events:
                lines.append(f"{var_name}={value}")
        
        # Part 2: DATABASE section
        lines.append("BASE DE DATOS")
        if not self.variables:
            lines.append("No hay datos")
        else:
            # Mantenemos el orden de inserción/consolidación
            for var_name, value in self.variables.items():
                lines.append(f"{var_name}={value}")
        
        return "\n".join(lines)
    
    def save_to_file(self, algorithm: str, test_filename: str) -> None:
        # Extraemos el nombre del archivo sin la extension
        base_name = os.path.splitext(os.path.basename(test_filename))[0]
        output_filename = f"{algorithm}_{base_name}.txt"
        output_path = os.path.join("logs", output_filename)
        
        # Aseguramos que el directorio de logs existe
        os.makedirs("logs", exist_ok=True)
        
        # Escribimos el contenido del log
        content = self.generate_log_file_content()
        with open(output_path, 'w', encoding='UTF-8') as f:
            f.write(content + '\n')
