import streamlit as st
from pypdf import PdfReader
import io

st.title("📄 PDF a Texto Converter")
st.write("Sube un archivo PDF y obtén su contenido en texto")

# Widget para subir archivos
uploaded_file = st.file_uploader("Elige un archivo PDF", type="pdf")

if uploaded_file is not None:
    try:
        # Leer el PDF usando PdfReader
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        
        # Extraer texto de cada página
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Mostrar texto extraído
        st.subheader("Texto extraído:")
        st.text_area("Contenido del PDF", text, height=400)
        
        # Botón para descargar
        st.download_button(
            label="Descargar como TXT",
            data=text,
            file_name="texto_extraido.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")