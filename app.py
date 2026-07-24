import streamlit as st
import google.generativeai as genai
import pypdf # Librería para leer archivos PDF

# Configuración de la interfaz
st.set_page_config(page_title="Validador de Originalidad - UTEC", page_icon="📝")
st.title("📝 Validador de Originalidad e IA")
st.write("Sube un documento para analizar si contiene patrones de Inteligencia Artificial o falta de originalidad.")

# Configurar API Key de Google
api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

uploaded_file = st.file_uploader("Carga tu archivo (PDF o TXT)", type=["pdf", "txt"])

def extract_text(file):
    if file.type == "application/pdf":
        reader = pypdf.PdfReader(file)
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    else:
        return file.read().decode("utf-8")

if uploaded_file and api_key:
    # Extraer texto del archivo
    text_content = extract_text(uploaded_file)
    
    st.subheader("Texto extraído (vista previa):")
    st.text_area("Contenido", text_content[:500] + "...", height=100)
    
    if st.button("Analizar Documento"):
        with st.spinner("Analizando el documento con IA..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Actúa como un evaluador académico experto. Analiza el siguiente texto académico y determina:
                1. **Probabilidad de generación por IA (0-100%)**: Identifica patrones sintéticos, repetición de estructuras o vocabulario típico de LLMs.
                2. **Coherencia y Originalidad**: Revisa la profundidad de las ideas expresadas.
                3. **Verificación de Citas y Referencias**: Analiza si las citas incluidas parecen reales y bien formateadas.
                4. **Recomendaciones**: Sugerencias para que el estudiante mejore la redacción.

                Texto a analizar:
                ---
                {text_content}
                ---
                Devuelve el análisis en un formato claro, organizado y fácil de leer.
                """
                
                response = model.generate_content(prompt)
                
                st.success("¡Análisis completado!")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error al procesar el análisis: {e}")