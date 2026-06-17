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
        return f"[{self.type}: {repr(self.value)} (Línea {self.line})]"

def tokenize(dsl_code):
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_TYPES)
    tokens = []
    line_num = 1
    
    for mo in re.finditer(regex, dsl_code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind in ['KEYWORD', 'IDENTIFIER', 'NUMBER', 'COLON']:
            tokens.append(Token(kind, value, line_num))
        elif kind == 'STRING':
            tokens.append(Token(kind, value[1:-1], line_num))
        elif kind == 'NEWLINE':
            line_num += 1
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"❌ Error Léxico: Carácter ilegal {repr(value)} en la línea {line_num}")
    return tokens

class UserStoryCompiler:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.ast = {"type": "Program", "body": []} # Raíz del Árbol de Sintaxis Abstracta
        
        # Diccionario semántico de verbos de infraestructura
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
                self.advance()

    def parse_story(self):
        id_token = self.advance()
        if id_token.type != 'IDENTIFIER':
            raise SyntaxError(f"❌ Error Sintáctico: Se esperaba un identificador de historia en la línea {id_token.line}")
        
        # Creamos un Nodo del AST específico para este bloque
        story_node = {
            "type": "UserStoryNode",
            "id": id_token.value,
            "properties": {}
        }

        while self.peek() and self.peek().value in ['COMO', 'QUIERO', 'PARA', 'PRIORIDAD']:
            key = self.advance().value
            self.match('COLON')
            val_token = self.advance()
            
            if val_token.type != 'STRING':
                raise SyntaxError(f"❌ Error Sintáctico: El valor de {key} debe ser un string entre comillas.")
            
            story_node["properties"][key.lower()] = val_token.value

        # --- ANÁLISIS SEMÁNTICO (Inyección de Complejidad en el AST) ---
        accion = story_node["properties"].get("quiero", "")
        story_node["properties"]["complejidad"] = self.calculate_semantic_complexity(accion)
        
        return story_node

    def calculate_semantic_complexity(self, text):
        text_lower = text.lower()
        max_points = 1
        for word, points in self.VERB_COMPLEXITY.items():
            if word in text_lower:
                if points > max_points:
                    max_points = points
        return max_points