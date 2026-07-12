"""
routes/api.py
REST API blueprint exposing all monitoring data as JSON.
"""

from flask import Blueprint, jsonify, request, send_file
import io

from services.cpu_service import cpu_service
from services.disk_service import disk_service
from services.docker_service import docker_service
from services.health_service import health_service
from services.memory_service import memory_service
from services.network_service import network_service
from services.process_service import process_service
from services.report_service import report_service
from services.system_service import system_service
from utils.logger import logger

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/system")
def get_system():
    return jsonify(system_service.get_system_info())


@api_bp.route("/cpu")
def get_cpu():
    return jsonify(cpu_service.get_cpu_info())


@api_bp.route("/memory")
def get_memory():
    return jsonify(memory_service.get_memory_info())


@api_bp.route("/disk")
def get_disk():
    return jsonify(disk_service.get_disk_info())


@api_bp.route("/network")
def get_network():
    return jsonify(network_service.get_network_info())


@api_bp.route("/docker")
def get_docker():
    return jsonify(docker_service.get_docker_info())


@api_bp.route("/processes")
def get_processes():
    search = request.args.get("search", default=None, type=str)
    limit = request.args.get("limit", default=None, type=int)
    processes = process_service.get_top_processes(limit=limit, search=search)
    return jsonify({"processes": processes, "count": len(processes)})


@api_bp.route("/load")
def get_load():
    data = cpu_service.get_system_load()
    data["temperature"] = cpu_service.get_cpu_temperature()
    return jsonify(data)


@api_bp.route("/summary")
def get_summary():
    return jsonify(health_service.get_summary())


@api_bp.route("/report/pdf")
def get_pdf_report():
    """Generate and stream a PDF snapshot report of current system health."""
    try:
        pdf_bytes = report_service.generate_pdf_report()
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="devops-health-report.pdf",
        )
    except Exception as exc:
        logger.error("PDF report generation failed: %s", exc)
        return jsonify({"error": "Failed to generate PDF report"}), 500


@api_bp.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found"}), 404


@api_bp.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Internal server error"}), 500
