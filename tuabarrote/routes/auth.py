from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from ..services.db_service import get_db_connection
from ..services.auth_service import is_logged_in, is_admin
import re
import mysql.connector

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('admin.dashboard')) if is_admin() else redirect(url_for('products.products_for_customer'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        conn = get_db_connection()
        if not conn:
            flash("Error de conexión.", "danger")
            return render_template('login.html', error="Error de conexión.", username=username)

        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user is None or not check_password_hash(user['password'], password):
                    error = 'Usuario o contraseña incorrectos.'
                else:
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_role'] = user['role']
                    flash('Inicio de sesión exitoso!', 'success')
                    if user['role'] == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    else:
                        return redirect(url_for('products.products_for_customer'))
        except mysql.connector.Error as e:
            error = 'Ocurrió un error al intentar iniciar sesión.'
            print(f"Error DB login: {e}")
        finally:
            if conn.is_connected():
                conn.close()
        
        flash(error, 'danger')
        return render_template('login.html', error=error, username=username)

    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        error = None
        
        if not username or not email or not password or not confirm_password:
            error = 'Todos los campos son obligatorios.'
        elif password != confirm_password:
            error = 'Las contraseñas no coinciden.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            error = 'Formato de correo electrónico inválido.'

        if error:
            flash(error, 'danger')
            return render_template('register.html', error=error, username=username, email=email)

        conn = get_db_connection()
        if not conn:
             flash('Error de conexión con el servidor.', 'danger')
             return render_template('register.html', username=username, email=email)
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    error = 'El nombre de usuario o email ya están registrados.'
                else:
                    hashed_password = generate_password_hash(password)
                    cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'customer')",
                                   (username, email, hashed_password))
                    conn.commit()
                    flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
                    return redirect(url_for('auth.login'))
        except mysql.connector.Error as e:
            error = "Error al registrar el usuario."
            print(f"Error DB register: {e}")
        finally:
            if conn.is_connected():
                conn.close()

        flash(error, 'danger')
        return render_template('register.html', error=error, username=username, email=email)
        
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('main.index'))
