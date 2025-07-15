from flask import Blueprint, render_template, request, flash, url_for, redirect
from ..services.db_service import get_db_connection
from ..services.auth_service import is_customer
import math
import mysql.connector

bp = Blueprint('products', __name__)
PRODUCTS_PER_PAGE = 9

@bp.route('/products', defaults={'category_id': None})
@bp.route('/products/category/<int:category_id>')
def products_for_customer(category_id=None):
    page = request.args.get('page', 1, type=int)
    conn = get_db_connection()
    if not conn:
        return render_template('products.html', products=[], categories=[], total_pages=1, current_page=1)
    
    products_list, categories_list = [], []
    selected_category_name = None 
    total_products = 0
    total_pages = 1

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor.fetchall()

            query_base = "FROM products p WHERE p.is_active = TRUE AND p.stock > 0"
            params = []
            if category_id:
                query_base += " AND p.category_id = %s"
                params.append(category_id)
                selected_category_name = next((c['name'] for c in categories_list if c['id'] == category_id), None)
            
            cursor.execute("SELECT COUNT(p.id) as total " + query_base, tuple(params))
            total_products = cursor.fetchone()['total']
            
            if total_products > 0:
                total_pages = math.ceil(total_products / PRODUCTS_PER_PAGE)

            offset = (page - 1) * PRODUCTS_PER_PAGE
            query_products = f"""
            SELECT p.*, c.name as category_name
            {query_base.replace("FROM products p", "FROM products p LEFT JOIN categories c ON p.category_id = c.id")}
            ORDER BY p.name ASC LIMIT %s OFFSET %s
            """
            cursor.execute(query_products, tuple(params + [PRODUCTS_PER_PAGE, offset]))
            products_list = cursor.fetchall()
    except mysql.connector.Error as e:
        flash("Error al cargar productos.", "danger")
        print(f"Error DB products: {e}")
    finally:
        if conn.is_connected():
            conn.close() 
        
    return render_template('products.html', 
                           products=products_list, 
                           categories=categories_list,
                           selected_category_name=selected_category_name,
                           selected_category_id=category_id,
                           current_page=page,
                           total_pages=total_pages)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('products.products_for_customer'))
    
    product = None
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = %s"
            cursor.execute(query, (product_id,))
            product = cursor.fetchone()
            if not product:
                flash("Producto no encontrado.", "warning")
                return redirect(url_for('products.products_for_customer'))
            if is_customer() and (not product['is_active'] or product['stock'] <= 0):
                 flash("Este producto no está disponible actualmente.", "warning")
                 return redirect(url_for('products.products_for_customer'))
    except mysql.connector.Error as e:
        flash("Error al cargar el detalle del producto.", "danger")
        print(f"Error DB product_detail: {e}")
    finally:
        if conn.is_connected():
            conn.close()

    return render_template('product_detail.html', product=product)

@bp.route('/search')
def search():
    query_term = request.args.get('query', '').strip()
    if not query_term:
        return redirect(url_for('products.products_for_customer'))

    conn = get_db_connection()
    if not conn:
        return render_template('search_results.html', query=query_term, products_results=[])
    
    results = []
    try:
        with conn.cursor(dictionary=True) as cursor:
            param = f"%{query_term}%"
            cursor.execute("SELECT * FROM products WHERE (name LIKE %s OR description LIKE %s) AND is_active = TRUE AND stock > 0", (param, param))
            results = cursor.fetchall()
    except mysql.connector.Error as e:
        flash("Error durante la búsqueda.", "danger")
        print(f"Error DB search: {e}")
    finally:
        if conn.is_connected():
            conn.close()

    return render_template('search_results.html', query=query_term, products_results=results)
