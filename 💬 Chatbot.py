import streamlit as st
from src.opeai_calls import openai_commercial

mensaje = """¡Hola! 👋 Soy tu asistente personal especializado en ayudarte a encontrar el portátil perfecto para tus necesidades. ¿Estás buscando algo potente para gaming, ligero para trabajar en movimiento, o quizás una opción equilibrada para el día a día? ¡Estoy aquí para guiarte! 

Cuéntame qué estás buscando y te recomendaré las mejores opciones. ¿Listo para encontrar tu próximo portátil? 🚀💻"""


if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
    
def upload_file():

    if not st.session_state.file_uploaded:
        # Mostrar el uploader solo si no se ha subido un archivo
        uploaded_file = st.file_uploader("Sube tu archivo aquí")

        if uploaded_file is not None:
            with st.spinner("Procesando, por favor espera..."):
                # Al subir el archivo, actualizar el estado y guardar el archivo
                st.session_state.file_uploaded = True
                st.session_state.uploaded_file = uploaded_file
                st.rerun()  # Forzar una actualización inmediata para ocultar el uploader
    else:
        # Procesar el archivo subido (ejemplo)
        if 'uploaded_file' in st.session_state:
            st.write("Contenido del archivo:")
            content = st.session_state.uploaded_file.getvalue()
            st.text(content)  # Mostrar contenido como texto plano   
        
        col1, col2, col3 = st.columns([3,2,3])
        with col2:
            if st.button("Subir otro archivo"):
                st.session_state.file_uploaded = False
                if "uploaded_file" in st.session_state:
                    del st.session_state.uploaded_file
                st.rerun()       


def chat():        
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": mensaje}]

        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            # client = OpenAI(api_key=openai_api_key)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            msg = openai_commercial(prompt)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)


        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": mensaje}]

def ui():
    # UI del sistema
    st.title("💬 Chatbot")
    # upload_file()
    chat()
        
    
ui()