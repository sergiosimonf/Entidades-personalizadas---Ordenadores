import streamlit as st
import json
import pandas as pd

# Datos de ejemplo en tu formato (simulados)
with open('./src/output/all_products_openai.json') as f:
    laptops = json.load(f)

df = pd.DataFrame(laptops)

# Configurar página
st.set_page_config(page_title="Catálogo de Portátiles", layout="wide")
st.title("💻 Comparador de Portátiles Interactivo")

# Sidebar con filtros
st.sidebar.header("Filtros Avanzados")

# Filtro por rango de precios
precio_min, precio_max = st.sidebar.slider(
    "Rango de Precio (€)",
    min_value=float(df["price"].min()),
    max_value=float(df["price"].max()),
    value=(float(df["price"].min()), float(df["price"].max())),
    step=50.0
)

# Filtros múltiples
col1, col2 = st.sidebar.columns(2)
with col1:
    ram_seleccionada = st.selectbox(
        "RAM (GB)",
        ["Todas"] + sorted(df["ram_gb"].unique())
    )
    
    almacenamiento = st.selectbox(
        "Almacenamiento (GB)",
        ["Todas"] + sorted(df["storage"].unique())
    )

with col2:
    procesador = st.selectbox(
        "Procesador",
        ["Todos"] + sorted(df["processor"].unique())
    )
    
    pantalla = st.selectbox(
        "Tamaño pantalla (pulgadas)",
        ["Todas"] + sorted(df["inchs"].unique())
    )

# Aplicar filtros
filtered_data = df[
    (df["price"] >= precio_min) & 
    (df["price"] <= precio_max)
]

if ram_seleccionada != "Todas":
    filtered_data = filtered_data[filtered_data["ram_gb"] == ram_seleccionada]

if almacenamiento != "Todas":
    filtered_data = filtered_data[filtered_data["storage"] == almacenamiento]

if procesador != "Todos":
    filtered_data = filtered_data[filtered_data["processor"] == procesador]

if pantalla != "Todas":
    filtered_data = filtered_data[filtered_data["inchs"] == pantalla]

# Mostrar resultados
st.subheader(f"🔄 {len(filtered_data)} Modelos encontrados")

# Mostrar como tarjetas interactivas
for _, row in filtered_data.iterrows():
    with st.expander(f"{row['model']} - {row['price']:,.2f}€", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.metric("Precio", f"{row['price']:,.2f}€")
            st.write(f"**Procesador:** {row['processor']}")
            st.write(f"**Grficos:** {row['graphics']}")
            
        with col2:
            st.write(f"**RAM:** {row['ram_gb']} GB")
            st.write(f"**Almacenamiento:** {row['storage']} GB")
            st.write(f"**Pantalla:** {row['inchs']}''")
            
        max_storage = filtered_data['storage'].max()
        progress_value = row['storage'] / max_storage if max_storage != 0 else 0
        st.progress(
            min(progress_value, 1.0),  # Asegurar que nunca supere 1.0
            text=f"Capacidad relativa: {row['storage']}GB / {max_storage}GB"
        )
# Mostrar datos tabulares
st.divider()
st.subheader("📊 Vista Tabular Completa")

# Configurar columnas en la tabla
column_config = {
    "price": st.column_config.NumberColumn(
        "Precio (€)",
        format="%.2f€",
        help="Precio de venta al público"
    ),
    "ram_gb": st.column_config.NumberColumn(
        "RAM (GB)",
        help="Memoria RAM en Gigabytes"
    ),
    "storage": st.column_config.NumberColumn(
        "Almacenamiento (GB)",
        help="Capacidad de almacenamiento interno"
    )
}

st.dataframe(
    filtered_data,
    column_config=column_config,
    hide_index=True,
    use_container_width=True
)

# Mostrar estadísticas
st.divider()
st.subheader("📈 Estadísticas Clave")

cols = st.columns(3)
cols[0].metric("Precio promedio", f"{filtered_data['price'].mean():,.2f}€")
cols[1].metric("RAM promedio", f"{filtered_data['ram_gb'].mean():.1f} GB")
cols[2].metric("Almacenamiento promedio", f"{filtered_data['storage'].mean():.0f} GB")