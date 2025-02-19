import os,re,json,duckdb,requests,time
from opeai_calls import openai_extraction

# Conectar a DuckDB (en memoria o archivo)
conn = duckdb.connect(':memory:')
   
def parse_file(text):
    data = {}

    # Extraer el código del producto - Mejorado para manejar diferentes formatos
    code_match = re.search(r'(?:Código|Code)\s*:?\s*([\w\d-]+)', text, re.IGNORECASE)
    data["code"] = code_match.group(1) if code_match else None

    # Extraer el nombre o modelo del equipo - Patrón más inclusivo
    model_match = re.search(r'^.*(?:Chromebook|Inspiron|Latitude|XPS|Surface|ThinkPad|IdeaPad|gram|GALAXY|HP|Lenovo)\s+[^\n]+', text, re.MULTILINE)
    data["model"] = model_match.group().strip() if model_match else None

    # Extraer el precio - Mejorado para manejar diferentes separadores decimales
    price_match = re.search(r'([\d.,]+)\s*€', text)
    if price_match:
        price = price_match.group(1).replace(',', '.')
        # Asegurar que solo hay un punto decimal
        if price.count('.') > 1:
            parts = price.split('.')
            price = parts[0] + '.' + ''.join(parts[1:])
        data["price"] = price
    else:
        data["price"] = None

    # Extraer información del procesador - Patrón más robusto
    processor_patterns = [
        r'Procesador(?:[:\s]+)((?:Intel|AMD|Apple)(?:[^.]*?)(?=\.|$))',
        r'(?:Intel|AMD|Apple)(?:®|\s)?(?:Core|Ryzen|M)\s+(?:[\w-]+\s*)+(?:\d+[A-Z]\d+[A-Z0-9]+|\d+[A-Z]{0,1}\s*(?:Gen|generación|generation)?)',
    ]
    
    for pattern in processor_patterns:
        processor_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if processor_match:
            data["processor"] = processor_match.group(1).strip() if len(processor_match.groups()) > 0 else processor_match.group(0).strip()
            break
    else:
        data["processor"] = None

    # Extraer la memoria RAM - Mejorado para capturar más formatos
    ram_patterns = [
        r'RAM(?:[:\s]*)([\d]+\s*GB)',
        r'(\d+)\s*GB\s+(?:Soldered\s+)?(?:DDR\d+|LPDDR\d+)',
        r'Memoria(?:[:\s]*)([\d]+\s*GB)',
    ]
    
    for pattern in ram_patterns:
        ram_match = re.search(pattern, text, re.IGNORECASE)
        if ram_match:
            data["ram"] = ram_match.group(1).strip()
            data["max_ram"] = ram_match.group(1).strip()
            break
    else:
        data["ram"] = None
        data["max_ram"] = None

    # Extraer el almacenamiento - Mejorado para capturar más tipos y formatos
    storage_patterns = [
        r'(\d+\s*(?:GB|TB))(?:\s+(?:SSD|eMMC|HDD))',
        r'(?:SSD|eMMC|HDD)(?:[:\s]*)([\d]+\s*(?:GB|TB))',
        r'Disco duro(?:[:\s]*)([\d.]+\s*(?:GB|TB))',
    ]
    
    for pattern in storage_patterns:
        storage_match = re.search(pattern, text, re.IGNORECASE)
        if storage_match:
            data["storage"] = storage_match.group(1).strip()
            break
    else:
        data["storage"] = None

    # Extraer información de la pantalla - Mejorado para capturar más formatos
    display_patterns = [
        r'(\d+(?:\.\d+)?)["\″](?:\s*(?:OLED|IPS|Touch|Display|Screen|Monitor))?',
        r'(?:Tamaño\s*pantalla|Pantalla)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:["\″]|\'\'|pulgadas|inches)',
        r'(\d+(?:[.,]\d+)?)\s*(?:pulgadas|inches|["\″]|\'\')',
        r'(?:display|screen|monitor)\s*size\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:["\″]|\'\'|pulgadas|inches)'
    ]
        
    for pattern in display_patterns:
        display_match = re.search(pattern, text, re.IGNORECASE)
        if display_match:
            data["display_size"] = display_match.group(1).strip()
            break
    else:
        data["display_size"] = None

    # Extraer la tarjeta gráfica - Mejorado para capturar más modelos
    graphics_patterns = [
        r'(?:Gráfica|Graphics)(?:[:\s]*)((?:NVIDIA|Intel|AMD|Apple)(?:[^.\n]+)(?=\.|$))',
        r'(?:NVIDIA|Intel|AMD)\s+(?:GeForce|Iris|Radeon|UHD|Arc)\s+(?:[^\n]+?)(?=\s+Memoria|\s+Memory|$)',
    ]
    
    for pattern in graphics_patterns:
        graphics_match = re.search(pattern, text, re.IGNORECASE)
        if graphics_match:
            data["graphics"] = graphics_match.group(1).strip() if len(graphics_match.groups()) > 0 else graphics_match.group(0).strip()
            break
    else:
        data["graphics"] = None

    return data

def test_database():
        # Consulta 1: Productos más caros con componentes clave
    print("\nTop 5 productos más caros:")
    top_query = """
        SELECT code, model, price, ram_gb, storage 
        FROM products 
        ORDER BY price DESC 
        LIMIT 5
    """
    for row in conn.execute(top_query).fetchall():
        print(f"🖥️  {row[1]} | 💵 €{row[2]:,.2f} | 🧠 {row[3]}GB | 💾 {row[4] or 'N/A'}")
    
    # Consulta 2 modificada (manejo de nulos en promedio)
    print("\nPromedio de RAM por marca:")
    brand_analysis = """
        SELECT 
            CASE
                WHEN model LIKE '%Dell%' THEN 'Dell'
                WHEN model LIKE '%Lenovo%' THEN 'Lenovo'
                WHEN model LIKE '%LG%' THEN 'LG'
                ELSE 'Otras marcas'
            END AS marca,
            ROUND(AVG(ram_gb), 1) AS ram_promedio,
            COUNT(*) AS cantidad
        FROM products
        GROUP BY marca
        ORDER BY ram_promedio DESC
    """
    for row in conn.execute(brand_analysis).fetchall():
        print(f"🏷️  {row[0]:<12} | 📊 {row[1]:.1f}GB promedio | 📦 {row[2]} unidades")
        
    # Consulta 3: Relación precio-rendimiento corregida
    print("\nMejor relación precio-rendimiento (€ por GB de RAM):")
    value_query = """
        SELECT code, model, 
            (price/ram_gb) AS precio_por_ram,
            graphics
        FROM products
        WHERE 
            ram_gb > 0 AND
            price IS NOT NULL
        ORDER BY precio_por_ram ASC
        LIMIT 5
    """
    for row in conn.execute(value_query).fetchall():
        precio_por_ram = row[2]
        graphics_info = row[3][:25].replace('\n', ' ') + "..." if row[3] else "Sin detalles gráficos"
        print(f"""🏷️  {row[0]} - {row[1] or 'Modelo genérico'} | 💵 €{precio_por_ram:,.2f} por GB RAM | 🎮 {graphics_info}""")
    
    # Define your query
    value_query = """SELECT code, model, price, processor, ram_gb, storage, graphics, file_name FROM products WHERE processor ILIKE '%Intel%';"""

    # Execute the query and fetch results
    query = conn.execute(value_query)
    df = query.fetchdf()

    # Output the results
    print(df)

def db_regex():
    try:
        # Crear tabla con conversión de precio a numérico
        conn.execute("""
            CREATE TABLE products AS
            SELECT 
                code,
                model,
                TRY_CAST(REPLACE(price, '.', '') AS DECIMAL(10,2)) AS price,
                processor,
                COALESCE(
                    TRY_CAST(REGEXP_REPLACE(ram, '[^0-9]', '') AS INTEGER),
                    0
                ) AS ram_gb,
                storage,
                graphics,
                file_name
            FROM read_json_auto('./output/all_products.json')
        """)
        
        # test_database()
            
        schema = conn.execute("DESCRIBE products").fetchdf()
        print(schema)
        
    finally:
        conn.close()
        
def db_openai():
    data_path = "./src/output/all_products_openai.json"
    conn = duckdb.connect(database=":memory:")  # Conectar a la base de datos en memoria

    # try:
    # Crear la tabla con los datos procesados
    conn.execute("""
        CREATE TABLE products AS
        SELECT 
            model,
            CAST(price AS DECIMAL(10,2)) AS price,
            processor,
            COALESCE(TRY_CAST(ram_gb AS INTEGER), 0) AS ram_gb,
            storage,
            graphics,
            inchs
        FROM read_json_auto('./src/output/all_products_openai.json')
    """)

    # Mostrar el esquema de la tabla
    schema = conn.execute("DESCRIBE products").fetchdf()
    print(schema)
    
    run_openai_db_queries(conn)

    # finally:
        # conn.close()        
        
def run_openai_db_queries(conn):
    queries = {
        "1. Listar todos los productos": "SELECT * FROM products;",
        "2. Contar la cantidad total de productos": "SELECT COUNT(*) AS total_products FROM products;",
        "3. Estadísticas básicas de precios": """
            SELECT 
                MIN(price) AS min_price,
                MAX(price) AS max_price,
                AVG(price) AS avg_price
            FROM products;
        """,
        "4. Agrupar productos por procesador": """
            SELECT 
                processor,
                COUNT(*) AS total,
                AVG(price) AS avg_price
            FROM products
            GROUP BY processor
            ORDER BY total DESC;
        """,
        "5. Productos con precio mayor que el precio promedio": """
            SELECT *
            FROM products
            WHERE price > (SELECT AVG(price) FROM products);
        """,
        "6. Los 10 productos más caros": """
            SELECT *
            FROM products
            ORDER BY price DESC
            LIMIT 10;
        """,
        "7. Productos con al menos 8 GB de RAM": """
            SELECT *
            FROM products
            WHERE ram_gb >= 8;
        """,
        "8. Productos con pantalla de 15 pulgadas o más": """
            SELECT *
            FROM products
            WHERE inchs >= 15;
        """
    }

    for titulo, query in queries.items():
        print(f"\n--- {titulo} ---")
        try:
            resultado = conn.execute(query).fetchall()
            for fila in resultado:
                print(fila)
        except Exception as e:
            print("Error en la consulta:", e)

def process_call(result):
    raw_data = result['tasks']['items'][0]['results']['documents'][0]['entities']
    
    def get_best_entity_by_category(entities, category):
        matches = [entity for entity in entities if entity['category'] == category]
        if not matches:
            return None
        # Ordenar por confidence score y devolver el texto del más alto
        best_match = max(matches, key=lambda x: x['confidenceScore'])
        return best_match['text']
    
    ner_data = {
        "precio": get_best_entity_by_category(raw_data, "precio"),
        "procesador": get_best_entity_by_category(raw_data, "modelo procesador"),
        "grafica": get_best_entity_by_category(raw_data, "modelo de grafica"),
        "ram": get_best_entity_by_category(raw_data, "ram"),
        "ram_maxima": get_best_entity_by_category(raw_data, "ram maxima"),
    }
    
    return ner_data 

def azure_ner_response(document):
    reqUrl = "https://languajestudiosergiosimon.cognitiveservices.azure.com/language/analyze-text/jobs?api-version=2022-10-01-preview"

    headersList = {
        "Ocp-Apim-Subscription-Key": "2kkTaqCbWNA2Kmpjiz7CHMz4Sa6FPRxtQapHtLPDBhnwOKbwDhptJQQJ99BBACYeBjFXJ3w3AAAaACOGszSy",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "tasks": [
            {
                "kind": "CustomEntityRecognition",
                "parameters": {
                    "projectName": "Computer-Recognize",
                    "deploymentName": "Model",
                    "stringIndexType": "TextElement_v8"
                }
            }
        ],
        "displayName": "CustomTextPortal_CustomEntityRecognition",
        "analysisInput": {
            "documents": [
                {
                    "id": "document_CustomEntityRecognition",
                    "text": document,
                    "language": "es"
                }
            ]
        }
    })

    # Realizar la solicitud POST
    response = requests.post(reqUrl, data=payload, headers=headersList)

    # Obtener la URL de seguimiento de la operación
    reqUrl = response.headers["operation-location"]

    # Esperar hasta que el trabajo esté terminado
    while True:
        # Realizar la solicitud GET para verificar el estado
        response = requests.get(reqUrl, headers=headersList)
        
        # Verificar el estado del trabajo
        result = response.json()
        status = result.get("status", "")
        data = {}
        
        if status == "succeeded":
            # print("La tarea se completó con éxito.")
            print("Resultados: ", result)  # Aquí puedes procesar los resultados como necesites
            with open('output/ner_output.json', "w", encoding="utf-8") as json_file:
                json.dump(result, json_file, indent=4, ensure_ascii=False)
            data = process_call(result) 
            break
        elif status == "failed":
            print("La tarea ha fallado.")
            break
        else:
            print("Esperando a que se complete la tarea...")
            time.sleep(1)  # Esperar 10 segundos antes de volver a comprobar el estado
    
    return data

def azure_ner_call():
    folder_path = "./pdf_to_text/"
    data = {}
    
    for root, dirs, files in os.walk(folder_path):  
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(file_path)
                content = ""
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                result = azure_ner_response(content)
                data.update({file: result})

    with open("output/all_products_ner.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

def run_parse():
    folder_path = "./src/data/pdf_to_text/"
    all_data = []
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        if os.path.isfile(file_path) and file.endswith(".txt"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    extracted = parse_file(content)
                    extracted["file_name"] = file
                    all_data.append(extracted)
            except Exception as e:
                print(f"Error al leer {file_path}: {e}")
    
    # Guardar resultados
    with open("./src/output/all_products_regex.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, indent=4, ensure_ascii=False)

def opeai_call():
    folder_path = "./src/data/pdf_to_text/"
    data = []
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        if os.path.isfile(file_path) and file.endswith(".txt"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    result = openai_extraction(content)
                    print(result)
                    data.extend(result)
            except Exception as e:
                print(f"Error al leer {file_path}: {e}")
                
    with open("output/all_products_openai.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

def main():
    # run_parse()
    db_openai()
    return True
    
if __name__ == "__main__":
    main()