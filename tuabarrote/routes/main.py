from flask import Blueprint, redirect, url_for, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('products.products_for_customer'))

@bp.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')
