import streamlit as st
import requests

st.title("🔠 Traductor de documentos de Azure")

# Mapeo de nombres de idiomas a sus códigos
lang_map = {
    "Inglés": "en",
    "Francés": "fr",
    "Chino": "zh",
    "Ruso": "ru"
}

# Seleccionar idioma de destino
idioma_destino = st.selectbox("Selecciona el idioma de destino:", list(lang_map.keys()))

# Configuración de Azure (se arma el endpoint dinámicamente según el idioma elegido)
target_lang_code = lang_map[idioma_destino]
AZURE_ENDPOINT = f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from=es&to={target_lang_code}"
HEADERS = {
    'Ocp-Apim-Subscription-Key': st.secrets['azure_translator_key'],
    'Ocp-Apim-Subscription-Region': 'eastus',
    'Content-Type': 'application/json'
}

def calcular_altura_area_texto(texto, altura_linea=20, altura_min=68, altura_max=300):
    num_lineas = texto.count("\n") + 1  # Sumar 1 para la última línea (aunque no tenga salto)
    altura_ideal = num_lineas * altura_linea
    return min(max(altura_ideal, altura_min), altura_max)

# Subir archivo de texto
uploaded_file = st.file_uploader("Sube un archivo de texto (.txt)", type=['txt'])

if uploaded_file is not None:
    # Leer contenido del archivo
    text_content = uploaded_file.read().decode('utf-8')
    
    # Guardar en sesión
    st.session_state['original'] = {
        'nombre': uploaded_file.name,
        'contenido': text_content
    }
    st.toast('¡Archivo subido correctamente!', icon='✅')
    st.subheader("Texto original:")
    
    # Calcular altura del área de texto en función del contenido
    altura_texto = calcular_altura_area_texto(text_content)
    st.text_area("", value=text_content, height=altura_texto, disabled=True)

# Botón de traducción
if 'original' in st.session_state and st.button(f"Traducir a {idioma_destino}"):
    try:
        # Construir el cuerpo de la petición
        body = [{'Text': st.session_state['original']['contenido']}]
        
        # Llamada a la API de Azure
        response = requests.post(AZURE_ENDPOINT, headers=HEADERS, json=body)
        response.raise_for_status()
        
        # Procesar la respuesta
        translated_text = response.json()[0]['translations'][0]['text']
        
        # Guardar traducción en la sesión
        st.session_state['traduccion'] = {
            'nombre': f"TRADUCIDO_{st.session_state['original']['nombre']}",
            'contenido': translated_text
        }
        
        st.subheader("Texto traducido:")
        altura_texto_trad = calcular_altura_area_texto(translated_text)
        st.text_area("", value=translated_text, height=altura_texto_trad, disabled=True)
        st.toast("¡Traducción completada!", icon='🚀')
        
    except Exception as e:
        st.toast(f"Error en la traducción: {str(e)}", icon='❌')

# Descargar traducción
if 'traduccion' in st.session_state:
    st.download_button(
        label="⬇️ Descargar Traducción",
        data=st.session_state['traduccion']['contenido'].encode('utf-8'),
        file_name=st.session_state['traduccion']['nombre'],
        mime='text/plain'
    )