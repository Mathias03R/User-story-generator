# dsl_parser.py
import re

TOKEN_TYPES = [
    ('KEYWORD',    r'\b(HISTORIA|COMO|QUIERO|PARA|PRIORIDAD)\b'),
    ('NUMBER',     r'\b\d+\b'),
    ('STRING',     r'"[^"]*"'),
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('COLON',      r':'),
    ('NEWLINE',    r'\n'),
    ('SKIP',       r'[ \t\r]+'),
    ('MISMATCH',   r'.'),
]

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line
    def __repr__(self):
        # Formato limpio: Categoría, lexema y su respectiva línea
        return f"[{self.type}]: '{self.value}' (Línea {self.line})"

def tokenize(dsl_code):
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_TYPES)
    tokens = []
    line_num = 1
    
    # Inicializamos el diccionario de conteo para la interfaz
    counts = { 'KEYWORD': 0, 'IDENTIFIER': 0, 'STRING': 0, 'NUMBER': 0, 'COLON': 0 }
    
    for mo in re.finditer(regex, dsl_code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind in ['KEYWORD', 'IDENTIFIER', 'NUMBER', 'COLON']:
            tokens.append(Token(kind, value, line_num))
            counts[kind] += 1
        elif kind == 'STRING':
            tokens.append(Token(kind, value[1:-1], line_num)) # Quitar comillas
            counts[kind] += 1
        elif kind == 'NEWLINE':
            line_num += 1
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            # Lanzamos un error léxico explícito detallando la línea exacta
            raise SyntaxError(f"Error Léxico: Componente inválido {repr(value)} detectado en la línea {line_num}")
            
    return tokens, counts

class UserStoryCompiler:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.ast = {"type": "Program", "body": []}
        self.VERB_COMPLEXITY = {
            'pagar': 8, 'pasarela': 8, 'encriptar': 13, 'seguridad': 8,
            'sincronizar': 8, 'tiempo real': 13, 'notificar': 5, 'enviar': 3,
            'crear': 3, 'registrar': 3, 'eliminar': 2, 'listar': 2,
            'visualizar': 2, 'modificar': 3, 'subir': 5, 'audio': 8
        }

    def peek(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def advance(self):
        token = self.peek()
        self.current += 1
        return token

    def match(self, type, value=None):
        token = self.peek()
        if token and token.type == type and (value is None or token.value == value):
            self.advance()
            return True
        return False

    def parse(self):
        while self.peek():
            if self.match('KEYWORD', 'HISTORIA'):
                node = self.parse_story()
                self.ast["body"].append(node)
            else:
                token_invalido = self.peek()
                raise SyntaxError(f"Error Sintáctico: Se encontró un elemento fuera de lugar '{token_invalido.value}' en la línea {token_invalido.line}. Se esperaba la estructura 'HISTORIA'.")

    def parse_story(self):
        id_token = self.advance()
        if not id_token or id_token.type != 'IDENTIFIER':
            linea = id_token.line if id_token else "Final"
            raise SyntaxError(f"Error Sintáctico: Se requería un IDENTIFICADOR para la historia en la línea {linea}")
        
        story_node = { "type": "UserStoryNode", "id": id_token.value, "properties": {} }

        # Validamos el cuerpo rígido de la gramática
        while self.peek() and self.peek().value in ['COMO', 'QUIERO', 'PARA', 'PRIORIDAD']:
            key = self.advance().value
            
            if not self.match('COLON'):
                token_actual = self.peek()
                linea = token_actual.line if token_actual else "desconocida"
                raise SyntaxError(f"Error Sintáctico: Falta el delimitador ':' después de la propiedad '{key}' en la línea {linea}")
                
            val_token = self.advance()
            if not val_token or val_token.type != 'STRING':
                linea = val_token.line if val_token else "desconocida"
                raise SyntaxError(f"Error Sintáctico: El valor asignado a '{key}' debe ser un texto encerrado en comillas en la línea {linea}")
            
            story_node["properties"][key.lower()] = val_token.value

        accion = story_node["properties"].get("quiero", "")
        story_node["properties"]["complejidad"] = self.calculate_semantic_complexity(accion)
        return story_node

    def calculate_semantic_complexity(self, text):
        text_lower = text.lower()
        max_points = 1
        for word, points in self.VERB_COMPLEXITY.items():
            if word in text_lower:
                if points > max_points: max_points = points
        return max_points