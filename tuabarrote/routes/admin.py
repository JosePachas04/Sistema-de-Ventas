from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from ..services.db_service import get_db_connection
from ..services.auth_service import admin_required
import os
import mysql.connector

bp = Blueprint('admin', __name__, url_prefix='/admin')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/products')
@admin_required
def manage_products():
    conn = get_db_connection()
    if not conn:
        return render_template('admin/manage_products.html', products=[])
    
    products_list = []
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.id DESC"
            cursor.execute(query)
            products_list = cursor.fetchall()
    except mysql.connector.Error as e:
        flash("Error al cargar productos para administrar.", "danger")
        print(f"Error DB admin products: {e}")
    finally:
        if conn.is_connected():
            conn.close()
    return render_template('admin/manage_products.html', products=products_list)

@bp.route('/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('admin.manage_products'))
    
    categories_list = []
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor.fetchall()
    except mysql.connector.Error as e:
        flash("Error al cargar categorías.", "danger")
    finally:
        if conn.is_connected():
            conn.close()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        stock = request.form.get('stock')
        unidad_medida = request.form.get('unidad_medida', '').strip()
        category_id = request.form.get('category_id')
        is_active = 'is_active' in request.form
        file = request.files.get('image')
        
        image_filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        conn_insert = get_db_connection()
        try:
            with conn_insert.cursor() as cursor:
                sql = "INSERT INTO products (name, description, price, stock, unidad_medida, is_active, image_filename, category_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, (name, description, price, stock, unidad_medida, is_active, image_filename, category_id))
                conn_insert.commit()
                flash(f"Producto '{name}' añadido con éxito.", "success")
        except mysql.connector.Error as e:
            flash("Error al añadir el producto.", "danger")
            print(f"Error DB add product: {e}")
        finally:
            if conn_insert.is_connected():
                conn_insert.close()
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/add_edit_product.html', categories=categories_list, product=None, title="Añadir Producto")

@bp.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('admin.manage_products'))

    product = None
    categories_list = []
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor.fetchall()
    except mysql.connector.Error as e:
        flash("Error al cargar datos del producto.", "danger")
    finally:
        if conn.is_connected():
            conn.close()
    
    if not product:
        flash("Producto no encontrado.", "warning")
        return redirect(url_for('admin.manage_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        stock = request.form.get('stock')
        unidad_medida = request.form.get('unidad_medida', '').strip()
        category_id = request.form.get('category_id')
        is_active = 'is_active' in request.form
        file = request.files.get('image')
        
        image_filename = product['image_filename']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        conn_update = get_db_connection()
        try:
            with conn_update.cursor() as cursor:
                sql = "UPDATE products SET name=%s, description=%s, price=%s, stock=%s, unidad_medida=%s, is_active=%s, image_filename=%s, category_id=%s WHERE id=%s"
                cursor.execute(sql, (name, description, price, stock, unidad_medida, is_active, image_filename, category_id, product_id))
                conn_update.commit()
                flash(f"Producto '{name}' actualizado con éxito.", "success")
        except mysql.connector.Error as e:
            flash("Error al actualizar el producto.", "danger")
            print(f"Error DB edit product: {e}")
        finally:
            if conn_update.is_connected():
                conn_update.close()
        return redirect(url_for('admin.manage_products'))
    
    return render_template('admin/add_edit_product.html', product=product, categories=categories_list, title="Editar Producto")

@bp.route('/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('admin.manage_products'))

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT image_filename FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if result and result['image_filename']:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], result['image_filename']))
                except OSError as e:
                    print(f"Error eliminando imagen: {e}")

            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()
            flash("Producto eliminado con éxito.", "success")
    except mysql.connector.Error as e:
        flash("Error al eliminar el producto.", "danger")
        print(f"Error DB delete product: {e}")
    finally:
        if conn.is_connected():
            conn.close()

    return redirect(url_for('admin.manage_products'))
