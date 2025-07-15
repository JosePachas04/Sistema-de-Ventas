from ..services.db_service import get_db_connection
import mysql.connector
import json
import os
import requests

def get_chatbot_response(user_message, chat_history):
    # --- 1. Obtener datos dinámicos del sistema ---
    
    # Obtener info de la tienda desde el archivo .env
    store_address = os.getenv('DIRECCION_TIENDA', 'Dirección no especificada.')
    store_phone = os.getenv('TELEFONO_CONTACTO', 'Teléfono no especificado.')

    # Obtener los productos más vendidos de la base de datos
    top_products = []
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Consulta para encontrar los productos más vendidos
                query = """
                    SELECT p.name, SUM(oi.quantity) as total_sold
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    GROUP BY p.name
                    ORDER BY total_sold DESC
                    LIMIT 3;
                """
                cursor.execute(query)
                top_products = [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error as e:
            print(f"Error al obtener productos más vendidos: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    
    # Formatear sugerencias para el prompt
    if not top_products:
        suggestions_text = "Te sugiero explorar nuestras categorías como 'Bebidas' o 'Comestibles y productos básicos'."
    else:
        suggestions_text = f"Te recomiendo nuestros productos más populares: {', '.join(top_products)}. ¡A nuestros clientes les encantan!"


    # --- 2. Construir el prompt para la IA con los datos dinámicos ---
    system_prompt = f"""
    Eres 'AbarroBot', un asistente de ventas amigable y servicial para la tienda online 'TuAbarrote'. Tu nombre es Nelly.
    Tu objetivo es ayudar a los clientes con sus compras. Responde siempre en español y de forma muy breve y directa.

    **Información de la Tienda que DEBES usar:**
    - Dirección de la tienda: "{store_address}"
    - Teléfono de contacto: "{store_phone}"
    
    **Reglas de Interacción:**
    - Si te preguntan por "dirección" o "dónde están", responde con la dirección que te he proporcionado.
    - Si te preguntan por "teléfono", "número" o "contacto", responde con el número de teléfono.
    - Si te piden una "sugerencia" o "qué recomiendas", responde con el siguiente texto exacto: "{suggestions_text}"
    - Para cualquier otra pregunta, usa tu inteligencia general.
    - Si te preguntan por el precio o stock de un producto específico, amablemente diles que usen la barra de búsqueda principal para ver la información más actualizada.
    - Sé siempre amable y usa emojis de vez en cuando para parecer más cercana.
    """
    
    api_history = [{"role": "user", "parts": [{"text": system_prompt}]}]
    api_history.append({"role": "model", "parts": [{"text": "¡Hola! 😊 Soy Nelly, tu asistente de TuAbarrote. ¿En qué puedo ayudarte hoy?"}]})

    for message in chat_history:
        role = "user" if message["sender"] == "user" else "model"
        api_history.append({"role": role, "parts": [{"text": message["text"]}]})
    
    api_history.append({"role": "user", "parts": [{"text": user_message}]})

    # --- 3. Llamar a la API de Gemini ---
    try:
        apiKey = ""
        apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"
        payload = {"contents": api_history}
        
        response = requests.post(apiUrl, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if (result.get('candidates') and result['candidates'][0].get('content') and 
            result['candidates'][0]['content']['parts'][0].get('text')):
            bot_response = result['candidates'][0]['content']['parts'][0]['text']
            return bot_response
        else:
            return "No te he entendido bien. ¿Podrías preguntarme de otra forma?"

    except requests.exceptions.RequestException as e:
        print(f"Error en la petición a la API: {e}")
        return "Uhm, estoy teniendo problemas de conexión. Intenta de nuevo, por favor."
    except Exception as e:
        print(f"Error llamando a la API de Gemini: {e}")
        return "Lo siento, ocurrió un error técnico. Por favor, intenta de nuevo en unos momentos."
