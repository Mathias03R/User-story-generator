# dsl_generator.py

def json_to_dsl(json_data):
    """
    Toma una lista de diccionarios (Historias) y genera el string de código DSL equivalente
    """
    dsl_lines = []
    for index, item in enumerate(json_data, start=1):
        dsl_lines.append(f"HISTORIA US_{index:03d}")
        dsl_lines.append(f"    COMO: \"{item.get('como', 'Usuario')}\"")
        dsl_lines.append(f"    QUIERO: \"{item.get('quiero', '')}\"")
        dsl_lines.append(f"    PARA: \"{item.get('para', '')}\"")
        dsl_lines.append(f"    PRIORIDAD: \"{item.get('prioridad', 'Media')}\"")
        dsl_lines.append("") # Línea en blanco de separación
        
    return "\n".join(dsl_lines)