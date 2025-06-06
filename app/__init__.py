from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)  # ← обязательно внутри функции, после db.init_app

    # Регистрация blueprint'ов
    from .routes.auth_routes import auth_bp
    from .routes.equipment_routes import equipment_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(equipment_bp)

    # Создание папки для загрузок (если нет)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Главная страница → редирект на оборудование
    @app.route('/')
    def index():
        return redirect(url_for('equipment.index'))

    return app
