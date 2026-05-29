"""
PDF safety report generator using ReportLab.

Generates a structured PDF containing:
- Video metadata
- Compliance summary (safety score, violations breakdown)
- Full incident log table (capped at 50 rows)

Entry point: report_generator.generate(video_id, db) → str path or None
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    def generate(self, video_id: int, db) -> Optional[str]:
        """
        Generate a PDF safety report for the given completed video.
        Returns the absolute path to the PDF, or None on failure.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
                HRFlowable,
            )
        except ImportError:
            logger.error("reportlab is not installed; cannot generate PDF.")
            return None

        try:
            from app.config import settings
            from app.models.video import Video
            from app.models.incident import Incident

            video: Optional[Video] = db.get(Video, video_id)
            if not video:
                raise ValueError(f"Video {video_id} not found")

            incidents = (
                db.query(Incident)
                .filter(Incident.video_id == video_id)
                .order_by(Incident.timestamp_seconds)
                .all()
            )

            # ── Output path ───────────────────────────────────────────────────
            reports_dir = Path(settings.reports_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            pdf_path = reports_dir / f"report_{video_id}_{stamp}.pdf"

            # ── Document setup ────────────────────────────────────────────────
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                rightMargin=20 * mm,
                leftMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
            )
            styles = getSampleStyleSheet()

            AMBER  = colors.HexColor("#f59e0b")
            DARK   = colors.HexColor("#0f172a")
            SLATE  = colors.HexColor("#334155")
            LIGHT  = colors.HexColor("#f8fafc")
            GRID   = colors.HexColor("#e2e8f0")

            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                textColor=DARK,
                fontSize=22,
                spaceAfter=4,
            )
            subtitle_style = ParagraphStyle(
                "Subtitle",
                parent=styles["Normal"],
                textColor=colors.HexColor("#64748b"),
                fontSize=10,
                spaceAfter=10,
            )
            section_style = ParagraphStyle(
                "Section",
                parent=styles["Heading2"],
                textColor=DARK,
                fontSize=12,
                spaceAfter=6,
                spaceBefore=12,
            )
            note_style = ParagraphStyle(
                "Note",
                parent=styles["Normal"],
                textColor=colors.grey,
                fontSize=7,
                spaceBefore=3,
            )
            footer_style = ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                textColor=colors.grey,
                fontSize=7,
                alignment=1,
            )

            story = []

            # ── Title ─────────────────────────────────────────────────────────
            story.append(Paragraph("SafeSite AI — Safety Report", title_style))
            story.append(
                Paragraph(
                    f"Generated: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}",
                    subtitle_style,
                )
            )
            story.append(
                HRFlowable(width="100%", thickness=1.5, color=AMBER, spaceAfter=12)
            )

            # ── Video metadata ────────────────────────────────────────────────
            story.append(Paragraph("Video Information", section_style))

            def _fmt_duration(s: Optional[float]) -> str:
                if s is None:
                    return "—"
                m, sec = divmod(int(s), 60)
                return f"{m}m {sec}s"

            meta_rows = [
                ["Filename",    video.filename],
                ["Status",      video.status.value.capitalize()],
                ["Duration",    _fmt_duration(video.duration_seconds)],
                ["FPS",         f"{video.fps:.1f}" if video.fps else "—"],
                ["Frames",      f"{video.total_frames:,}" if video.total_frames else "—"],
                ["Uploaded",    video.created_at.strftime("%B %d, %Y %H:%M UTC")],
                ["Safety Score",
                 f"{video.safety_score:.1f} / 100" if video.safety_score is not None else "—"],
            ]

            meta_tbl = Table(meta_rows, colWidths=[50 * mm, 125 * mm])
            meta_tbl.setStyle(
                TableStyle([
                    ("BACKGROUND",   (0, 0), (0, -1), LIGHT),
                    ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME",     (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE",     (0, 0), (-1, -1), 9),
                    ("GRID",         (0, 0), (-1, -1), 0.5, GRID),
                    ("TOPPADDING",   (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
                    ("LEFTPADDING",  (0, 0), (-1, -1), 6),
                ])
            )
            story.append(meta_tbl)
            story.append(Spacer(1, 8 * mm))

            # ── Compliance summary ────────────────────────────────────────────
            story.append(Paragraph("Compliance Summary", section_style))

            total_i    = len(incidents)
            no_helmet  = sum(1 for i in incidents if i.violation_type.value == "NO_HELMET")
            no_vest    = sum(1 for i in incidents if i.violation_type.value == "NO_VEST")
            high_risk  = sum(
                1 for i in incidents if i.risk_level.value in ("HIGH", "CRITICAL")
            )

            comp_data = [
                ["Metric",                      "Value"],
                ["Total Incidents",             str(total_i)],
                ["No-Helmet Violations",        str(no_helmet)],
                ["No-Vest Violations",          str(no_vest)],
                ["High / Critical Risk",        str(high_risk)],
                ["Safety Score",
                 f"{video.safety_score:.1f} / 100" if video.safety_score is not None else "N/A"],
            ]

            comp_tbl = Table(comp_data, colWidths=[90 * mm, 85 * mm])
            comp_tbl.setStyle(
                TableStyle([
                    ("BACKGROUND",   (0, 0), (-1, 0), AMBER),
                    ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
                    ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE",     (0, 0), (-1, -1), 9),
                    ("GRID",         (0, 0), (-1, -1), 0.5, GRID),
                    ("TOPPADDING",   (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
                    ("LEFTPADDING",  (0, 0), (-1, -1), 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ])
            )
            story.append(comp_tbl)
            story.append(Spacer(1, 8 * mm))

            # ── Incident log ──────────────────────────────────────────────────
            if incidents:
                story.append(
                    Paragraph(f"Incident Log ({total_i} incidents)", section_style)
                )

                RISK_BG = {
                    "LOW":      colors.HexColor("#d1fae5"),
                    "MEDIUM":   colors.HexColor("#fef3c7"),
                    "HIGH":     colors.HexColor("#fee2e2"),
                    "CRITICAL": colors.HexColor("#fecaca"),
                }

                header_row = ["#", "Violation Type", "Risk", "Timestamp", "Worker", "Conf."]
                capped = incidents[:50]
                inc_data = [header_row] + [
                    [
                        str(idx + 1),
                        inc.violation_type.value.replace("_", " ").title(),
                        inc.risk_level.value,
                        f"{inc.timestamp_seconds:.1f}s",
                        str(inc.worker_id) if inc.worker_id else "—",
                        f"{inc.confidence:.0%}" if inc.confidence else "—",
                    ]
                    for idx, inc in enumerate(capped)
                ]

                inc_style = [
                    ("BACKGROUND",   (0, 0), (-1, 0), AMBER),
                    ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
                    ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE",     (0, 0), (-1, -1), 8),
                    ("GRID",         (0, 0), (-1, -1), 0.5, GRID),
                    ("TOPPADDING",   (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
                    ("LEFTPADDING",  (0, 0), (-1, -1), 4),
                ]

                for row_i, inc in enumerate(capped, start=1):
                    bg = RISK_BG.get(inc.risk_level.value, colors.white)
                    inc_style.append(("BACKGROUND", (2, row_i), (2, row_i), bg))

                inc_tbl = Table(
                    inc_data,
                    colWidths=[10 * mm, 47 * mm, 20 * mm, 24 * mm, 18 * mm, 18 * mm],
                )
                inc_tbl.setStyle(TableStyle(inc_style))
                story.append(inc_tbl)

                if len(incidents) > 50:
                    story.append(
                        Paragraph(
                            f"*Showing first 50 of {len(incidents)} incidents.",
                            note_style,
                        )
                    )

            story.append(Spacer(1, 8 * mm))
            story.append(
                HRFlowable(width="100%", thickness=0.5, color=SLATE, spaceAfter=6)
            )
            story.append(
                Paragraph(
                    "Generated by SafeSite AI — AI-powered construction safety monitoring.",
                    footer_style,
                )
            )

            doc.build(story)
            logger.info("PDF report generated: %s", pdf_path)
            return str(pdf_path)

        except Exception as exc:
            logger.error("PDF generation failed for video_id=%s: %s", video_id, exc)
            return None


report_generator = ReportGenerator()
