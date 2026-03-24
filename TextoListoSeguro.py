import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="TextoListo", page_icon="📝", layout="centered")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.error("⚠️ Falta la llave de Google en los Secrets de Streamlit.")
    st.stop()

st.markdown("""
    <style>
    .stButton>button { height: 90px; font-size: 24px !important; font-weight: bold; border-radius: 18px; }
    .stTextArea textarea { font-size: 24px !important; line-height: 1.6; }
    p, div, label { font-size: 22px !important; }
    h3 { font-size: 28px !important; margin-top: 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SISTEMA DE MEMORIA
# ==========================================
if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""
if "historial" not in st.session_state:
    st.session_state.historial = []

def guardar_pasado():
    st.session_state.historial.append(st.session_state.texto_acumulado)

def agregar_texto(texto_nuevo):
    guardar_pasado()
    if st.session_state.texto_acumulado == "":
        st.session_state.texto_acumulado = texto_nuevo
    else:
        st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"

def guardar_edicion_manual():
    st.session_state.texto_acumulado = st.session_state.editor_texto

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL
# ==========================================
def procesar_imagen(imagen_file):
    img = Image.open(imagen_file)
    prompt = """Extrae todo el texto de esta imagen de forma clara y limpia. Corrige ortografía. 
    SI ENCUENTRAS TABLAS O CIFRAS: Conviértelas en una lista fácil de leer renglón por renglón.
    Devuelve SOLO el texto, sin saludos ni explicaciones."""
    respuesta = model.generate_content([prompt, img])
    return respuesta.text

def procesar_audio(audio_file):
    audio_data = {"mime_type": audio_file.type, "data": audio_file.getvalue()}
    prompt = "Transcribe este audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto, sin saludos."
    respuesta = model.generate_content([prompt, audio_data])
    return respuesta.text

def procesar_pdf(pdf_file):
    pdf_data = {"mime_type": "application/pdf", "data": pdf_file.getvalue()}
    prompt = """Lee este PDF. Extrae el texto de forma clara. 
    SI ENCUENTRAS TABLAS O CIFRAS: Conviértelas en una lista fácil de leer renglón por renglón.
    Devuelve SOLO el texto, sin saludos."""
    respuesta = model.generate_content([prompt, pdf_data])
    return respuesta.text

def generar_voz(texto):
    tts = gTTS(text=texto, lang='es', tld='com.mx')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

# ==========================================
# INTERFAZ PARA EL ADULTO MAYOR
# ==========================================
st.title("📝 TextoListo")
st.write("Convierte fotos, documentos o tu voz en texto limpio.")
st.info("🔒 **Consejo:** No tomes fotos de tarjetas, contraseñas o datos del banco.")

# --- NUEVO: CONSENTIMIENTO SIMPLIFICADO Y LEGAL (Paso 1) ---
st.markdown("### 🛑 Paso 1: Permiso de Seguridad")
acepto_privacidad = st.checkbox("✅ Acepto que la computadora escuche mi voz o lea mis fotos de forma segura para ayudarme.")

with st.expander("👀 Ver detalles de privacidad (Para familiares o asesores)"):
    st.markdown("""
    **Aviso de Privacidad Simplificado (LFPDPPP):** Esta herramienta tecnológica independiente no guarda sus datos, fotografías ni audios de voz en bases de datos. Todo se borra de manera automática al cerrar la página o presionar el botón de limpiar (Cero Persistencia). 
    
    Para poder transcribir o leer sus documentos, el sistema transfiere temporalmente y de forma cifrada las imágenes o audios a los sistemas de Inteligencia Artificial. Al marcar la casilla de aceptación, usted consiente de manera expresa este procesamiento temporal para su asistencia personal.
    """)
st.divider()

# --- OPCIÓN 1: GRABAR VOZ (Paso 2) ---
st.subheader("🎙️ Paso 2: Dictar un mensaje")
audio_grabado = st.audio_input("Toca el micrófono para hablar")
if audio_grabado:
    if not acepto_privacidad:
        st.error("🚨 **ATENCIÓN:** Por favor, toca la casilla de 'Acepto' arriba en el Paso 1 para poder escucharte.")
    else:
        with st.spinner("⏳ Escuchando tu mensaje..."):
            texto = procesar_audio(audio_grabado)
            agregar_texto(texto)
            st.success("¡Mensaje agregado!")

st.divider()

# --- OPCIÓN 2: LA SOLUCIÓN NATIVA PARA CÁMARA Y ARCHIVOS (Paso 3) ---
st.subheader("📷 Paso 3: Tomar Foto o Subir Documento")
st.write("💡 Toca el botón de abajo. **Tu celular te preguntará si quieres abrir tu Cámara** o elegir una foto de tu galería.")

archivos_subidos = st.file_uploader(
    "Toca aquí para abrir cámara o archivos:", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'opus'],
    accept_multiple_files=True 
)

if archivos_subidos and st.button("✅ PROCESAR DOCUMENTOS / FOTOS", type="secondary", use_container_width=True):
    if not acepto_privacidad:
        st.error("🚨 **ATENCIÓN:** Por favor, toca la casilla de 'Acepto' arriba en el Paso 1 para poder leer tus fotos o documentos.")
    else:
        with st.spinner("⏳ Leyendo... no cierres la pantalla..."):
            textos_nuevos = []
            for archivo in archivos_subidos:
                tipo = archivo.type
                if tipo.startswith("image/"): 
                    textos_nuevos.append(procesar_imagen(archivo))
                elif tipo.startswith("audio/") or tipo in ["audio/ogg", "audio/opus"]: 
                    textos_nuevos.append(procesar_audio(archivo))
                elif tipo == "application/pdf": 
                    textos_nuevos.append(procesar_pdf(archivo))
            
            if textos_nuevos:
                texto_unido = "\n\n".join(textos_nuevos)
                agregar_texto(texto_unido)
                st.success("¡Texto extraído con éxito!")

# ==========================================
# REVISIÓN Y ENVÍO
# ==========================================
if st.session_state.texto_acumulado.strip():
    st.divider()
    st.subheader("👀 Paso 4: Revisa tu mensaje")
    
    if len(st.session_state.historial) > 0:
        if st.button("↩️ Me equivoqué, borrar lo último que agregué"):
            st.session_state.texto_acumulado = st.session_state.historial.pop()
            st.rerun()

    st.write("Toca el cuadro blanco si necesitas corregir alguna letra.")
    
    texto_final = st.text_area("Mensaje listo:", value=st.session_state.texto_acumulado.strip(), height=300, key="editor_texto", on_change=guardar_edicion_manual)
    
    if st.button("🔊 Escuchar en voz alta"):
        st.audio(generar_voz(texto_final), format='audio/mp3', autoplay=True)

    st.divider()
    
    mensaje_wpp = urllib.parse.quote(f"Hola, por favor ayúdame a pasar este texto a un Word e imprimirlo:\n\n{texto_final}")
    enlace_wpp = f"https://api.whatsapp.com/send?text={mensaje_wpp}"
    
    st.link_button("✅ ENVIAR POR WHATSAPP", enlace_wpp, type="primary", use_container_width=True)

    st.write("---")
    if st.button("🗑️ Borrar TODO y empezar de cero"):
        st.session_state.texto_acumulado = ""
        st.session_state.historial = []
        st.rerun()
