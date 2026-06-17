# ai_service.py
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# Definimos la estructura estricta que esperamos de la IA usando Pydantic
class UserStorySchema(BaseModel):
    como: str = Field(description="El rol o tipo de usuario. Ejemplo: Cliente, Administrador")
    quiero: str = Field(description="La acción o funcionalidad requerida. Ejemplo: Registrar un usuario, Pagar con tarjeta")
    para: str = Field(description="El beneficio o valor de la acción. Ejemplo: mantener mis datos seguros")
    prioridad: str = Field(description="Debe ser estrictamente una de estas opciones: Alta, Media, Baja")

class RequirementReport(BaseModel):
    historias: List[UserStorySchema]

def analyze_requirement_with_ai(prompt_text):
    """
    Se conecta con la API de Gemini usando la SDK oficial de 2026.
    Fuerza al modelo a devolver una estructura JSON perfecta basada en nuestro esquema.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    print(api_key)
    if not api_key:
        raise ValueError("❌ Error: La variable de entorno GEMINI_API_KEY no está configurada.")

    # Inicializamos el cliente oficial de Gemini
    client = genai.Client(api_key=api_key)
    
    system_instruction = (
        "Eres un Business Analyst experto en metodologías ágiles. Tu trabajo es tomar un requerimiento "
        "en lenguaje natural y desglosarlo en historias de usuario atómicas bajo el formato estándar: "
        "COMO, QUIERO, PARA. Clasifica la prioridad según el impacto del negocio."
    )

    try:
        # Usamos el modelo gemini-2.5-flash optimizado para velocidad y estructuración
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Transforma el siguiente requerimiento en historias de usuario estructuradas: {prompt_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=RequirementReport, # Forzamos la salida estructurada
                temperature=0.2
            ),
        )
        
        # La respuesta ya es un string JSON válido que cumple con RequirementReport
        import json
        data = json.loads(response.text)
        return data.get("historias", [])
        
    except Exception as e:
        raise RuntimeError(f"Error al comunicarse con la API de Gemini: {str(e)}")