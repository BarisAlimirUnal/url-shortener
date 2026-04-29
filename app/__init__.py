# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

# Create db and migrate as module-level objects
# so they can be imported anywhere in the app
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Validate all required env vars are present before starting
    Config.validate()

    # Load config into Flask
    app.config.from_object(Config)

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register routes
    from app.routes import bp
    app.register_blueprint(bp)

    return app