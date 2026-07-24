"""
Script de diagnóstico v3: busca automáticamente qué modelo funciona con tu clave.
Uso: python test_api.py TU_API_KEY_AQUI
"""
import sys
from google import genai
from google.genai import types

if len(sys.argv) < 2:
    print("Uso: python test_api.py TU_API_KEY_AQUI")
    sys.exit(1)

api_key = sys.argv[1].strip()
client = genai.Client(api_key=api_key)

# Modelos a probar - con y sin prefijo models/
CANDIDATES = [
    "gemini-2.5-flash",
    "models/gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "models/gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "models/gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "models/gemini-2.0-flash",
    "gemini-flash-latest",
    "models/gemini-flash-latest",
    "gemini-flash-lite-latest",
    "models/gemini-flash-lite-latest",
]

print("\n=== Buscando modelo que funcione con tu clave ===\n")
working_model = None

for model in CANDIDATES:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Di solo: OK",
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=5)
        )
        print(f"  ✅ FUNCIONA: {model}  →  Respuesta: {response.text.strip()}")
        if working_model is None:
            working_model = model
        break  # Encontramos uno que funciona, podemos parar
    except Exception as e:
        err = str(e)
        if "limit: 0" in err or "RESOURCE_EXHAUSTED" in err:
            print(f"  ⚠️  {model} → Cuota del proyecto agotada hoy")
        elif "NOT_FOUND" in err or "404" in err:
            print(f"  ❌ {model} → No disponible para generateContent")
        elif "INVALID_ARGUMENT" in err or "API_KEY" in err:
            print(f"  🔑 {model} → Problema con la API Key")
            break
        else:
            print(f"  ❌ {model} → {err[:120]}")

print()
if working_model:
    print(f"🎉 USA ESTE MODELO EN LA APP: {working_model}")
else:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("RESULTADO: La cuota gratuita del proyecto está agotada para hoy.")
    print()
    print("OPCIONES:")
    print("  1. Espera a las 21:00 (hora Argentina) — las cuotas se reinician.")
    print("  2. Crea un NUEVO proyecto en AI Studio:")
    print("     → https://aistudio.google.com/apikey")
    print("     → Haz clic en 'Create API key' → 'Create new project'")
    print("     → Genera la clave en el NUEVO proyecto")
    print("  3. Activa facturación (pago por uso):")
    print("     → https://console.cloud.google.com/billing")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
