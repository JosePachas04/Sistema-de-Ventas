# tuabarrote/services/db_service.py

import mysql.connector
import os
from flask import flash
from datetime import datetime # <--- IMPORTANTE: AÑADIR ESTA LÍNEA

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('HOST'),
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            database=os.getenv('DATABASE'),
            port=int(os.getenv('PORT'))
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        flash("Error de comunicación con el servidor. Inténtelo más tarde.", "danger")
        return None

def process_order_transaction(user_id, cart):
    """
    Procesa una orden completa. Esta función es transaccional.
    Devuelve un diccionario con el estado y el ID de la orden si es exitosa.
    """
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'No se pudo conectar a la base de datos.'}

    try:
        with conn.cursor(dictionary=True) as cursor:
            # 1. Verificación de Stock
            product_ids = list(cart.keys())
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"SELECT id, name, price, stock FROM products WHERE id IN ({placeholders})"
            cursor.execute(query, product_ids)
            db_products = {str(p['id']): p for p in cursor.fetchall()}

            items_to_process = []
            total_amount = 0

            for pid, qty in cart.items():
                product = db_products.get(pid)
                if not product or product['stock'] < qty:
                    error_msg = f"Stock insuficiente para {product.get('name', 'un producto') if product else 'un producto'}."
                    conn.close()
                    return {'success': False, 'error': error_msg}
                
                price = product['price']
                total_amount += price * qty
                items_to_process.append({'id': pid, 'qty': qty, 'price': price})

            # --- 3. Crear la orden (CON FECHA) ---
            now = datetime.utcnow() # Obtener la fecha y hora actual
            cursor.execute(
                # ===== CONSULTA MODIFICADA =====
                "INSERT INTO orders (user_id, total_amount, status, created_at) VALUES (%s, %s, %s, %s)",
                (user_id, total_amount, 'Completado', now)
            )
            order_id = cursor.lastrowid

            # --- 4. Insertar los items y actualizar stock ---
            order_items_sql = "INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (%s, %s, %s, %s)"
            update_stock_sql = "UPDATE products SET stock = stock - %s WHERE id = %s"

            for item in items_to_process:
                cursor.execute(order_items_sql, (order_id, item['id'], item['qty'], item['price']))
                cursor.execute(update_stock_sql, (item['qty'], item['id']))

            # 5. Confirmar transacción
            conn.commit()
            return {'success': True, 'order_id': order_id}

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error DB en transacción de orden: {e}")
        return {'success': False, 'error': 'Ocurrió un error al procesar tu pedido. Inténtalo de nuevo.'}
    finally:
        if conn and conn.is_connected():
            conn.close()