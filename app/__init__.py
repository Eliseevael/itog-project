from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask import redirect, url_for
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Регистрация blueprint'ов внутри функции
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.equipment_routes import equipment_bp
    app.register_blueprint(equipment_bp)

    # Можно добавить остальные маршруты позже
    # from .routes.equipment_routes import equipment_bp
    # app.register_blueprint(equipment_bp)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.route('/')
    def index():
        return redirect(url_for('equipment.index'))

    return app
