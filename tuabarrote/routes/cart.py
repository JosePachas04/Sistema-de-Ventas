# tuabarrote/routes/cart.py

import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, Response
from weasyprint import HTML
from ..services.db_service import get_db_connection, process_order_transaction
from ..services.auth_service import customer_required

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('/')
@customer_required
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0
    if not cart:
        return render_template('cart.html', cart_items=cart_items, total_price=total_price)

    conn = get_db_connection()
    if not conn:
        return render_template('cart.html', cart_items=[], total_price=0)

    try:
        with conn.cursor(dictionary=True) as cursor:
            product_ids = list(cart.keys())
            if not product_ids:
                return render_template('cart.html', cart_items=[], total_price=0)
                
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"SELECT id, name, price, stock, image_filename, unidad_medida FROM products WHERE id IN ({placeholders})"
            cursor.execute(query, product_ids)
            db_products = {str(p['id']): p for p in cursor.fetchall()}

            for product_id, quantity in cart.items():
                product = db_products.get(product_id)
                if product:
                    item_total = product['price'] * quantity
                    total_price += item_total
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'item_total': item_total
                    })
    finally:
        if conn and conn.is_connected():
            conn.close()

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@bp.route('/add/<int:product_id>', methods=['POST'])
@customer_required
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    pid_str = str(product_id)
    cart[pid_str] = cart.get(pid_str, 0) + quantity
    session['cart'] = cart
    session.modified = True
    flash("Producto añadido al carrito.", "success")
    return redirect(request.referrer or url_for('products.products_for_customer'))

@bp.route('/update/<int:product_id>', methods=['POST'])
@customer_required
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 0))
    cart = session.get('cart', {})
    pid_str = str(product_id)
    if quantity > 0:
        cart[pid_str] = quantity
    elif pid_str in cart:
        del cart[pid_str]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart.view_cart'))

@bp.route('/remove/<int:product_id>', methods=['POST'])
@customer_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    pid_str = str(product_id)
    if pid_str in cart:
        del cart[pid_str]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart.view_cart'))

@bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for('products.products_for_customer'))
    
    if request.method == 'POST':
        user_id = session.get('user_id')
        result = process_order_transaction(user_id, cart)
        
        if result.get('success'):
            order_id = result.get('order_id')
            session.pop('cart', None)
            session.modified = True
            flash(f"¡Pedido #{order_id} realizado con éxito!", "success")
            return redirect(url_for('cart.order_confirmation', order_id=order_id))
        else:
            flash(result.get('error', 'Error desconocido'), "danger")
            return redirect(url_for('cart.view_cart'))

    cart_items = []
    total_price = 0
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            product_ids = list(cart.keys())
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"SELECT id, name, price, stock, image_filename, unidad_medida FROM products WHERE id IN ({placeholders})"
            cursor.execute(query, product_ids)
            db_products = {str(p['id']): p for p in cursor.fetchall()}
            for product_id, quantity in cart.items():
                product = db_products.get(product_id)
                if product:
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'item_total': product['price'] * quantity
                    })
                    total_price += product['price'] * quantity
    finally:
        if conn and conn.is_connected():
            conn.close()
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

@bp.route('/order-confirmation/<int:order_id>')
@customer_required
def order_confirmation(order_id):
    return render_template('order_confirmation.html', order_id=order_id)

@bp.route('/receipt/<int:order_id>')
@customer_required
def generate_receipt(order_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    if not conn:
        flash("Error de conexión.", "danger")
        return redirect(url_for('main.index'))
    
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
            order_data = cursor.fetchone()
            if not order_data:
                flash("Orden no encontrada o no te pertenece.", "warning")
                return redirect(url_for('main.index'))

            cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            customer_data = cursor.fetchone()
            
            query_items = "SELECT oi.*, p.name FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s"
            cursor.execute(query_items, (order_id,))
            order_items_raw = cursor.fetchall()
            
            order_items_data = [{'quantity': i['quantity'], 'price_at_purchase': i['price_at_purchase'], 'product': {'name': i['name']}} for i in order_items_raw]
    finally:
        if conn and conn.is_connected():
            conn.close()

    store_address = os.getenv('DIRECCION_TIENDA', 'Av. Principal 123, Sunampe')
    store_phone = os.getenv('TELEFONO_CONTACTO', '+51 999 888 777')
    
    rendered_html = render_template('receipt_template.html', order=order_data, order_items=order_items_data, customer=customer_data, store_address=store_address, store_phone=store_phone)
    pdf = HTML(string=rendered_html).write_pdf()
    
    return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename=boleta_pedido_{order_id}.pdf'})