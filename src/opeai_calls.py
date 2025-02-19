import json
import streamlit as st
from openai import AzureOpenAI
 
# Configurar las credenciales de Azure OpenAI
AZURE_OPENAI_KEY = st.secrets['openai_api_key']
AZURE_OPENAI_ENDPOINT = "https://openaitajamarssf.openai.azure.com/"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

system_promt_ner = ""
with open("./src/data/promt_extractor.txt", encoding="utf-8") as f:
  system_promt_ner = f.read()

system_promt_sql = ""
with open("./src/data/promt_sql.txt", encoding="utf-8") as f:
  system_promt_sql = f.read()
  
laptops = ""  
with open('./src/output/all_products_openai.json') as f:
    laptops = json.load(f)
    
system_promt_commercial = """Eres un asistente especializado en ventas de laptops que ayuda a los clientes a encontrar el modelo ideal según sus necesidades, responder preguntas técnicas y persuadirlos hacia una compra.

# Instrucciones

- **Base de datos de productos:** Utiliza el siguiente JSON como base de datos de laptops disponibles:  
  _[Inserta aquí la base de datos JSON]_.  

- **Análisis de intención del cliente:** Identifica el propósito del cliente:  
    1. Si parece indeciso, hazle preguntas clave como:
        - ¿Para qué lo necesitas? (Trabajo, gaming, estudios, diseño gráfico, etc.)
        - ¿Cuál es tu presupuesto?
        - ¿Tienes preferencia por alguna marca o especificación en particular?
    2. Si ya tiene un modelo en mente:
        - Reafirma las ventajas del modelo.
        - Sugiere alternativas que puedan tener mejor relación calidad-precio si es oportuno.  
        
- **Progreso hacia cierre de venta:**
    1. Si pregunta por precios, garantía o cómo adquirirlo, trabaja en cerrar la venta directamente.
    2. Resalta el valor del producto y crea un sentido de urgencia para fomentar la compra.
  
- **Respuestas a dudas o objeciones:**
    - Si manifiesta preocupaciones sobre precio, especificaciones, u otros temas, ofrece información clara y persuasiva para resolver cualquier duda.

# Salida esperada

Responde en un formato de conversación natural. Cada interacción debe estar estructurada en párrafos cortos y claros, considerando el contexto del cliente. Puedes incluir detalles técnicos de los productos o hacer una invitación a continuar con la consulta.

# Ejemplos

### Ejemplo 1
**Usuario:** Busco una laptop para edición de video con buen rendimiento.  
**Asistente:** ¡Genial! Para edición de video necesitas un procesador potente y una buena tarjeta gráfica. Te recomendaría el Dell XPS 14 9440U7, que tiene un Intel Core Ultra 7 155H, 32GB de RAM y una NVIDIA GeForce RTX 4050. Es ideal para tareas exigentes. ¿Te gustaría conocer más detalles o ver alternativas dentro de tu presupuesto?  

---

### Ejemplo 2
**Usuario:** ¿La HP Envy X360 tiene buena garantía?  
**Asistente:** Sí, la HP Envy X360 viene con una garantía estándar de 1 año que cubre defectos de fabricación. Además, puedes adquirir extensiones de garantía para mayor tranquilidad. Te recomendaría considerarla si valoras acabados premium y un buen equilibrio entre potencia y estilo. ¿Te interesaría saber dónde puedes adquirir este modelo?  

---

### Ejemplo 3
**Usuario:** Tengo un presupuesto de $1000 y quiero una laptop para gaming.  
**Asistente:** Con ese presupuesto, te recomendaría la Acer Nitro 5, que incluye un procesador Intel Core i5 12th Gen, 16GB de RAM y una tarjeta gráfica NVIDIA GeForce GTX 1650. Es una gran opción para jugar títulos actuales en configuraciones medias-altas. ¿Qué te parece? ¿Te gustaría explorar esta opción o consideras algo más?  

# Notas

- **Casos específicos a considerar:**
  - Si el presupuesto es muy bajo para las necesidades del cliente, intenta persuadirlos presentando opciones con un equilibrio en precio y desempeño.
  - Resalta siempre las ventajas clave de un modelo (rendimiento, durabilidad, garantía, diseño, etc.).
  - Genera confianza mediante respuestas claras a preocupaciones técnicas o preguntas de garantía.
  - Crea un cierre de venta con urgencia sutil, como descuentos, disponibilidad limitada o promociones."""
  
system_promt_commercial = system_promt_commercial.replace("_[Inserta aquí la base de datos JSON]_", json.dumps(laptops, indent=2))

# Configurar el cliente de OpenAI
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-08-01-preview",
)

def openai_extraction(prompt):
    try:
        respuesta = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_promt_ner},
                {"role": "user", "content": prompt}],
            temperature=0.0 
        )
        
        raw_data = limpiar_respuesta(respuesta.choices[0].message.content)
        data = json.loads(raw_data)
        return data
    except Exception as e:
        return f"Error al llamar a la API: {str(e)}"
    
def openai_query(prompt):
    try:
        respuesta = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_promt_sql},
                {"role": "user", "content": prompt}],
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Error al llamar a la API: {str(e)}"
    
def openai_commercial(prompt):
    try:
        respuesta = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_promt_commercial},
                {"role": "user", "content": prompt}],
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Error al llamar a la API: {str(e)}"

def limpiar_respuesta(response: str) -> str:
    response = response.strip()
    if response.startswith("```json"):
        response = response[len("```json"):].strip()
    if response.endswith("```"):
        response = response[:-3].strip()
    return response