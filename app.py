# app.py
import json
import os
from flask import Flask, render_template, request, redirect, url_for, session
from ai_service import analyze_requirement_with_ai
from dsl_generator import json_to_dsl
from dsl_parser import tokenize, UserStoryCompiler

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "un_secreto_super_seguro_123")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        session['user_prompt'] = request.form.get('prompt', '')
        session['generated_dsl'] = request.form.get('dsl_code', '')

        if action == 'generate_dsl':
            try:
                raw_json = analyze_requirement_with_ai(session['user_prompt'])
                session['generated_dsl'] = json_to_dsl(raw_json)
                session['status_message'] = "🚀 Gemini API generó las historias base de forma exitosa."
                session['status_type'] = "success"
                session['compiler_error'] = "" # Limpiamos errores previos
            except Exception as e:
                session['status_message'] = "⚠️ Falló la comunicación con la IA."
                session['status_type'] = "error"
                session['compiler_error'] = str(e)

        elif action == 'compile_dsl':
            try:
                # 1. Ejecución del Analizador Léxico
                tokens, counts = tokenize(session['generated_dsl'])
                session['tokens_list'] = [str(t) for t in tokens]
                session['token_counts'] = counts # Guardamos cantidades por tipo
                
                # 2. Ejecución del Parser y Semántico
                compiler = UserStoryCompiler(tokens)
                compiler.parse()
                
                session['ast_json'] = json.dumps(compiler.ast, indent=2, ensure_ascii=False)
                
                stories = []
                for node in compiler.ast["body"]:
                    props = node["properties"]
                    stories.append({
                        "id": node["id"], "como": props.get("como"),
                        "quiero": props.get("quiero"), "para": props.get("para"),
                        "prioridad": props.get("prioridad", "Media"), "complejidad": props.get("complejidad", 1)
                    })
                session['stories'] = stories
                session['status_message'] = f"🔬 Análisis completado con éxito. {len(stories)} estructuras en el AST."
                session['status_type'] = "success"
                session['compiler_error'] = "" # No hay errores
                
            except SyntaxError as e:
                # Capturamos errores léxicos o sintácticos controlados
                session['status_message'] = "⚠️ Error detectado durante el procesamiento."
                session['status_type'] = "error"
                session['compiler_error'] = str(e) # Mensaje detallado con línea
                session['stories'] = []
                session['ast_json'] = ""
                session['tokens_list'] = []
                session['token_counts'] = {}

        return redirect(url_for('index'))

    # Petición GET: Carga de la vista
    return render_template(
        'index.html',
        user_prompt=session.get('user_prompt', ''),
        generated_dsl=session.get('generated_dsl', ''),
        tokens_list=session.get('tokens_list', []),
        token_counts=session.get('token_counts', {}),
        compiler_error=session.get('compiler_error', ''),
        ast_json=session.get('ast_json', ''),
        stories=session.get('stories', []),
        status_message=session.get('status_message', "Esperando requerimiento inicial..."),
        status_type=session.get('status_type', "info")
    )

if __name__ == '__main__':
    app.run(debug=True)