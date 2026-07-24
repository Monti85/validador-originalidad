# 🎓 Validador de Originalidad e Inteligencia Artificial — UTEC

Herramienta académica desarrollada en Python con Streamlit y Google Gemini AI para analizar documentos de estudiantes (PDF y TXT). Detecta contenido generado por IA, evalúa la coherencia del pensamiento y verifica la validez de las citas bibliográficas.

---

## 🚀 Instalación rápida

> **Requisito previo:** Tener instalado Python 3.9 o superior.
> Si no lo tienes, seguí el [Manual de Instalación Completo](MANUAL_INSTALACION.txt).

```bash
# 1. Clonar el repositorio
git clone https://github.com/Monti85/validador-originalidad.git
cd validador-originalidad

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
streamlit run app.py
```

Luego abrí tu navegador en: **http://localhost:8501**

---

## 🔑 API Key de Google Gemini (gratis)

La aplicación requiere una clave de API de Google AI Studio (gratuita):

1. Entrá a 👉 [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Iniciá sesión con tu cuenta de Google
3. Hacé clic en **"Create API key"** → **"Create new project"**
4. Copiá la clave generada (empieza con `AIzaSy...`)
5. Pegala en el campo **"Gemini API Key"** de la barra lateral de la app

> 📌 El plan gratuito incluye hasta 200 análisis por día por modelo.
> Si un modelo alcanza su límite, la app intenta automáticamente con el siguiente.

---

## 📋 Características

- 📄 **Soporte de formatos:** PDF y TXT (hasta 200 MB)
- 🔍 **Análisis completo:** Todo el documento (hasta 120,000 caracteres)
- 🤖 **Detección de IA:** Porcentaje estimado de contenido generado por IA
- 🧠 **Coherencia:** Evaluación de profundidad analítica y originalidad
- 📚 **Citas bibliográficas:** Verificación de formato APA/IEEE/Vancouver
- 💡 **Recomendaciones:** Sugerencias constructivas para mejorar el trabajo
- 🔄 **Reintento automático:** Si se agota la cuota, reintenta automáticamente

---

## 🛠️ Requisitos del sistema

| Componente | Versión mínima |
|---|---|
| Python | 3.9+ |
| Sistema operativo | Windows 10/11, macOS, Linux |
| RAM | 512 MB |
| Conexión a internet | Requerida (para la API de Gemini) |

---

## 📦 Dependencias

```
streamlit
google-genai
pypdf
```

---

## 📁 Estructura del proyecto

```
validador-originalidad/
├── app.py                    # Aplicación principal
├── requirements.txt          # Dependencias de Python
├── README.md                 # Este archivo
├── MANUAL_INSTALACION.txt    # Guía paso a paso desde cero
└── test_api.py               # Script de diagnóstico de API Key
```

---

## ❓ Problemas frecuentes

| Error | Solución |
|---|---|
| `streamlit: command not found` | Ejecutar `pip install streamlit` |
| `API Key inválida` | Verificar que la clave fue copiada completa desde AI Studio |
| `Cuota agotada` | Esperar a las 21:00 ARG (reinicio de cuota diaria) o usar otro modelo |
| PDF sin texto extraído | El PDF puede ser una imagen escaneada; convertirlo a texto primero |

---

## 👨‍💻 Desarrollado para

**UTEC - Universidad Tecnológica** · 2026  
Herramienta de apoyo académico para validación de originalidad e integridad de trabajos estudiantiles.
