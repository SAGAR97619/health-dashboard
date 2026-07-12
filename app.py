"""
app.py
Application entry point. Creates the Flask app via an application factory,
registers blueprints, and configures logging and error handling.

Run locally with:
    python app.py

Run in production with:
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

from flask import Flask, jsonify

from config import get_config
from routes.api import api_bp
from routes.views import views_bp
from utils.logger import setup_logger


def create_app() -> Flask:
    """Application factory: builds and configures the Flask app instance."""
    cfg = get_config()

    app = Flask(__name__)
    app.config.from_object(cfg)

    logger = setup_logger(log_file=cfg.LOG_FILE, level=cfg.LOG_LEVEL)
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        app.logger.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    app.logger.info("DevOps Health Dashboard initialized (env=%s)",
                     app.config.get("ENV", "production"))

    return app


app = create_app()

if __name__ == "__main__":
    cfg = get_config()
    # Never run with debug=True and host 0.0.0.0 in production.
    app.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)
