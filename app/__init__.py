from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)


    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.route('/')
    def index():
        return 'Приложение запущено!'

    return app
