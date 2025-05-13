from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'una_clave_secreta_muy_larga_y_aleatoria_para_tu_abarrote'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '72624803',
    'database': 'tuabarrotedb'
}

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'products')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
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
    if is_logged_in():
        if is_admin(): return redirect(url_for('admin_dashboard'))
        else: return redirect(url_for('products_for_customer'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
     if is_logged_in():
         if is_admin(): return redirect(url_for('admin_dashboard'))
         else: return redirect(url_for('products_for_customer'))
     if request.method == 'POST':
         username = request.form.get('username')
         password = request.form.get('password')
         error = None
         conn = get_db_connection()
         if conn:
             cursor = conn.cursor(dictionary=True)
             query = "SELECT id, username, password, role FROM users WHERE username = %s"
             try:
                  cursor.execute(query, (username,))
                  user = cursor.fetchone()
                  if user is None: error = 'Usuario incorrecto.'
                  elif not check_password_hash(user['password'], password): error = 'Contraseña incorrecta.'
                  if error is None:
                      session['user_id'] = user['id']
                      session['username'] = user['username']
                      session['user_role'] = user['role']
                      if session['user_role'] == 'admin':
                          flash('Inicio de sesión de administrador exitoso!', 'success')
                          return redirect(url_for('admin_dashboard'))
                      else:
                          flash('Inicio de sesión exitoso!', 'success')
                          return redirect(url_for('products_for_customer'))
             except mysql.connector.Error as e: print(f"Error DB login: {e}"); error = 'Ocurrió un error al intentar iniciar sesión.'
             finally:
                 if 'cursor' in locals() and cursor is not None: cursor.close()
                 if conn is not None: conn.close()
         else: error = 'Error de conexión a la base de datos.'
         return render_template('login.html', error=error, username=username)
     return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
     if is_logged_in():
         if is_admin(): return redirect(url_for('admin_dashboard'))
         else: return redirect(url_for('products_for_customer'))
     if request.method == 'POST':
         username = request.form.get('username')
         password = request.form.get('password')
         confirm_password = request.form.get('confirm_password')
         error = None
         if not username or not password or not confirm_password: error = 'Todos los campos son obligatorios.'
         elif password != confirm_password: error = 'Las contraseñas no coinciden.'
         if error is None:
              conn = get_db_connection()
              if conn:
                  cursor = conn.cursor()
                  query = "SELECT id FROM users WHERE username = %s"
                  try:
                     cursor.execute(query, (username,))
                     existing_user = cursor.fetchone()
                     if existing_user: error = f'El usuario "{username}" ya existe.'
                  except mysql.connector.Error as e: print(f"Error DB verificar usuario: {e}"); error = 'Ocurrió un error al verificar el usuario.'
                  finally:
                      if 'cursor' in locals() and cursor is not None: cursor.close()
                      if conn is not None: conn.close()
              else: error = 'Error de conexión a la base de datos al verificar usuario.'
         if error is None:
             hashed_password = generate_password_hash(password)
             conn = get_db_connection()
             if conn:
                 cursor = conn.cursor()
                 query = "INSERT INTO users (username, password) VALUES (%s, %s)"
                 try:
                     cursor.execute(query, (username, hashed_password))
                     conn.commit()
                     print("Registro exitoso para:", username)
                     flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
                     return redirect(url_for('login'))
                 except mysql.connector.Error as e: conn.rollback(); print(f"Error DB insertar usuario: {e}"); error = 'Ocurrió un error al intentar registrar el usuario.'
                 finally:
                      if 'cursor' in locals() and cursor is not None: cursor.close()
                      if conn is not None: conn.close()
             else: error = 'Error de conexión a la base de datos al intentar registrar.'
         return render_template('register.html', error=error, username=username)
     return render_template('register.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user_role', None)
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
     conn = get_db_connection()
     products_list = []
     if conn:
         cursor = conn.cursor(dictionary=True)
         query = """
         SELECT p.id, p.name, p.description, p.price, p.stock, p.is_active,
                p.image_filename, p.category_id, c.name as category_name
         FROM products p LEFT JOIN categories c ON p.category_id = c.id
         ORDER BY p.id DESC
         """
         try:
             cursor.execute(query)
             products_list = cursor.fetchall()
         except mysql.connector.Error as e: print(f"Error DB obtener productos admin: {e}"); flash("Error al cargar la lista de productos.", "danger")
         finally:
              if 'cursor' in locals() and cursor is not None: cursor.close()
              if conn is not None: conn.close()
     return render_template('products.html', products=products_list, user_role=get_user_role(), is_logged_in=is_logged_in())


@app.route('/products_for_customer', defaults={'category_id': None})
@app.route('/products_for_customer/category/<int:category_id>')
def products_for_customer(category_id):
     if not is_logged_in():
         return redirect(url_for('login'))

     conn = get_db_connection()
     products_list = []
     categories_list = []
     selected_category = None

     if conn:
         cursor = conn.cursor(dictionary=True)
         try:
             cursor.execute("SELECT id, name FROM categories ORDER BY name")
             categories_list = cursor.fetchall()
         except mysql.connector.Error as e: print(f"Error DB obtener categorías para sidebar: {e}"); flash("Error al cargar las categorías.", "danger")

         query = """
         SELECT p.id, p.name, p.description, p.price, p.stock,
                p.image_filename, p.category_id, c.name as category_name
         FROM products p LEFT JOIN categories c ON p.category_id = c.id
         WHERE p.is_active = TRUE AND p.stock > 0
         """
         params = []

         if category_id is not None:
             query += " AND p.category_id = %s"
             params.append(category_id)
             try:
                 cat_cursor = conn.cursor(dictionary=True)
                 cat_cursor.execute("SELECT name FROM categories WHERE id = %s", (category_id,))
                 cat_result = cat_cursor.fetchone()
                 if cat_result: selected_category = cat_result['name']
                 cat_cursor.close()
             except mysql.connector.Error as e: print(f"Error DB obtener nombre categoría: {e}")

         query += " ORDER BY p.id DESC"

         try:
             cursor.execute(query, params)
             products_list = cursor.fetchall()
         except mysql.connector.Error as e: print(f"Error DB obtener productos cliente (filtrado): {e}"); flash("Error al cargar los productos disponibles.", "danger")
         finally:
              if 'cursor' in locals() and cursor is not None: cursor.close()
              if conn is not None: conn.close()

     return render_template('products.html', products=products_list, categories=categories_list, user_role=get_user_role(), is_logged_in=is_logged_in(), selected_category=selected_category)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not is_admin():
        flash('Acceso denegado. Inicia sesión como administrador.', 'danger')
        return redirect(url_for('login'))

    categories_list = []
    conn_cat = get_db_connection()
    if conn_cat:
        cursor_cat = conn_cat.cursor(dictionary=True)
        try:
            cursor_cat.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor_cat.fetchall()
        except mysql.connector.Error as e: print(f"Error DB obtener categorías para formulario: {e}"); flash("Error al cargar categorías para el formulario.", "danger")
        finally:
            if 'cursor_cat' in locals() and cursor_cat is not None: cursor_cat.close()
            if conn_cat is not None: conn_cat.close()
    else: flash("Error de conexión a la base de datos al cargar categorías.", "danger")

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        stock = request.form.get('stock')
        is_active = 'is_active' in request.form
        category_id = request.form.get('category_id')

        image_filename = None
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
             filename = secure_filename(file.filename)
             filepath = os.path.join(UPLOAD_FOLDER, filename)
             try:
                 file.save(filepath)
                 image_filename = filename
             except Exception as e: print(f"Error al guardar archivo: {e}"); flash("Error al subir la imagen.", "danger")

        try:
            price_float = float(price) if price else 0.0
            stock_int = int(stock) if stock else 0
            category_id_int = int(category_id) if category_id and category_id.isdigit() else None

            if not name or price is None or stock is None or category_id_int is None: error = "Nombre, precio, stock y categoría son obligatorios."
            elif price_float < 0 or stock_int < 0: error = "Precio y stock no pueden ser negativos."
            else: error = None
        except ValueError: error = "Verifica que el precio y el stock sean números válidos."

        if error is None:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                query = """
                INSERT INTO products (name, description, price, stock, is_active, image_filename, category_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                try:
                     values = (name, description, price_float, stock_int, is_active, image_filename, category_id_int)
                     cursor.execute(query, values)
                     conn.commit()
                     print(f"Producto '{name}' añadido exitosamente.")
                     flash(f"Producto '{name}' añadido exitosamente!", 'success')
                     return redirect(url_for('products'))
                except mysql.connector.Error as e: conn.rollback(); print(f"Error DB al insertar producto: {e}"); error = 'Ocurrió un error al guardar el producto en la base de datos.'
                finally:
                     if 'cursor' in locals() and cursor is not None: cursor.close()
                     if conn is not None: conn.close()
            else: error = "Error de conexión a la base de datos al intentar guardar el producto."

        return render_template('add_product.html', error=error, name=name, description=description, price=price, stock=stock, is_active=is_active, category_id=category_id_int, categories=categories_list)

    return render_template('add_product.html', categories=categories_list, error=None, name='', description='', price='', stock=0, is_active=True)


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not is_admin():
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    product = None
    categories_list = []
    error = None

    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if product is None:
                 flash("Producto no encontrado.", "warning")
                 cursor.close()
                 conn.close()
                 return redirect(url_for('products'))
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories_list = cursor.fetchall()
        except mysql.connector.Error as e: print(f"Error DB al obtener producto para editar o categorías: {e}"); error = "Error al cargar datos del producto o categorías."
        finally:
             if 'cursor' in locals() and cursor is not None: cursor.close()
             if conn is not None: conn.close()
    else: error = "Error de conexión a la base de datos."

    if request.method == 'GET':
        return render_template('edit_product.html', product=product, categories=categories_list, error=error)

    if request.method == 'POST':
        conn_re = get_db_connection()
        if conn_re:
             cursor_re = conn_re.cursor(dictionary=True)
             try:
                  cursor_re.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                  product_before_update = cursor_re.fetchone()
                  cursor_re.execute("SELECT id, name FROM categories ORDER BY name")
                  categories_list = cursor_re.fetchall()
             except mysql.connector.Error as e_re: print(f"Error DB re-obteniendo datos para edición (POST error): {e_re}"); flash("Error al recargar datos para edición.", "danger")
             finally:
                  if 'cursor_re' in locals() and cursor_re is not None: cursor_re.close()
                  if conn_re is not None: conn_re.close()
        else: flash("Error de conexión a la base de datos al recargar datos.", "danger")


        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        stock = request.form.get('stock')
        is_active = 'is_active' in request.form
        category_id = request.form.get('category_id')

        image_filename = product_before_update['image_filename'] if product_before_update and 'image_filename' in product_before_update else None
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
             filename = secure_filename(file.filename)
             filepath = os.path.join(UPLOAD_FOLDER, filename)
             try:
                 file.save(filepath)
                 image_filename = filename
                 flash(f"Nueva imagen '{filename}' subida exitosamente.", "success")
             except Exception as e: print(f"Error al guardar nueva imagen: {e}"); flash("Error al subir la nueva imagen.", "danger")

        try:
            price_float = float(price) if price else 0.0
            stock_int = int(stock) if stock else 0
            category_id_int = int(category_id) if category_id and category_id.isdigit() else None

            if not name or price is None or stock is None or category_id_int is None: error = "Nombre, precio, stock y categoría son obligatorios."
            elif price_float < 0 or stock_int < 0: error = "Precio y stock no pueden ser negativos."
            else: error = None
        except ValueError: error = "Verifica que el precio y el stock sean números válidos."

        if error is None:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                query = """
                UPDATE products
                SET name = %s, description = %s, price = %s, stock = %s, is_active = %s,
                    image_filename = %s, category_id = %s
                WHERE id = %s
                """
                try:
                     values = (name, description, price_float, stock_int, is_active, image_filename, category_id_int, product_id)
                     cursor.execute(query, values)
                     conn.commit()
                     print(f"Producto '{name}' (ID: {product_id}) actualizado exitosamente.")
                     flash(f"Producto '{name}' actualizado exitosamente!", 'success')
                     return redirect(url_for('products'))
                except mysql.connector.Error as e: conn.rollback(); print(f"Error DB al actualizar producto: {e}"); error = 'Ocurrió un error al actualizar el producto en la base de datos.'
                finally:
                     if 'cursor' in locals() and cursor is not None: cursor.close()
                     if conn is not None: conn.close()
            else: error = "Error de conexión a la base de datos al intentar actualizar el producto."

        product_form_data = {
             'id': product_id,
             'name': name, 'description': description, 'price': price,
             'stock': stock, 'is_active': is_active, 'image_filename': image_filename,
             'category_id': category_id
        }
        return render_template('edit_product.html', product=product_form_data, categories=categories_list, error=error)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT image_filename FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            image_to_delete = result[0] if result and result[0] else None

            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()

            if image_to_delete:
                filepath = os.path.join(UPLOAD_FOLDER, image_to_delete)
                if os.path.exists(filepath):
                    try: os.remove(filepath); print(f"Imagen '{image_to_delete}' eliminada del disco.")
                    except Exception as e: print(f"Error al borrar archivo de imagen '{filepath}': {e}"); flash(f"Producto eliminado, pero hubo un error al borrar la imagen asociada.", "warning")

            print(f"Producto (ID: {product_id}) eliminado exitosamente.")
            flash("Producto eliminado exitosamente.", "success")

        except mysql.connector.Error as e: conn.rollback(); print(f"Error DB al eliminar producto: {e}"); flash("Ocurrió un error al eliminar el producto.", "danger")
        finally:
             if 'cursor' in locals() and cursor is not None: cursor.close()
             if conn is not None: conn.close()
    else: flash("Error de conexión a la base de datos al intentar eliminar.", "danger")

    return redirect(url_for('products'))


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if not is_logged_in():
         flash('Debes iniciar sesión para ver los detalles del producto.', 'warning')
         return redirect(url_for('login'))

    conn = get_db_connection()
    product = None
    error = None

    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT p.id, p.name, p.description, p.price, p.stock, p.is_active,
                   p.image_filename, p.category_id, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
            """
            cursor.execute(query, (product_id,))
            product = cursor.fetchone()

            if product is None:
                flash("Producto no encontrado.", "warning")
                return redirect(url_for('products_for_customer'))

            if is_customer() and (not product['is_active'] or product['stock'] <= 0):
                 flash("Este producto no está disponible actualmente.", "warning")
                 return redirect(url_for('products_for_customer'))

        except mysql.connector.Error as e: print(f"Error DB obtener detalle producto: {e}"); error = "Error al cargar los detalles del producto."; flash(error, "danger")
        finally:
             if 'cursor' in locals() and cursor is not None: cursor.close()
             if conn is not None: conn.close()
    else: error = "Error de conexión a la base de datos."; flash(error, "danger")

    return render_template('product_detail.html', product=product, user_role=get_user_role(), is_logged_in=is_logged_in(), error=error)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if not is_logged_in():
         flash('Debes iniciar sesión para añadir productos al carrito.', 'warning')
         return redirect(url_for('login'))

    quantity = request.form.get('quantity', type=int, default=1)

    if quantity <= 0:
        flash("La cantidad debe ser al menos 1.", "warning")
        return redirect(request.referrer or url_for('products_for_customer'))


    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT stock, is_active FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if result:
                available_stock = result[0]
                is_active = result[1]
                cursor.close()
                conn.close()

                if not is_active:
                    flash("Este producto no está disponible actualmente.", "warning")
                    return redirect(request.referrer or url_for('products_for_customer'))

                cart = session.get('cart', {})
                current_quantity_in_cart = cart.get(str(product_id), 0)

                if current_quantity_in_cart + quantity > available_stock:
                     flash(f"Solo quedan {available_stock} unidades de este producto. No se pudo añadir {quantity} más.", "warning")
                     return redirect(request.referrer or url_for('product_detail', product_id=product_id))

            else:
                 flash("Producto no válido.", "danger")
                 if 'cursor' in locals() and cursor is not None: cursor.close()
                 if conn is not None: conn.close()
                 return redirect(url_for('products_for_customer'))

        except mysql.connector.Error as e:
             print(f"Error DB verificar stock al añadir al carrito: {e}")
             flash("Error al verificar el stock del producto.", "danger")
             if 'cursor' in locals() and cursor is not None: cursor.close()
             if conn is not None: conn.close()
             return redirect(request.referrer or url_for('product_detail', product_id=product_id))

    else:
         flash("Error de conexión a la base de datos.", "danger")
         return redirect(request.referrer or url_for('product_detail', product_id=product_id))

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity

    session['cart'] = cart
    session.modified = True

    print(f"Producto {product_id} añadido al carrito. Carrito actual: {session['cart']}")

    flash(f"Producto(s) añadido(s) al carrito!", "success")
    return redirect(request.referrer or url_for('view_cart'))


@app.route('/cart')
def view_cart():
     if not is_logged_in():
          flash('Debes iniciar sesión para ver tu carrito.', 'warning')
          return redirect(url_for('login'))

     cart = session.get('cart', {})
     cart_items = []
     total_price = 0

     if cart:
         product_ids = list(cart.keys())
         product_ids_int = [int(pid) for pid in product_ids]

         conn = get_db_connection()
         if conn:
             cursor = conn.cursor(dictionary=True)
             placeholders = ','.join(['%s'] * len(product_ids_int))
             query = f"SELECT id, name, price, image_filename, stock, is_active FROM products WHERE id IN ({placeholders})"
             try:
                 cursor.execute(query, product_ids_int)
                 products_in_cart_details = {product['id']: product for product in cursor.fetchall()}

                 items_to_remove = []

                 for product_id_str, quantity in list(cart.items()):
                     product_id = int(product_id_str)

                     if product_id in products_in_cart_details:
                         product = products_in_cart_details[product_id]
                         if not product['is_active']:
                             flash(f"'{product['name']}' ya no está disponible y será eliminado de tu carrito.", "warning")
                             items_to_remove.append(product_id_str)
                         elif product['stock'] < quantity:
                             if product['stock'] > 0:
                                 flash(f"La cantidad de '{product['name']}' ha sido ajustada a {product['stock']} debido a stock limitado.", "info")
                                 cart[product_id_str] = product['stock']
                                 session.modified = True
                                 item_total = product['price'] * product['stock']
                                 cart_items.append({'product': product, 'quantity': product['stock'], 'item_total': item_total})
                                 total_price += item_total
                             else:
                                 flash(f"'{product['name']}' no tiene stock disponible y será eliminado de tu carrito.", "warning")
                                 items_to_remove.append(product_id_str)

                         else:
                             item_total = product['price'] * quantity
                             cart_items.append({'product': product, 'quantity': quantity, 'item_total': item_total})
                             total_price += item_total

                     else:
                          flash(f"Un producto en tu carrito ya no existe y será eliminado.", "warning")
                          items_to_remove.append(product_id_str)

                 for product_id_str in items_to_remove:
                     if product_id_str in cart:
                         cart.pop(product_id_str)

                 if items_to_remove:
                      session['cart'] = cart
                      session.modified = True


             except mysql.connector.Error as e:
                 print(f"Error DB obtener items carrito: {e}")
                 flash("Error al cargar el carrito.", "danger")
             finally:
                 if 'cursor' in locals() and cursor is not None: cursor.close()
                 if conn is not None: conn.close()
         else:
             flash("Error de conexión a la base de datos al cargar el carrito.", "danger")

     return render_template('cart.html', cart_items=cart_items, total_price=total_price, user_role=get_user_role(), is_logged_in=is_logged_in(), user_id=session.get('user_id'))


@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
     if not is_logged_in():
         flash('Debes iniciar sesión para actualizar tu carrito.', 'warning')
         return redirect(url_for('login'))

     quantity = request.form.get('quantity', type=int)

     cart = session.get('cart', {})

     if quantity is not None and quantity >= 0:
         if quantity > 0:
              conn = get_db_connection()
              if conn:
                   cursor = conn.cursor()
                   try:
                        cursor.execute("SELECT stock, is_active FROM products WHERE id = %s", (product_id,))
                        result = cursor.fetchone()
                        if result:
                             available_stock = result[0]
                             is_active = result[1]
                             cursor.close()
                             conn.close()

                             if not is_active:
                                  flash("Este producto ya no está disponible y será eliminado de tu carrito.", "warning")
                                  if str(product_id) in cart: cart.pop(str(product_id))
                                  session['cart'] = cart
                                  session.modified = True
                                  return redirect(url_for('view_cart'))

                             if quantity > available_stock:
                                  flash(f"Solo quedan {available_stock} unidades disponibles. No se pudo actualizar a {quantity}.", "warning")
                                  return redirect(url_for('view_cart'))

                        else:
                             flash("Producto no válido y será eliminado de tu carrito.", "danger")
                             if str(product_id) in cart: cart.pop(str(product_id))
                             session['cart'] = cart
                             session.modified = True
                             if 'cursor' in locals() and cursor is not None: cursor.close()
                             if conn is not None: conn.close()
                             return redirect(url_for('view_cart'))

                   except mysql.connector.Error as e:
                        print(f"Error DB verificar stock para actualizar carrito: {e}")
                        flash("Error al verificar stock para actualizar.", "danger")
                        if 'cursor' in locals() and cursor is not None: cursor.close()
                        if conn is not None: conn.close()
                        return redirect(url_for('view_cart'))
              else:
                   flash("Error de conexión a la base de datos al actualizar carrito.", "danger")
                   return redirect(url_for('view_cart'))

         if quantity > 0:
             cart[str(product_id)] = quantity
             flash("Cantidad actualizada.", "info")
         elif quantity == 0:
             cart.pop(str(product_id), None)
             flash("Producto eliminado del carrito.", "warning")

         session['cart'] = cart
         session.modified = True

     else:
         flash("Cantidad no válida.", "warning")

     return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
     if not is_logged_in():
         flash('Debes iniciar sesión para modificar tu carrito.', 'warning')
         return redirect(url_for('login'))

     cart = session.get('cart', {})

     if str(product_id) in cart:
         cart.pop(str(product_id), None)
         session['cart'] = cart
         session.modified = True
         flash("Producto eliminado del carrito.", "warning")
     else:
         flash("El producto no se encontró en tu carrito.", "info")

     return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
     if not is_customer():
         flash('Debes iniciar sesión como cliente para finalizar la compra.', 'warning')
         return redirect(url_for('login'))

     user_id = session.get('user_id')
     cart = session.get('cart', {})

     if not cart:
         flash("Tu carrito está vacío.", "warning")
         return redirect(url_for('products_for_customer'))

     conn = get_db_connection()
     if not conn:
         flash("Error de conexión a la base de datos al procesar el checkout.", "danger")
         return redirect(url_for('view_cart'))

     cursor = conn.cursor(dictionary=True)

     try:
         product_ids_str = list(cart.keys())
         product_ids_int = [int(pid) for pid in product_ids_str]

         placeholders = ','.join(['%s'] * len(product_ids_int))
         query = f"SELECT id, name, price, stock, is_active FROM products WHERE id IN ({placeholders})"
         cursor.execute(query, product_ids_int)
         products_details = {product['id']: product for product in cursor.fetchall()}

         order_items_to_process = []
         total_amount = 0
         stock_errors = []

         for product_id_str, quantity in cart.items():
             product_id = int(product_id_str)

             if product_id in products_details:
                 product = products_details[product_id]
                 if not product['is_active']:
                     stock_errors.append(f"'{product['name']}' ya no está disponible.")
                 elif product['stock'] < quantity:
                      stock_errors.append(f"Stock insuficiente para '{product['name']}'. Solo quedan {product['stock']} unidades.")
                 else:
                     order_items_to_process.append({
                         'product_id': product_id,
                         'quantity': quantity,
                         'price_at_purchase': product['price']
                     })
                     total_amount += product['price'] * quantity

             else:
                 stock_errors.append(f"Un producto en tu carrito (ID: {product_id}) no se encontró o ya no existe.")


         if stock_errors:
             conn.rollback()
             flash("No se pudo completar la compra debido a los siguientes problemas de stock:", "danger")
             for error_msg in stock_errors:
                  flash(f"- {error_msg}", "danger")
             return redirect(url_for('view_cart'))


         conn.start_transaction()

         try:
             payment_successful = True

             if not payment_successful:
                  raise Exception("El pago no se pudo procesar.")

             insert_order_query = "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s)"
             order_values = (user_id, total_amount, 'Processing')
             cursor.execute(insert_order_query, order_values)
             order_id = cursor.lastrowid

             update_stock_query = "UPDATE products SET stock = stock - %s WHERE id = %s"
             insert_order_item_query = "INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (%s, %s, %s, %s)"

             for item in order_items_to_process:
                 order_item_values = (order_id, item['product_id'], item['quantity'], item['price_at_purchase'])
                 cursor.execute(insert_order_item_query, order_item_values)

                 stock_update_values = (item['quantity'], item['product_id'])
                 cursor.execute(update_stock_query, stock_update_values)

             conn.commit()

             session.pop('cart', None)
             session.modified = True

             print(f"Pedido {order_id} procesado exitosamente para el usuario {user_id}. Total: {total_amount}")
             flash(f"¡Tu pedido ha sido procesado con éxito! Número de pedido: {order_id}", "success")

             return redirect(url_for('order_confirmation', order_id=order_id))

         except Exception as e:
             conn.rollback()
             print(f"Error durante el procesamiento del checkout: {e}")
             flash("Ocurrió un error al procesar tu pedido. Por favor, inténtalo de nuevo.", "danger")
             return redirect(url_for('view_cart'))

     except mysql.connector.Error as e:
          print(f"Error de conexión a la base de datos al iniciar checkout: {e}")
          flash("Error de conexión a la base de datos al procesar el checkout.", "danger")
          return redirect(url_for('view_cart'))

     finally:
          if 'cursor' in locals() and cursor is not None: cursor.close()
          if conn is not None: conn.close()


@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if not is_logged_in():
         flash('Debes iniciar sesión para ver la confirmación de tu pedido.', 'warning')
         return redirect(url_for('login'))

    conn = get_db_connection()
    order = None
    order_items_list = []
    error = None

    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query_order = "SELECT id, total_amount, order_date, status, user_id FROM orders WHERE id = %s"
            cursor.execute(query_order, (order_id,))
            order = cursor.fetchone()

            if order is None:
                 flash("Pedido no encontrado.", "warning")
                 return redirect(url_for('index'))

            if not is_admin() and order['user_id'] != session.get('user_id'):
                 flash("No tienes permiso para ver este pedido.", "danger")
                 return redirect(url_for('index'))

            query_items = """
            SELECT oi.quantity, oi.price_at_purchase, p.name, p.image_filename
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
            """
            cursor.execute(query_items, (order_id,))
            order_items_list = cursor.fetchall()

        except mysql.connector.Error as e: print(f"Error DB obtener detalles de pedido para confirmación: {e}"); error = "Error al cargar los detalles de tu pedido."; flash(error, "danger")
        finally:
             if 'cursor' in locals() and cursor is not None: cursor.close()
             if conn is not None: conn.close()
    else: error = "Error de conexión a la base de datos."; flash(error, "danger")

    return render_template('order_confirmation.html', order=order, order_items=order_items_list, user_role=get_user_role(), is_logged_in=is_logged_in(), error=error)

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html', user_role=get_user_role(), is_logged_in=is_logged_in())


if __name__ == '__main__':
    app.run(debug=True)
