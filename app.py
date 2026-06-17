# app.py
import json
from flask import Flask, render_template, request
from ai_service import analyze_requirement_with_ai
from dsl_generator import json_to_dsl
from dsl_parser import tokenize, UserStoryCompiler

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    user_prompt = ""
    generated_dsl = ""
    tokens_list = []
    ast_json = ""
    stories = []
    status_message = "Esperando requerimiento bruto para iniciar procesamiento..."
    status_type = "info"

    if request.method == 'POST':
        action = request.form.get('action')
        user_prompt = request.form.get('prompt', '')
        generated_dsl = request.form.get('dsl_code', '')

        if action == 'generate_dsl':
            try:
                # LLAMADA REAL A GEMINI
                raw_json = analyze_requirement_with_ai(user_prompt)
                generated_dsl = json_to_dsl(raw_json)
                status_message = "🚀 Gemini API generó las historias base. Listo para ser compilado."
                status_type = "success"
            except Exception as e:
                status_message = str(e)
                status_type = "error"

        elif action == 'compile_dsl':
            try:
                # 1. Fase de Lexer
                tokens = tokenize(generated_dsl)
                tokens_list = [str(t) for t in tokens]
                
                # 2. Fase de Parser y Semántico
                compiler = UserStoryCompiler(tokens)
                compiler.parse()
                
                # Guardamos el AST formateado como JSON lindo para la pantalla
                ast_json = json.dumps(compiler.ast, indent=2, ensure_ascii=False)
                
                # Extraemos las propiedades internas del AST para pintar las tarjetas finales
                for node in compiler.ast["body"]:
                    props = node["properties"]
                    stories.append({
                        "id": node["id"],
                        "como": props.get("como"),
                        "quiero": props.get("quiero"),
                        "para": props.get("para"),
                        "prioridad": props.get("prioridad", "Media"),
                        "complejidad": props.get("complejidad", 1)
                    })
                
                status_message = f"🔬 Compilación Exitosa: {len(stories)} Historias de Usuario procesadas en el AST."
                status_type = "success"
            except (SyntaxError, NameError) as e:
                status_message = f"⚠️ Error en Compilación: {str(e)}"
                status_type = "error"

    return render_template(
        'index.html',
        user_prompt=user_prompt,
        generated_dsl=generated_dsl,
        tokens_list=tokens_list,
        ast_json=ast_json,
        stories=stories,
        status_message=status_message,
        status_type=status_type
    )

if __name__ == '__main__':
    app.run(debug=True)