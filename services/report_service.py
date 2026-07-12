"""
services/report_service.py
Builds a downloadable PDF system report using reportlab, pulling live data
from the other services.
"""

import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from services.cpu_service import cpu_service
from services.disk_service import disk_service
from services.docker_service import docker_service
from services.memory_service import memory_service
from services.network_service import network_service
from services.process_service import process_service
from services.system_service import system_service
from utils.logger import logger


class ReportService:
    """Generates a PDF snapshot of current system health."""

    def _kv_table(self, data: Dict[str, Any], title: str, styles) -> list:
        elements = [Paragraph(title, styles["Heading2"]), Spacer(1, 0.2 * cm)]
        rows = [[str(k).replace("_", " ").title(), str(v)] for k, v in data.items()
                if not isinstance(v, (dict, list))]
        if rows:
            table = Table(rows, colWidths=[6 * cm, 10 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))
        return elements

    def generate_pdf_report(self) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title="DevOps Health Report")
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#0ea5e9")
        )

        elements = [
            Paragraph("DevOps Health Dashboard — System Report", title_style),
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
            Spacer(1, 0.6 * cm),
        ]

        elements += self._kv_table(system_service.get_system_info(), "System Information", styles)
        elements += self._kv_table(cpu_service.get_cpu_info(), "CPU", styles)
        elements += self._kv_table(memory_service.get_memory_info(), "Memory", styles)
        elements += self._kv_table(disk_service.get_disk_info(), "Disk", styles)
        elements += self._kv_table(network_service.get_network_info(), "Network", styles)
        elements += self._kv_table(docker_service.get_docker_info(), "Docker", styles)

        processes = process_service.get_top_processes()
        elements.append(Paragraph("Top Processes", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * cm))
        proc_rows = [["PID", "Name", "CPU %", "Memory %"]] + [
            [str(p["pid"]), p["name"], str(p["cpu_percent"]), str(p["memory_percent"])]
            for p in processes
        ]
        proc_table = Table(proc_rows, colWidths=[3 * cm, 6 * cm, 3.5 * cm, 3.5 * cm])
        proc_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(proc_table)

        try:
            doc.build(elements)
        except Exception as exc:
            logger.error("Failed to build PDF report: %s", exc)
            raise

        buffer.seek(0)
        return buffer.read()


report_service = ReportService()
