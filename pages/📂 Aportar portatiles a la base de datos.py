import streamlit as st
from src.opeai_calls import openai_extraction
import json

# Initialize session state variables if they don't exist
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'openai_data' not in st.session_state:
    st.session_state.openai_data = ""

# Load existing data
with open('./src/output/all_products_openai.json') as f:
    laptops = json.load(f)

def upload_file():
    if not st.session_state.file_uploaded:
        # Show uploader only if no file has been uploaded
        uploaded_file = st.file_uploader("Sube tu archivo aquí", key="file_uploader")
        
        if uploaded_file is not None:
            with st.spinner("Procesando, por favor espera..."):
                # Read file content as text
                file_content = uploaded_file.getvalue()
                
                try:
                    # Try to decode if it's binary
                    if isinstance(file_content, bytes):
                        file_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    st.error("El archivo debe ser un documento de texto (TXT, PDF, etc.)")
                    return
                
                # Process with OpenAI
                openai_data = openai_extraction(file_content)
                
                if isinstance(openai_data, str) and openai_data.startswith("Error"):
                    st.error(openai_data)
                else:
                    # Store in session state
                    st.session_state.file_uploaded = True
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.openai_data = openai_data
                    st.rerun()
    else:
        # Process the uploaded file
        if st.session_state.uploaded_file is not None:
            if isinstance(st.session_state.openai_data, str) and st.session_state.openai_data.startswith("Error"):
                st.error(st.session_state.openai_data)
            else:
                st.header("Información del portátil extraída")
                
                # Display each laptop in the data - handle both list and single object cases
                laptop_data = st.session_state.openai_data if isinstance(st.session_state.openai_data, list) else [st.session_state.openai_data]
                
                for idx, laptop in enumerate(laptop_data):
                    # Create a card-like display for each laptop
                    with st.container():
                        st.subheader(f"{laptop.get('model', 'Modelo desconocido')}")
                        
                        # Create three columns for organized display
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Precio", f"{laptop.get('price', 'N/A')} €")
                            st.markdown(f"**Procesador:** {laptop.get('processor', 'N/A')}")
                            st.markdown(f"**Gráficos:** {laptop.get('graphics', 'N/A')}")
                        
                        with col2:
                            st.metric("Memoria RAM", f"{laptop.get('ram_gb', 'N/A')} GB")
                            st.markdown(f"**Almacenamiento:** {laptop.get('storage', 'N/A')} GB")
                            st.markdown(f"**Pantalla:** {laptop.get('inchs', 'N/A')} pulgadas")
                        
                        with col3:
                            # Create a simple gauge for price-to-performance ratio
                            if 'price' in laptop and 'processor' in laptop:
                                # Simple score calculation based on available data
                                score = min(100, int(laptop.get('ram_gb', 0) * 3))
                                st.metric("Rendimiento", f"{score}/100")
                                
                                # Create progress bar for visual representation
                                st.progress(score/100)
                            
                            # Additional specs or features if available
                            if 'weight' in laptop:
                                st.markdown(f"**Peso:** {laptop.get('weight')} kg")
                            if 'battery' in laptop:
                                st.markdown(f"**Batería:** {laptop.get('battery')}")
                        
                        st.markdown("---")  # Divider between laptops
                
                # Option to download JSON
                laptop_json = json.dumps(laptop_data, indent=2)
                st.download_button(
                    label="Descargar datos en formato JSON",
                    data=laptop_json,
                    file_name="laptop_datos.json",
                    mime="application/json"
                )
                
                # Correctly append each laptop individually to the laptops list
                for laptop in laptop_data:
                    laptops.append(laptop)
                
                # Save to file
                with open('./src/output/all_products_openai.json', 'w') as file:
                    json.dump(laptops, file, indent=4)
            
            # Show original content if needed
            with st.expander("Ver contenido original del archivo"):
                try:
                    content = st.session_state.uploaded_file.getvalue()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    st.text(content)
                except:
                    st.text("No se puede mostrar el contenido original")
        
        col1, col2, col3 = st.columns([3,2,3])
        with col2:
            if st.button("Subir otro archivo"):
                st.session_state.file_uploaded = False
                st.session_state.uploaded_file = None
                st.session_state.openai_data = ""
                st.rerun()

def ui():
    upload_file()

ui()