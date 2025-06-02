from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DB_CONFIG = {
    'host': os.getenv('HOST'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'), # Reemplaza con tu contraseña si es diferente
    'database': os.getenv('DATABASE'),
    'port': int(os.getenv('PORT'))
}

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'products')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG, autocommit=False)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        flash("Error al conectar con la base de datos.", "danger")
        return None

def is_logged_in():
    return 'user_id' in session

def get_user_role():
    return session.get('user_role')

def is_admin():
    return is_logged_in() and get_user_role() == 'admin'

def is_customer():
     return is_logged_in() and get_user_role() == 'customer'

@app.route('/')
def index():
    return redirect(url_for('products_for_customer'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        if is_admin(): return redirect(url_for('admin_dashboard'))
        else: return redirect(url_for('products_for_customer'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        conn, cursor = None, None
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT id, username, password, role, email FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                if user is None: error = 'Usuario incorrecto.'
                elif not check_password_hash(user['password'], password): error = 'Contraseña incorrecta.'
                
                if error is None:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_role'] = user['role']
                    session['user_email'] = user.get('email')
                    if session['user_role'] == 'admin':
                        flash('Inicio de sesión de administrador exitoso!', 'success')
                        return redirect(url_for('admin_dashboard'))
                    else:
                        flash('Inicio de sesión exitoso!', 'success')
                        return redirect(url_for('products_for_customer'))
            else:
                error = 'Error de conexión a la base de datos.'
        except mysql.connector.Error as e:
            print(f"Error DB login: {e}")
            error = 'Ocurrió un error al intentar iniciar sesión.'
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        return render_template('login.html', error=error, username=username)
    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        if is_admin(): return redirect(url_for('admin_dashboard'))
        else: return redirect(url_for('products_for_customer'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        error = None
        conn_check, cursor_check, conn_insert, cursor_insert = None, None, None, None

        if not username or not email or not password or not confirm_password:
            error = 'Todos los campos son obligatorios.'
        elif password != confirm_password:
            error = 'Las contraseñas no coinciden.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            error = 'Formato de correo electrónico inválido.'

        if error is None:
            try:
                conn_check = get_db_connection()
                if conn_check:
                    cursor_check = conn_check.cursor()
                    query_check = "SELECT id FROM users WHERE username = %s OR email = %s"
                    cursor_check.execute(query_check, (username, email))
                    if cursor_check.fetchone():
                        error = 'El nombre de usuario o el correo electrónico ya están registrados.'
                else: error = 'Error de conexión (verificación).'
            except mysql.connector.Error as e:
                print(f"Error DB (verificación): {e}")
                error = 'Error al verificar usuario.'
            finally:
                if cursor_check: cursor_check.close()
                if conn_check and conn_check.is_connected(): conn_check.close()

        if error is None:
            hashed_password = generate_password_hash(password)
            try:
                conn_insert = get_db_connection()
                if conn_insert:
                    cursor_insert = conn_insert.cursor()
                    query_insert = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
                    cursor_insert.execute(query_insert, (username, email, hashed_password, 'customer'))
                    conn_insert.commit()
                    flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
                    return redirect(url_for('login'))
                else: error = 'Error de conexión (registro).'
            except mysql.connector.Error as e:
                if conn_insert: conn_insert.rollback()
                print(f"Error DB (registro): {e}")
                error = 'Error al registrar usuario.'
            finally:
                if cursor_insert: cursor_insert.close()
                if conn_insert and conn_insert.is_connected(): conn_insert.close()
        return render_template('register.html', error=error, username=username, email=email)
    return render_template('register.html', error=None, username='', email='')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user_role', None)
    session.pop('user_email', None)
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
     if not is_admin():
         flash('Acceso denegado. Inicia sesión como administrador.', 'danger')
         return redirect(url_for('login'))
     return render_template('admin_dashboard.html', user_role=get_user_role(), is_logged_in=is_logged_in())

@app.route('/products') 
def products():
    if not is_admin():
        if is_customer(): return redirect(url_for('products_for_customer'))
        else: return redirect(url_for('login'))

    conn, cursor = None, None
    products_list = []
    try:
        conn = get_db_connection()
        if not conn: flash("Error de conexión (admin productos).", "danger")
        else:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT p.id, p.name, p.description, p.price, p.stock, p.unidad_medida, p.is_active,
                   p.image_filename, p.category_id, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.id DESC
            """
            cursor.execute(query)
            products_list = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Error DB (admin productos): {e}")
        flash("Error al cargar lista de productos (admin).", "danger")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('products.html', products=products_list, user_role=get_user_role(), is_logged_in=is_logged_in())

@app.route('/products_for_customer', defaults={'category_id': None})
@app.route('/products_for_customer/category/<int:category_id>')
def products_for_customer(category_id):
    conn, cursor = None, None
    products_list, categories_list = [], []
    selected_category_name = None 
    try:
        conn = get_db_connection()
        if not conn: flash("Error de conexión (productos cliente).", "danger")
        else:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, name FROM categories ORDER BY name")
                categories_list = cursor.fetchall()
            except mysql.connector.Error as e_cat: print(f"Error DB (cat. sidebar): {e_cat}")

            query_products = """
            SELECT p.id, p.name, p.description, p.price, p.stock, p.unidad_medida,
                   p.image_filename, p.category_id, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE AND p.stock > 0
            """
            params_products = []
            if category_id is not None:
                query_products += " AND p.category_id = %s"
                params_products.append(category_id)
                for cat_item in categories_list:
                    if cat_item['id'] == category_id:
                        selected_category_name = cat_item['name']
                        break
            query_products += " ORDER BY p.name ASC"
            cursor.execute(query_products, params_products)
            products_list = cursor.fetchall()
    except mysql.connector.Error as e_main:
        print(f"Error DB (productos cliente): {e_main}")
        flash("Error al cargar productos.", "danger")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close() 
        
    return render_template('products.html', products=products_list, categories=categories_list,
                           user_role=get_user_role(), is_logged_in=is_logged_in(), 
                           selected_category=selected_category_name)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not is_admin():
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('login'))

    categories_list = []
    conn_cat, cursor_cat = None, None
    try:
        conn_cat = get_db_connection()
        if conn_cat:
            cursor_cat = conn_cat.cursor(dictionary=True)
            cursor_cat.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor_cat.fetchall()
        else: flash("Error de conexión (cat. add_product).", "danger")
    except mysql.connector.Error as e:
        print(f"Error DB (cat. add_product): {e}")
        flash("Error al cargar categorías.", "danger")
    finally:
        if cursor_cat: cursor_cat.close()
        if conn_cat and conn_cat.is_connected(): conn_cat.close()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price_str, stock_str = request.form.get('price'), request.form.get('stock')
        unidad_medida = request.form.get('unidad_medida', '').strip()
        is_active = 'is_active' in request.form
        category_id_form = request.form.get('category_id')
        error, image_filename = None, None
        
        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
             filename = secure_filename(file.filename)
             try:
                 file.save(os.path.join(UPLOAD_FOLDER, filename))
                 image_filename = filename
             except Exception as e_file: error = f"Error al subir imagen: {e_file}"
        
        if not error:
            try:
                price_float = float(price_str)
                stock_int = int(stock_str)
                cat_id_int = int(category_id_form) if category_id_form and category_id_form.isdigit() else None
                if not name or cat_id_int is None: error = "Nombre y categoría son obligatorios."
                elif price_float < 0 or stock_int < 0: error = "Precio/stock no pueden ser negativos."
            except (ValueError, TypeError): error = "Precio/stock deben ser números válidos."

        if not error:
            conn_ins, cursor_ins = None, None
            try:
                conn_ins = get_db_connection()
                if conn_ins:
                    cursor_ins = conn_ins.cursor()
                    sql = "INSERT INTO products (name, description, price, stock, unidad_medida, is_active, image_filename, category_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                    vals = (name, description, price_float, stock_int, unidad_medida or None, is_active, image_filename, cat_id_int)
                    cursor_ins.execute(sql, vals)
                    conn_ins.commit()
                    flash(f"Producto '{name}' añadido!", 'success')
                    return redirect(url_for('products'))
                else: error = "Error de conexión (guardar producto)."
            except mysql.connector.Error as e_db:
                if conn_ins: conn_ins.rollback()
                error = f"Error DB al guardar: {e_db}"
            finally:
                if cursor_ins: cursor_ins.close()
                if conn_ins and conn_ins.is_connected(): conn_ins.close()
        
        return render_template('add_product.html', error=error, name=name, description=description, price=price_str, stock=stock_str, unidad_medida=unidad_medida, is_active=is_active, category_id=category_id_form, categories=categories_list)
    
    return render_template('add_product.html', categories=categories_list, error=None, name='', description='', price='', stock='', unidad_medida='', is_active=True, category_id=None)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not is_admin():
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('login'))

    conn, cursor = None, None
    product_initial, categories_list_load, error_load = None, [], None

    try: 
        conn = get_db_connection()
        if not conn:
            error_load = "Error de conexión."
            flash(error_load, "danger")
            return redirect(url_for('products'))
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product_initial = cursor.fetchone()

        if not product_initial:
            flash("Producto no encontrado.", "warning")
            return redirect(url_for('products'))
            
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories_list_load = cursor.fetchall()
    except mysql.connector.Error as e:
        error_load = f"Error al cargar datos para editar: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

    if request.method == 'GET':
        if error_load and not product_initial:
             flash(error_load, "danger")
             return redirect(url_for('products'))
        return render_template('edit_product.html', product=product_initial, categories=categories_list_load, error=error_load)

    name, description = request.form.get('name'), request.form.get('description', '')
    price_str, stock_str = request.form.get('price'), request.form.get('stock')
    unidad_medida = request.form.get('unidad_medida', '').strip()
    is_active = 'is_active' in request.form
    category_id_form = request.form.get('category_id')
    current_post_error = None
    
    if not product_initial: # Debería existir por el GET, pero como fallback
        flash("Error crítico: Producto base no encontrado.", "danger")
        return redirect(url_for('products'))

    image_filename = product_initial.get('image_filename') 
    file = request.files.get('image')
    if file and file.filename and allowed_file(file.filename):
         filename = secure_filename(file.filename)
         try:
             file.save(os.path.join(UPLOAD_FOLDER, filename))
             image_filename = filename 
         except Exception as e_file: current_post_error = f"Error al subir nueva imagen: {e_file}"

    if not current_post_error:
        try:
            price_float = float(price_str)
            stock_int = int(stock_str)
            cat_id_int = int(category_id_form) if category_id_form and category_id_form.isdigit() else None
            if not name or cat_id_int is None: current_post_error = "Nombre y categoría son obligatorios."
            elif price_float < 0 or stock_int < 0: current_post_error = "Precio/stock no negativos."
        except (ValueError, TypeError): current_post_error = "Precio/stock deben ser números."

    if not current_post_error:
        conn_update, cursor_update = None, None
        try:
            conn_update = get_db_connection()
            if conn_update:
                cursor_update = conn_update.cursor()
                sql = "UPDATE products SET name=%s,description=%s,price=%s,stock=%s,unidad_medida=%s,is_active=%s,image_filename=%s,category_id=%s WHERE id=%s"
                vals = (name,description,price_float,stock_int,unidad_medida or None,is_active,image_filename,cat_id_int,product_id)
                cursor_update.execute(sql, vals)
                conn_update.commit()
                flash(f"Producto '{name}' actualizado!", 'success')
                return redirect(url_for('products'))
            else: current_post_error = "Error de conexión (actualizar)."
        except mysql.connector.Error as e_db:
            if conn_update: conn_update.rollback()
            current_post_error = f"Error DB al actualizar: {e_db}"
        finally:
            if cursor_update: cursor_update.close()
            if conn_update and conn_update.is_connected(): conn_update.close()
    
    product_form_data = {
         'id': product_id, 'name': name, 'description': description, 'price': price_str, 
         'stock': stock_str, 'unidad_medida': unidad_medida, 'is_active': is_active, 
         'image_filename': image_filename, 'category_id': category_id_form, 
    }
    return render_template('edit_product.html', product=product_form_data, categories=categories_list_load, error=current_post_error)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('login'))
    conn, cursor = None, None
    try:
        conn = get_db_connection()
        if not conn:
            flash("Error de conexión.", "danger")
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT image_filename FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            cursor.close() # Cerrar cursor de select

            cursor = conn.cursor() # Nuevo cursor para delete
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()
            
            if result and result['image_filename']:
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, result['image_filename']))
                except Exception as e_file:
                    flash(f"Producto borrado, error al eliminar imagen: {e_file}", "warning")
            flash("Producto eliminado.", "success")
    except mysql.connector.Error as e:
        if conn: conn.rollback()
        flash(f"Error al eliminar producto: {e}", "danger")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return redirect(url_for('products'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if not is_logged_in():
         flash('Debes iniciar sesión.', 'warning')
         return redirect(url_for('login'))

    conn, cursor = None, None
    product, error = None, None
    try:
        conn = get_db_connection()
        if not conn: error = "Error de conexión."
        else:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT p.*, c.name as category_name FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = %s
            """
            cursor.execute(query, (product_id,))
            product = cursor.fetchone()
            if not product: flash("Producto no encontrado.", "warning")
            elif is_customer() and (not product['is_active'] or product['stock'] <= 0):
                 flash("Producto no disponible.", "warning")
                 product = None # Para que no se muestre si no está disponible para el cliente
    except mysql.connector.Error as e: error = f"Error al cargar detalle: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    
    if error: flash(error, "danger")
    if product is None and not error : # Si no hay producto y no fue por error de BD
        return redirect(url_for('products_for_customer'))
        
    return render_template('product_detail.html', product=product, user_role=get_user_role(), is_logged_in=is_logged_in(), error=error)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if not is_logged_in():
         flash('Debes iniciar sesión.', 'warning')
         return redirect(url_for('login'))

    try: quantity = int(request.form.get('quantity', 1))
    except ValueError: quantity = 1
    if quantity <= 0: quantity = 1

    conn, cursor = None, None
    can_add = False
    p_name = "Producto"
    try:
        conn = get_db_connection()
        if not conn: flash("Error de conexión.", "danger")
        else:
            cursor = conn.cursor(dictionary=True) 
            cursor.execute("SELECT stock, is_active, name FROM products WHERE id = %s", (product_id,))
            p_info = cursor.fetchone()
            if p_info:
                p_name = p_info['name']
                if not p_info['is_active']: flash(f"'{p_name}' no disponible.", "warning")
                else:
                    cart = session.get('cart', {})
                    in_cart_qty = cart.get(str(product_id), 0)
                    if in_cart_qty + quantity > p_info['stock']:
                        flash(f"Solo quedan {p_info['stock']} de '{p_name}'.", "warning")
                    else: can_add = True 
            else: flash("Producto no válido.", "danger")
    except mysql.connector.Error as e: flash(f"Error al verificar stock: {e}", "danger")
    finally:
         if cursor: cursor.close()
         if conn and conn.is_connected(): conn.close()

    if not can_add: 
        return redirect(request.referrer or url_for('product_detail', product_id=product_id))

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} x '{p_name}' añadido(s)!", "success")
    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart')
def view_cart():
    if not is_logged_in():
        flash('Debes iniciar sesión para ver tu carrito.', 'warning')
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    cart_items, total_price = [], 0
    conn, cursor = None, None

    if cart:
        p_ids_str = list(cart.keys())
        p_ids_int = [int(pid) for pid in p_ids_str if pid.isdigit()]

        if not p_ids_int:
            if cart: session.pop('cart', None); session.modified = True; flash("Carrito limpiado.", "warning")
        else:
            try:
                conn = get_db_connection()
                if not conn: flash("Error de conexión (carrito).", "danger")
                else:
                    cursor = conn.cursor(dictionary=True)
                    placeholders = ','.join(['%s'] * len(p_ids_int))
                    query = f"SELECT * FROM products WHERE id IN ({placeholders})"
                    cursor.execute(query, p_ids_int)
                    db_products = {p['id']: p for p in cursor.fetchall()}
                    
                    modified_cart_in_view = False
                    current_session_cart = dict(cart) 

                    for pid_s, qty_s in current_session_cart.items():
                        try: pid, qty = int(pid_s), int(qty_s)
                        except ValueError: cart.pop(pid_s, None); modified_cart_in_view = True; continue

                        if pid in db_products:
                            p = db_products[pid]
                            if not p['is_active'] or p['stock'] == 0:
                                flash(f"'{p['name']}' no disponible/sin stock, eliminado.", "warning")
                                cart.pop(pid_s, None); modified_cart_in_view = True
                            elif p['stock'] < qty:
                                flash(f"Stock de '{p['name']}' ajustado a {p['stock']}.", "info")
                                cart[pid_s] = p['stock']
                                qty = p['stock'] # Usar la cantidad ajustada
                                total_price += p['price'] * qty
                                cart_items.append({'product': p, 'quantity': qty, 'item_total': p['price'] * qty})
                                modified_cart_in_view = True
                            else:
                                total_price += p['price'] * qty
                                cart_items.append({'product': p, 'quantity': qty, 'item_total': p['price'] * qty})
                        else:
                            flash(f"Producto ID {pid} no encontrado, eliminado.", "warning")
                            cart.pop(pid_s, None); modified_cart_in_view = True
                    
                    if modified_cart_in_view:
                       session['cart'] = cart
                       session.modified = True
            except mysql.connector.Error as e: flash(f"Error al cargar carrito: {e}", "danger")
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
    
    return render_template('cart.html', cart_items=cart_items, total_price=total_price, user_role=get_user_role(), is_logged_in=is_logged_in(), user_id=session.get('user_id'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    if not is_logged_in():
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('login'))
    try: qty_form = int(request.form.get('quantity'))
    except: qty_form = -1 # Para que entre en el else de cantidad no válida

    cart = session.get('cart', {})
    pid_s = str(product_id)

    if qty_form >= 0:
        if qty_form > 0:
            conn, cursor = None, None
            try:
                conn = get_db_connection()
                if not conn: flash("Error de conexión.", "danger")
                else:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT stock, is_active, name FROM products WHERE id = %s", (product_id,))
                    p_info = cursor.fetchone()
                    if p_info:
                        if not p_info['is_active']: flash(f"'{p_info['name']}' no disponible.", "warning"); cart.pop(pid_s, None)
                        elif qty_form > p_info['stock']: flash(f"Solo {p_info['stock']} de '{p_info['name']}'.", "warning")
                        else: cart[pid_s] = qty_form; flash("Cantidad actualizada.", "info")
                    else: flash(f"ID {product_id} no encontrado.", "danger"); cart.pop(pid_s, None)
            except mysql.connector.Error as e: flash(f"Error al actualizar: {e}", "danger")
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
        elif qty_form == 0: cart.pop(pid_s, None); flash("Producto eliminado.", "warning")
        session['cart'] = cart
        session.modified = True
    else: flash("Cantidad no válida.", "warning")
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if not is_logged_in():
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    if str(product_id) in cart:
        cart.pop(str(product_id))
        session['cart'] = cart
        session.modified = True
        flash("Producto eliminado.", "warning")
    else: flash("Producto no encontrado en carrito.", "info")
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    if not is_customer():
        flash('Debes iniciar sesión como cliente.', 'warning')
        return redirect(url_for('login'))
    user_id, cart = session.get('user_id'), session.get('cart', {})
    if not cart:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for('products_for_customer'))

    conn, cursor = None, None
    try:
        conn = get_db_connection()
        if not conn: flash("Error de conexión.", "danger"); return redirect(url_for('view_cart'))
        cursor = conn.cursor(dictionary=True)

        # Validar carrito y stock
        items_for_template, total_price_checkout = [], 0
        items_to_process, total_amount_db, stock_errors = [], 0, []
        
        p_ids = [int(pid) for pid in cart.keys() if pid.isdigit()]
        if not p_ids: flash("Carrito inválido.", "warning"); return redirect(url_for('view_cart'))

        query = f"SELECT * FROM products WHERE id IN ({','.join(['%s']*len(p_ids))})"
        cursor.execute(query, p_ids)
        db_prods = {p['id']: p for p in cursor.fetchall()}

        for pid_s, qty_s in cart.items():
            try: pid, qty = int(pid_s), int(qty_s)
            except ValueError: stock_errors.append(f"Item inválido (ID/cant)."); continue
            if qty <= 0: continue

            if pid in db_prods:
                p = db_prods[pid]
                if not p['is_active']: stock_errors.append(f"'{p['name']}' no disponible.")
                elif p['stock'] < qty: stock_errors.append(f"Stock de '{p['name']}' (Disp:{p['stock']}) insuficiente para {qty}.")
                else:
                    items_for_template.append({'product': p, 'quantity': qty, 'item_total': p['price'] * qty})
                    total_price_checkout += p['price'] * qty
                    items_to_process.append({'product_id': pid, 'quantity': qty, 'price_at_purchase': p['price']})
                    total_amount_db += p['price'] * qty
            else: stock_errors.append(f"Producto ID {pid} no encontrado.")

        if request.method == 'GET':
            if stock_errors: # Mostrar errores de stock en la página de checkout si es GET
                for err in stock_errors: flash(err, "warning")
                # Podrías decidir redirigir al carrito si hay errores de stock en GET
                # return redirect(url_for('view_cart')) 
            return render_template('checkout.html', cart_items=items_for_template, total_price=total_price_checkout, user_role=get_user_role(), is_logged_in=is_logged_in())

        # --- Lógica POST ---
        if stock_errors: # Si hay errores de stock en POST, no continuar
            for err in stock_errors: flash(err, "danger")
            return redirect(url_for('view_cart'))
        if not items_to_process: # Si no hay items válidos
            flash("No hay productos válidos para procesar.", "warning")
            return redirect(url_for('view_cart'))

        conn.start_transaction()
        try:
            q_order = "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s)"
            cursor.execute(q_order, (user_id, total_amount_db, 'Processing'))
            order_id = cursor.lastrowid

            q_item = "INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (%s,%s,%s,%s)"
            q_stock = "UPDATE products SET stock = stock - %s WHERE id = %s"
            for item in items_to_process:
                cursor.execute(q_item, (order_id, item['product_id'], item['quantity'], item['price_at_purchase']))
                cursor.execute(q_stock, (item['quantity'], item['product_id']))
            
            conn.commit()
            session['cart'] = {}
            session.modified = True
            flash(f"¡Pedido #{order_id} procesado con éxito!", "success")
            return redirect(url_for('order_confirmation', order_id=order_id))
        except Exception as e_trans:
            if conn.in_transaction: conn.rollback()
            flash(f"Error durante transacción: {e_trans}", "danger")
            return redirect(url_for('view_cart'))

    except mysql.connector.Error as e_db:
         print(f"Error de BD en checkout: {e_db}")
         flash("Error de base de datos al procesar checkout.", "danger")
         if conn and conn.in_transaction: conn.rollback() # Si la transacción se inició
         return redirect(url_for('view_cart'))
    except Exception as e_gen:
        print(f"Error general en checkout: {e_gen}")
        flash("Error inesperado al procesar checkout.", "danger")
        if conn and conn.in_transaction: conn.rollback()
        return redirect(url_for('view_cart'))
    finally:
         if cursor: cursor.close()
         if conn and conn.is_connected(): conn.close()
    return redirect(url_for('index')) # Fallback

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if not is_logged_in():
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('login'))
    conn, cursor = None, None
    order, items, error_msg = None, [], None
    try:
        conn = get_db_connection()
        if not conn: error_msg = "Error de conexión."
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            if not order: flash("Pedido no encontrado.", "warning"); return redirect(url_for('index'))
            if not is_admin() and order['user_id'] != session.get('user_id'):
                flash("No tienes permiso.", "danger"); return redirect(url_for('index'))
            
            q_items = "SELECT oi.*, p.name, p.unidad_medida, p.image_filename FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s"
            cursor.execute(q_items, (order_id,))
            items = cursor.fetchall()
    except mysql.connector.Error as e: error_msg = f"Error al cargar confirmación: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    if error_msg: flash(error_msg, "danger")
    return render_template('order_confirmation.html', order=order, order_items=items, user_role=get_user_role(), is_logged_in=is_logged_in(), error=error_msg)

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html', user_role=get_user_role(), is_logged_in=is_logged_in())

@app.route('/search')
def search():
    query_term = request.args.get('query', '').strip()
    results, cats, error_s = [], [], None
    conn, cursor = None, None
    if not query_term:
        return render_template('search_results.html', query=query_term, products_results=results, categories_results=cats, user_role=get_user_role(), is_logged_in=is_logged_in(), error=None)
    try:
        conn = get_db_connection()
        if not conn: error_s = "Error de conexión (búsqueda)."
        else:
            cursor = conn.cursor(dictionary=True)
            param = f"%{query_term}%"
            cursor.execute("SELECT * FROM products WHERE (name LIKE %s OR description LIKE %s) AND is_active = TRUE AND stock > 0", (param, param))
            results = cursor.fetchall()
            cursor.execute("SELECT id, name FROM categories WHERE name LIKE %s", (param,))
            cats = cursor.fetchall()
    except mysql.connector.Error as e: error_s = f"Error en búsqueda: {e}"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    if error_s: flash(error_s, "danger")
    return render_template('search_results.html', query=query_term, products_results=results, categories_results=cats, user_role=get_user_role(), is_logged_in=is_logged_in(), error=error_s)

if __name__ == '__main__':
    app.run(debug=True)