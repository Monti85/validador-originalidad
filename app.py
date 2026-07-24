import streamlit as st
import pypdf
import json
import time
from google import genai
from google.genai import types

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
        help="Ingresa tu clave de API de Google Gemini (generada en AI Studio).",
        placeholder="AIzaSy..."
    )
    
    if api_key:
        st.success("🔑 API Key ingresada", icon="✅")
    else:
        st.warning("⚠️ Ingresa tu API Key para comenzar", icon="🔑")
        st.markdown("[¿Cómo obtener tu API Key de Gemini gratis?](https://aistudio.google.com/app/apikey)")
        
    st.divider()
    st.markdown("### 🤖 Modelo de IA")
    selected_model = st.selectbox(
        "Selecciona el modelo Gemini:",
        ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-pro"],
        index=0,
        help="gemini-flash-latest es el modelo recomendado y con cuota disponible. Cada modelo tiene su propio límite diario independiente."
    )
    
    st.divider()
    st.markdown("### ℹ️ Especificaciones")
    st.info(f"**Modelo activo:** `{selected_model}`\n\n**Modo:** Documento completo (hasta 120,000 caracteres)\n\n**Formatos:** PDF y TXT")
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

def prepare_full_text(text: str, max_chars: int = 120000) -> tuple[str, bool]:
    """Devuelve el texto completo del documento. Si excede el límite del modelo, lo trunca con aviso."""
    if len(text) <= max_chars:
        return text, False  # texto completo, sin truncar
    # Solo truncar si supera el límite seguro del modelo
    truncated = text[:max_chars]
    return truncated, True  # texto truncado, con aviso

def _call_gemini(client, model_name: str, prompt: str, system_instruction: str) -> dict:
    """Realiza una llamada a Gemini y parsea el JSON de respuesta."""
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    raw = response.text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)

def analyze_document_with_gemini(text: str, key: str, model_name: str) -> dict:
    """Envía el documento completo a Gemini con reintento automático y fallback de modelos."""
    client = genai.Client(api_key=key.strip())
    full_text, was_truncated = prepare_full_text(text, max_chars=120000)

    if was_truncated:
        st.warning(
            f"⚠️ El documento tiene {len(text):,} caracteres. Se analizaron los primeros 120,000 "
            "para no superar el límite del modelo. Los resultados son representativos del documento completo."
        )

    system_instruction = (
        "Eres un experto académico en detección de IA y validación bibliográfica. "
        "Analiza el texto y responde SOLO con un JSON válido con estas claves exactas: "
        "porcentaje_ia (int 0-100), clasificacion_ia (\"Bajo\"|\"Moderado\"|\"Alto\"), "
        "justificacion_estilistica (str), coherencia_originalidad (str), "
        "revision_citas ({estado: str, detalles: str}), recomendaciones (list[str])."
    )
    prompt = f"Analiza este trabajo académico completo:\n\n{full_text}"

    # Cadena de fallback: cada modelo tiene su propia cuota diaria independiente
    fallback_chain = [model_name]
    for m in ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"]:
        if m not in fallback_chain:
            fallback_chain.append(m)

    last_error = None
    for attempt_model in fallback_chain:
        try:
            return _call_gemini(client, attempt_model, prompt, system_instruction)
        except Exception as e:
            err_str = str(e)
            is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
            is_not_found = "404" in err_str or "NOT_FOUND" in err_str

            if not is_quota and not is_not_found:
                # Error definitivo (auth, parsing, etc.) — no tiene sentido reintentar
                if "API_KEY_INVALID" in err_str or ("INVALID_ARGUMENT" in err_str and "key" in err_str.lower()):
                    raise ValueError("❌ La API Key ingresada no es válida. Por favor verifica tu clave en la barra lateral.")
                raise RuntimeError(f"Error en Gemini ({attempt_model}): {err_str}")

            last_error = err_str

            if is_quota:
                # Esperamos y reintentamos con el MISMO modelo antes de pasar al siguiente
                wait_seconds = 62
                placeholder = st.empty()
                placeholder.warning(f"⏳ Cuota alcanzada en `{attempt_model}`. Esperando {wait_seconds}s antes de reintentar...")
                for remaining in range(wait_seconds, 0, -1):
                    placeholder.warning(f"⏳ Cuota alcanzada en `{attempt_model}`. Reintentando en **{remaining}s**...")
                    time.sleep(1)
                placeholder.empty()
                try:
                    return _call_gemini(client, attempt_model, prompt, system_instruction)
                except Exception:
                    pass  # Sigue al siguiente modelo del fallback
            # Si es NOT_FOUND, pasa directo al siguiente modelo

    raise ValueError(
        f"⚠️ Todos los modelos disponibles alcanzaron su límite de cuota.\n"
        "**Opciones:**\n"
        "1. Espera 1-2 minutos y vuelve a intentarlo.\n"
        "2. Genera una nueva API Key en [Google AI Studio](https://aistudio.google.com/app/apikey).\n"
        "3. Si el problema persiste, la clave puede tener restricciones de dominio institucional."
    )

# -----------------------------------------------------------------------------
# Interfaz de Usuario Principal
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📁 Carga de Documento")
    uploaded_file = st.file_uploader(
        "Arrastra o selecciona un trabajo académico (.pdf o .txt)",
        type=["pdf", "txt"],
        help="Extrae el texto del documento para análisis de originalidad."
    )
    
    # Opción de texto de prueba rápido
    use_sample_doc = st.checkbox("🧪 Usar texto de ejemplo (para prueba rápida)", value=False)
    
    extracted_text = None
    if use_sample_doc:
        extracted_text = """El impacto de la inteligencia artificial en la educación superior ha generado importantes debates éticos e institucionales. Según García (2023), la adopción de modelos generativos de lenguaje en entornos universitarios requiere un marco normativo claro. Sin embargo, estudios recientes (Smith et al., 2024) sugieren que más del 65% de los estudiantes utiliza herramientas de IA para sintetizar información académica.

En la Universidad Tecnológica (UTEC), la implementación de tecnologías emergentes busca potenciar el pensamiento crítico sin reemplazar la autoría genuina. Es fundamental distinguir entre la asistencia tecnológica responsable y la delegación completa del razonamiento analítico. La bibliografía consultada demuestra que los patrones sintácticos reiterativos y la falta de variabilidad estilística son marcas distintivas de los borradores sintéticos."""
        st.info("📄 Documento de ejemplo cargado (3 párrafos académicos con citas APA).")
        
    elif uploaded_file:
        with st.spinner("Extrayendo texto del documento..."):
            try:
                extracted_text = extract_text_from_file(uploaded_file)
                st.success(f"Archivo `{uploaded_file.name}` procesado correctamente.", icon="✅")
                
                word_count = len(extracted_text.split())
                char_count = len(extracted_text)
                
                m1, m2 = st.columns(2)
                m1.metric("Total de Palabras", f"{word_count:,}")
                m2.metric("Caracteres Extraídos", f"{char_count:,}")
                
            except Exception as e:
                st.error(f"❌ {str(e)}")

with col_right:
    st.subheader("📊 Ejecución del Análisis")
    if not api_key:
        st.info("👈 Por favor ingresa tu **Gemini API Key** en la barra lateral para continuar.", icon="💡")
    elif not extracted_text:
        st.info("👈 Sube un documento **PDF o TXT** o marca la casilla de prueba rápida.", icon="📑")
    else:
        st.write(f"El texto está listo para evaluarse con el modelo **{selected_model}**.")
        btn_analyze = st.button("🚀 Iniciar Análisis de Originalidad e IA", type="primary", use_container_width=True)
        
        if btn_analyze:
            with st.spinner(f"🔍 Analizando patrones de IA, coherencia y citas bibliográficas con {selected_model}..."):
                try:
                    analysis_result = analyze_document_with_gemini(extracted_text, api_key, selected_model)
                    st.session_state["analysis_result"] = analysis_result
                    st.session_state["analyzed_filename"] = uploaded_file.name if uploaded_file else "Ejemplo_Academico.txt"
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