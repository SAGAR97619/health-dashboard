"""
routes/views.py
Frontend view routes: the dashboard page and a plain health-check endpoint.
"""

from flask import Blueprint, jsonify, render_template

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@views_bp.route("/health")
def health():
    """Lightweight liveness endpoint for Docker healthchecks / load balancers."""
    return jsonify({"status": "ok"}), 200
