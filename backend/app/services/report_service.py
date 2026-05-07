from __future__ import annotations

import csv
import datetime
from io import BytesIO, StringIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.piecharts import Pie

# ---------------------------------------------------------------------------
# Design Tokens — "Intelligence Dossier" aesthetic
# ---------------------------------------------------------------------------
_PAPER_BG       = colors.HexColor("#FAFAF7")   # slightly warm off-white
_BORDER_DARK    = colors.HexColor("#1A2332")   # dark navy outer border
_BORDER_MID     = colors.HexColor("#2E4057")   # mid inner border
_ACCENT_RED     = colors.HexColor("#C0392B")   # fire/alert red
_ACCENT_AMBER   = colors.HexColor("#E67E22")   # warning amber
_ACCENT_GREEN   = colors.HexColor("#1E8449")   # nominal green
_HEADER_BG      = colors.HexColor("#1A2332")   # table header bg
_ROW_ALT        = colors.HexColor("#EEF1F5")   # alternating row tint
_TEXT_DARK      = colors.HexColor("#0D1B2A")   # body text
_TEXT_MED       = colors.HexColor("#344055")   # secondary text
_TEXT_LIGHT     = colors.HexColor("#6B7894")   # muted text
_STAMP_RED      = colors.HexColor("#C0392B")
_GOLD           = colors.HexColor("#B7950B")


def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    return {
        "agency": ParagraphStyle(
            "agency",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=_TEXT_LIGHT,
            letterSpacing=2,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=_BORDER_DARK,
            spaceAfter=4,
            leading=26,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=_TEXT_MED,
            spaceAfter=2,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=_BORDER_DARK,
            spaceBefore=14,
            spaceAfter=4,
            borderPad=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            textColor=_TEXT_DARK,
            leading=13,
            spaceAfter=6,
        ),
        "narrative": ParagraphStyle(
            "narrative",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=_TEXT_DARK,
            leading=15,
            spaceAfter=8,
            leftIndent=12,
            rightIndent=12,
            borderColor=_BORDER_MID,
            borderWidth=1,
            borderPad=8,
            backColor=colors.HexColor("#F0F4FA"),
        ),
        "stamp": ParagraphStyle(
            "stamp",
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=_STAMP_RED,
            alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=_TEXT_LIGHT,
            alignment=TA_CENTER,
        ),
        "kv_key": ParagraphStyle(
            "kv_key",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=_TEXT_LIGHT,
            leading=11,
        ),
        "kv_val": ParagraphStyle(
            "kv_val",
            fontName="Helvetica",
            fontSize=9,
            textColor=_TEXT_DARK,
            leading=12,
        ),
    }


# ---------------------------------------------------------------------------
# Page canvas callback — draws double-line paper border on every page
# ---------------------------------------------------------------------------

def _draw_paper_border(canvas, doc):
    """Draws a double-line border to evoke a classified document aesthetic."""
    w, h = letter
    canvas.saveState()

    # Fill entire page with warm paper background
    canvas.setFillColor(_PAPER_BG)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Outer border (thick, dark navy)
    canvas.setStrokeColor(_BORDER_DARK)
    canvas.setLineWidth(3)
    margin = 24
    canvas.rect(margin, margin, w - 2 * margin, h - 2 * margin, fill=0, stroke=1)

    # Inner border (thin, slightly lighter)
    canvas.setStrokeColor(_BORDER_MID)
    canvas.setLineWidth(0.75)
    inner_margin = 30
    canvas.rect(
        inner_margin, inner_margin,
        w - 2 * inner_margin, h - 2 * inner_margin,
        fill=0, stroke=1,
    )

    # Corner marks (classification tick marks)
    canvas.setStrokeColor(_BORDER_DARK)
    canvas.setLineWidth(1.5)
    tick = 10
    for x, y in [(margin, margin), (w - margin, margin), (margin, h - margin), (w - margin, h - margin)]:
        canvas.line(x - tick, y, x + tick, y)
        canvas.line(x, y - tick, x, y + tick)

    # Page number footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_TEXT_LIGHT)
    canvas.drawCentredString(w / 2, margin - 8, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Report Service
# ---------------------------------------------------------------------------

class ReportService:

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------

    def build_csv(
        self,
        *,
        metrics: list[dict[str, Any]],
        repeat_offenders: list[dict[str, Any]],
    ) -> bytes:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Section", "Name", "Value", "Status"])
        for metric in metrics:
            cv = metric.get("current_value")
            writer.writerow([
                "Executive Metric",
                metric.get("metric_name"),
                cv if cv is None else str(cv),
                metric.get("status"),
            ])
        for offender in repeat_offenders:
            writer.writerow([
                "Repeat Offender",
                offender.get("address"),
                offender.get("enforcement_priority"),
                offender.get("enforcement_action"),
            ])
        return buffer.getvalue().encode("utf-8")

    # ------------------------------------------------------------------
    # PDF — "Tactical Intelligence Dossier"
    # ------------------------------------------------------------------

    def build_pdf(
        self,
        *,
        metrics: list[dict[str, Any]],
        repeat_offenders: list[dict[str, Any]],
        ai_narrative: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title="FIRE — Tactical Intelligence Dossier",
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.65 * inch,
        )

        S = _make_styles()
        W = letter[0] - 1.3 * inch   # usable width
        story: list[Any] = []

        # ── Header ────────────────────────────────────────────────────────
        now_str = datetime.datetime.utcnow().strftime("%d %B %Y  %H:%M UTC")
        classification = "RESTRICTED // TACTICAL USE ONLY"

        story += [
            Paragraph("FIRE RISK INTELLIGENCE PLATFORM", S["agency"]),
            Paragraph("Tactical Intelligence Dossier", S["title"]),
            Paragraph(now_str, S["subtitle"]),
            Spacer(1, 4),
            HRFlowable(width=W, thickness=2, color=_BORDER_DARK, spaceAfter=4),
            HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=8),
        ]

        # Metadata KV strip (doc serial + classification)
        kv_data = [[
            Paragraph("SERIAL NO.", S["kv_key"]),
            Paragraph("CLASS.", S["kv_key"]),
            Paragraph("METRICS", S["kv_key"]),
            Paragraph("INCIDENTS", S["kv_key"]),
        ], [
            Paragraph(f"FIRE-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')}", S["kv_val"]),
            Paragraph(classification, S["kv_val"]),
            Paragraph(str(len(metrics)), S["kv_val"]),
            Paragraph(str(len(repeat_offenders)), S["kv_val"]),
        ]]
        kv_table = Table(kv_data, colWidths=[W * 0.18, W * 0.42, W * 0.2, W * 0.2])
        kv_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, _BORDER_MID),
        ]))
        story += [kv_table, Spacer(1, 14)]

        # ── Section 1: AI Executive Interpretation ──────────────────────
        story.append(Paragraph("▌ SECTION I — EXECUTIVE INTERPRETATION", S["section_header"]))
        story.append(HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=6))

        if ai_narrative:
            story.append(Paragraph(ai_narrative, S["narrative"]))
        else:
            story.append(Paragraph(
                "AI narrative unavailable at the time of report generation. "
                "All AI providers were unreachable or rate-limited. "
                "Please refer to Section II for raw metric data.",
                S["narrative"],
            ))
        story.append(Spacer(1, 10))

        # ── Section 2: System Health Infographic (Pie) ───────────────────
        status_counts = {
            "NOMINAL": 0, "WARNING": 0, "CRITICAL": 0, "UNKNOWN": 0,
            "BEHIND": 0, "ON TRACK": 0, "AT RISK": 0, "NOT STARTED": 0,
            "STABLE": 0, "ELEVATED": 0, "DEGRADED": 0,
            "OK": 0,
        }
        for m in metrics:
            st = str(m.get("status", "UNKNOWN")).upper()
            status_counts[st] = status_counts.get(st, 0) + 1

        if any(v > 0 for v in status_counts.values()):
            story.append(Paragraph("▌ SECTION II — SYSTEM HEALTH OVERVIEW", S["section_header"]))
            story.append(HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=6))

            drawing = Drawing(W, 180)
            pie = Pie()
            pie.x = int(W * 0.05)
            pie.y = 20
            pie.width = 140
            pie.height = 140
            color_map = {
                "NOMINAL":  _ACCENT_GREEN,
                "WARNING":  _ACCENT_AMBER,
                "CRITICAL": _ACCENT_RED,
                "UNKNOWN":  colors.HexColor("#7F8C8D"),
                "BEHIND":   _ACCENT_RED,
                "ON TRACK": _ACCENT_GREEN,
                "AT RISK":  _ACCENT_AMBER,
                "NOT STARTED": colors.HexColor("#95A5A6"),
                "STABLE":   _ACCENT_GREEN,
                "ELEVATED": _ACCENT_AMBER,
                "DEGRADED": _ACCENT_RED,
                "OK":       _ACCENT_GREEN,
            }
            data, labels, pie_colors = [], [], []
            for k, v in status_counts.items():
                if v > 0:
                    data.append(v)
                    labels.append(f"{k} ({v})")
                    pie_colors.append(color_map.get(k, colors.HexColor("#95A5A6")))

            pie.data = data
            pie.labels = labels
            for i, pc in enumerate(pie_colors):
                pie.slices[i].fillColor = pc
                pie.slices[i].strokeColor = _PAPER_BG
                pie.slices[i].strokeWidth = 1

            # Legend
            lx = int(W * 0.42)
            drawing.add(String(lx, 155, "Metric Status Distribution", fontName="Helvetica-Bold", fontSize=9, fillColor=_TEXT_DARK))
            ly = 135
            for label, pc in zip(labels, pie_colors):
                rect = Rect(lx, ly - 7, 10, 10, fillColor=pc, strokeColor=_BORDER_MID, strokeWidth=0.5)
                drawing.add(rect)
                drawing.add(String(lx + 14, ly - 5, label, fontName="Helvetica", fontSize=8, fillColor=_TEXT_DARK))
                ly -= 16

            drawing.add(pie)
            story += [drawing, Spacer(1, 10)]

        # ── Section 3: Executive Metrics Table ───────────────────────────
        story.append(Paragraph("▌ SECTION III — EXECUTIVE METRICS", S["section_header"]))
        story.append(HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=6))

        def _status_color(s: str) -> colors.Color:
            su = str(s).upper()
            # Critical/Bad statuses → Red
            if su in ("CRITICAL", "BEHIND", "DEGRADED"): return _ACCENT_RED
            # Warning/At-Risk statuses → Amber
            if su in ("WARNING", "AT RISK", "ELEVATED"): return _ACCENT_AMBER
            # Good/Nominal statuses → Green
            if su in ("NOMINAL", "ON TRACK", "STABLE", "OK"): return _ACCENT_GREEN
            # Unknown/Not Started → Gray
            if su in ("UNKNOWN", "NOT STARTED"): return colors.HexColor("#7F8C8D")
            # Default for any unknown status → Gray
            return colors.HexColor("#95A5A6")

        col_w = [W * 0.46, W * 0.18, W * 0.16, W * 0.2]
        table_data: list[list[Any]] = [[
            Paragraph("METRIC NAME", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
            Paragraph("VALUE", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
            Paragraph("UNIT", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
            Paragraph("STATUS", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
        ]]

        row_styles: list[tuple] = [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D0DC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_PAPER_BG, _ROW_ALT]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]

        for idx, metric in enumerate(metrics[:15]):
            cv = metric.get("current_value")
            cv_s = "—" if cv is None else str(cv)
            unit = metric.get("unit") or ""
            status = str(metric.get("status", "N/A"))
            sc = _status_color(status)
            row = idx + 1

            table_data.append([
                Paragraph(str(metric.get("metric_name", "—")), S["body"]),
                Paragraph(cv_s, S["body"]),
                Paragraph(unit, S["body"]),
                Paragraph(f'<font color="{sc.hexval() if hasattr(sc, "hexval") else "#000"}"><b>{status}</b></font>', S["body"]),
            ])
            row_styles.append(("TEXTCOLOR", (3, row), (3, row), sc))

        metrics_table = Table(table_data, colWidths=col_w, repeatRows=1)
        metrics_table.setStyle(TableStyle(row_styles))
        story += [metrics_table, Spacer(1, 16)]

        # ── Section 4: Priority Incident Locations ────────────────────────
        if repeat_offenders:
            story.append(Paragraph("▌ SECTION IV — PRIORITY INCIDENT LOCATIONS", S["section_header"]))
            story.append(HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=6))

            off_col_w = [W * 0.52, W * 0.16, W * 0.32]
            off_data: list[list[Any]] = [[
                Paragraph("ADDRESS / LOCATION", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
                Paragraph("PRIORITY", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
                Paragraph("ENFORCEMENT ACTION", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
            ]]
            for offender in repeat_offenders[:12]:
                off_data.append([
                    Paragraph(str(offender.get("address", "N/A")), S["body"]),
                    Paragraph(str(offender.get("enforcement_priority", "N/A")), S["body"]),
                    Paragraph(str(offender.get("enforcement_action", "N/A")), S["body"]),
                ])

            off_table = Table(off_data, colWidths=off_col_w, repeatRows=1)
            off_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D0DC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_PAPER_BG, _ROW_ALT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]))
            story += [off_table, Spacer(1, 16)]

        # ── Footer / Classification Banner ───────────────────────────────
        story += [
            HRFlowable(width=W, thickness=0.5, color=_BORDER_MID, spaceAfter=4),
            HRFlowable(width=W, thickness=2, color=_BORDER_DARK, spaceAfter=6),
            Paragraph(
                f"{classification} — FIRE Risk Intelligence Platform — Generated {now_str}",
                S["footer"],
            ),
        ]

        # Build with background border on every page
        doc.build(story, onFirstPage=_draw_paper_border, onLaterPages=_draw_paper_border)
        return buffer.getvalue()
