from flask import Flask
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
    )
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'products')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        from .routes import main, auth, products, admin, cart, chatbot
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(products.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(cart.bp)
        app.register_blueprint(chatbot.bp)

        from . import context_processors
        
    return app
