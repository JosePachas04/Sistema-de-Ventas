from flask import session
from functools import wraps
from flask import flash, redirect, url_for

def is_logged_in():
    return 'user_id' in session

def get_user_role():
    return session.get('user_role')

def is_admin():
    return is_logged_in() and get_user_role() == 'admin'

def is_customer():
     return is_logged_in() and get_user_role() == 'customer'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Acceso denegado. Se requiere rol de administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_customer():
            flash('Debes iniciar sesión como cliente para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function