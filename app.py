import streamlit as st
import pypdf
import json

# Soporte flexible para librerías de Google Gemini (google-genai y google-generativeai)
try:
    from google import genai
    from google.genai import types
    USE_NEW_GENAI = True
except ImportError:
    try:
        import google.generativeai as genai
        USE_NEW_GENAI = False
    except ImportError:
        st.error("No se encontró la librería de Google Gemini. Por favor ejecuta: `pip install google-genai google-generativeai`")
        st.stop()

# -----------------------------------------------------------------------------
# Configuración de Página e Identidad Visual Académica (UTEC)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Validador de Originalidad e IA - UTEC",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para la interfaz académica UTEC
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #002F6C 0%, #005691 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: #E2E8F0;
        font-size: 1.1rem;
        margin: 0;
    }
    
    .badge-utec {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Encabezado Principal
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <span class="badge-utec">UTEC · Herramienta Académica</span>
    <h1>🎓 Validador de Originalidad e Inteligencia Artificial</h1>
    <p>Evaluación integral de documentos académicos: detección de patrones de IA, coherencia de pensamiento y verificación de citas bibliográficas.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Panel Lateral (Sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    
    api_key = st.text_input(
        "Gemini API Key:",
        type="password",
        help="Ingresa tu clave de API de Google Gemini.",
        placeholder="AIzaSy..."
    )
    
    if api_key:
        st.success("🔑 API Key ingresada correctamente", icon="✅")
    else:
        st.warning("⚠️ Ingresa tu API Key para comenzar", icon="🔑")
        st.markdown("[¿Cómo obtener tu API Key de Gemini gratis?](https://aistudio.google.com/app/apikey)")
        
    st.divider()
    st.markdown("### 🤖 Modelo de IA")
    selected_model = st.selectbox(
        "Selecciona el modelo Gemini:",
        ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0,
        help="gemini-1.5-flash es el modelo más rápido y estable disponible para cuentas estándar."
    )
    
    st.divider()
    st.markdown("### ℹ️ Especificaciones")
    st.info(f"**Modelo activo:** `{selected_model}`\n\n**Formatos:** PDF y TXT")
    st.divider()
    st.caption("UTEC - Universidad Tecnológica · 2026")

# -----------------------------------------------------------------------------
# Lógica de Extracción e Integración con Gemini
# -----------------------------------------------------------------------------
def extract_text_from_file(uploaded_file) -> str:
    """Extrae texto plano de archivos PDF y TXT con manejo de excepciones."""
    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ValueError("El archivo PDF está protegido con contraseña.")
            
            text_pages = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_pages.append(extracted)
            
            full_text = "\n\n".join(text_pages).strip()
            if not full_text:
                raise ValueError("No se pudo extraer texto legible del PDF. Es posible que sea un documento escaneado (imágenes).")
            return full_text
            
        elif uploaded_file.name.lower().endswith(".txt"):
            content = uploaded_file.read()
            try:
                return content.decode("utf-8").strip()
            except UnicodeDecodeError:
                return content.decode("latin-1").strip()
        else:
            raise ValueError("Formato no soportado. Por favor sube un archivo .pdf o .txt")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {str(e)}")

def analyze_document_with_gemini(text: str, key: str, model_name: str) -> dict:
    """Envía el documento a Gemini y procesa la respuesta en formato JSON estructurado."""
    system_instruction = """
Eres un comité académico experto de alto nivel en validación de originalidad, análisis lingüístico-estilístico y verificación bibliográfica universitaria.
Tu tarea es analizar exhaustivamente el documento académico proporcionado por un estudiante o docente.

Debes responder strictly en formato JSON válido con la siguiente estructura (sin bloques markdown adicionales fuera del JSON):
{
    "porcentaje_ia": 25,
    "clasificacion_ia": "Bajo" | "Moderado" | "Alto",
    "justificacion_estilistica": "Explicación detallada sobre vocabulario, sintaxis, repetitividad o patrones robóticos...",
    "coherencia_originalidad": "Análisis profundo sobre la fluidez de las ideas, profundidad analítica y originalidad del razonamiento...",
    "revision_citas": {
        "estado": "Correcto" | "Atención Requerida" | "Citas Sospechosas",
        "detalles": "Evaluación del formato de citas (APA/IEEE/etc), mención de citas posiblemente inventadas o afirmaciones sin fuente..."
    },
    "recomendaciones": [
        "Recomendación 1 para mejorar la redacción u originalidad.",
        "Recomendación 2 sobre el manejo bibliográfico.",
        "Recomendación 3..."
    ]
}
"""

    prompt = f"""Analiza el siguiente texto académico y proporciona la evaluación de originalidad:

--- INICIO DEL TEXTO ACADÉMICO ---
{text[:15000]}
--- FIN DEL TEXTO ACADÉMICO ---
"""

    # Modelos a intentar en caso de que uno devuelva 404 (fallback automático)
    models_to_try = [model_name, "gemini-1.5-flash", "gemini-1.5-pro"]
    # Eliminar duplicados manteniendo orden
    models_to_try = list(dict.fromkeys(models_to_try))
    
    last_exception = None

    for m_name in models_to_try:
        try:
            if USE_NEW_GENAI:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=m_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                raw_text = response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
                raw_text = response.text
            
            # Limpieza básica por si incluye marcas de código markdown ```json ... ```
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            result_json = json.loads(clean_text.strip())
            return result_json

        except Exception as e:
            err_msg = str(e)
            last_exception = e
            # Si el modelo no fue encontrado (404), intentamos con el siguiente modelo en la lista
            if "404" in err_msg or "NOT_FOUND" in err_msg:
                continue
            elif "API_KEY_INVALID" in err_msg or "400" in err_msg or "403" in err_msg:
                raise ValueError("La API Key ingresada no es válida. Por favor verifica tu clave en el panel lateral.")
            elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                raise ValueError("Se excedió la cuota de la API de Gemini. Espera unos momentos antes de reintentar.")
            else:
                raise RuntimeError(f"Error durante el análisis con Gemini ({m_name}): {err_msg}")

    # Si todos fallaron
    raise RuntimeError(f"No se pudo completar la llamada a la API con los modelos disponibles: {str(last_exception)}")

# -----------------------------------------------------------------------------
# Interfaz de Usuario Principal
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📁 Carga de Documento")
    uploaded_file = st.file_uploader(
        "Arrastra o selecciona un trabajo académico (.pdf o .txt)",
        type=["pdf", "txt"],
        help="Límite recomendado: hasta 15,000 caracteres de texto."
    )
    
    extracted_text = None
    if uploaded_file:
        with st.spinner("Extrayendo texto del documento..."):
            try:
                extracted_text = extract_text_from_file(uploaded_file)
                st.success(f"Archivo `{uploaded_file.name}` procesado.", icon="✅")
                
                word_count = len(extracted_text.split())
                char_count = len(extracted_text)
                
                m1, m2 = st.columns(2)
                m1.metric("Total de Palabras", f"{word_count:,}")
                m2.metric("Caracteres", f"{char_count:,}")
                
            except Exception as e:
                st.error(f"❌ {str(e)}")

with col_right:
    st.subheader("📊 Ejecución del Análisis")
    if not api_key:
        st.info("👈 Por favor ingresa tu **Gemini API Key** en la barra lateral para continuar.", icon="💡")
    elif not uploaded_file or not extracted_text:
        st.info("👈 Sube un documento **PDF o TXT** para habilitar la evaluación.", icon="📑")
    else:
        st.write(f"El documento está listo para evaluarse con **{selected_model}**.")
        btn_analyze = st.button("🚀 Iniciar Análisis de Originalidad e IA", type="primary", use_container_width=True)
        
        if btn_analyze:
            with st.spinner(f"🔍 Analizando sintaxis, coherencia y referencias bibliográficas con {selected_model}..."):
                try:
                    analysis_result = analyze_document_with_gemini(extracted_text, api_key, selected_model)
                    st.session_state["analysis_result"] = analysis_result
                    st.session_state["analyzed_filename"] = uploaded_file.name
                    st.toast("Análisis completado exitosamente", icon="🎉")
                except Exception as e:
                    st.error(f"❌ {str(e)}")

# -----------------------------------------------------------------------------
# Despliegue de Resultados Organizaciones en Tarjetas y Tabs
# -----------------------------------------------------------------------------
if "analysis_result" in st.session_state:
    st.divider()
    res = st.session_state["analysis_result"]
    filename = st.session_state.get("analyzed_filename", "documento")
    
    st.markdown(f"## 📈 Reporte de Evaluación: `{filename}`")
    
    porcentaje_ia = res.get("porcentaje_ia", 0)
    clasificacion = res.get("clasificacion_ia", "N/A")
    citas_estado = res.get("revision_citas", {}).get("estado", "N/A")
    
    # Tarjetas Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🤖 Estimación de Contenido IA", value=f"{porcentaje_ia}%")
        st.progress(porcentaje_ia / 100.0)
        
    with col2:
        if porcentaje_ia < 30:
            st.success(f"Probabilidad de IA: **{clasificacion}** (Autoría predominantemente humana)")
        elif porcentaje_ia < 70:
            st.warning(f"Probabilidad de IA: **{clasificacion}** (Sugerida revisión docente)")
        else:
            st.error(f"Probabilidad de IA: **{clasificacion}** (Alto patrón de IA detectado)")
            
    with col3:
        if citas_estado == "Correcto":
            st.success(f"Citas Bibliográficas: **{citas_estado}**", icon="📚")
        elif citas_estado == "Atención Requerida":
            st.warning(f"Citas Bibliográficas: **{citas_estado}**", icon="⚠️")
        else:
            st.error(f"Citas Bibliográficas: **{citas_estado}**", icon="🚨")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Pestañas de Resultados
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 Detección de IA",
        "🧠 Coherencia y Originalidad",
        "📚 Citas y Referencias",
        "💡 Recomendaciones",
        "📄 Texto Extraído"
    ])
    
    with tab1:
        st.markdown("### 🔍 Justificación Estilística y Sintáctica")
        st.info(res.get("justificacion_estilistica", "Sin información."))
        
    with tab2:
        st.markdown("### 🧠 Análisis de Coherencia y Profundidad del Pensamiento")
        st.write(res.get("coherencia_originalidad", "Sin información."))
        
    with tab3:
        st.markdown("### 📚 Revisión de Fuentes y Rigor Académico")
        st.write(res.get("revision_citas", {}).get("detalles", "Sin información."))
        
    with tab4:
        st.markdown("### 💡 Recomendaciones Constructivas")
        recs = res.get("recomendaciones", [])
        if isinstance(recs, list) and recs:
            for idx, r in enumerate(recs, 1):
                st.markdown(f"**{idx}.** {r}")
        else:
            st.write(recs)
            
    with tab5:
        st.markdown("### 📄 Contenido Extraído del Documento")
        if extracted_text:
            st.text_area("Texto analizado", extracted_text, height=350)