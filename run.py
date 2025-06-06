from flask_migrate import Migrate, upgrade
from flask import Flask
from app import create_app, db
from flask.cli import with_appcontext
import click

app = create_app()
migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run(debug=True)
