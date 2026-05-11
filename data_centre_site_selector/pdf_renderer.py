"""
pdf_renderer.py
===============
Renders a ReportDraft (produced by pdf_pipeline.py) to a professional A4 PDF
file using the reportlab Platypus framework.

Layout
------
  Cover page
  Abstract
  1  Introduction
  2  Methodology
  3  Data & Candidate Overview
  4  Results        (figures embedded inline)
  5  Discussion
  6  Conclusions
  References
  Appendix A — Full Ranked Candidates Table
"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .logging_utils import get_logger

logger = get_logger("pdf_renderer")

# ── reportlab imports (all deferred to render_pdf_report so the rest of the
#    package can be imported even if reportlab is absent) ────────────────────

_RL_AVAILABLE: bool | None = None


def _check_reportlab() -> bool:
    global _RL_AVAILABLE
    if _RL_AVAILABLE is None:
        try:
            import reportlab  # noqa: F401
            _RL_AVAILABLE = True
        except ImportError:
            _RL_AVAILABLE = False
    return _RL_AVAILABLE


# ── Colour / style constants ──────────────────────────────────────────────────

_BRAND_BLUE   = "#1a3c5e"
_BRAND_LIGHT  = "#2980b9"
_ACCENT_GREY  = "#5d6d7e"
_TABLE_HEADER = "#1a3c5e"
_TABLE_ROW_A  = "#eaf0fb"
_TABLE_ROW_B  = "#ffffff"
_RED_WARN     = "#c0392b"

_SECTION_TITLES: dict[str, str] = {
    "abstract":      "Abstract",
    "introduction":  "1  Introduction",
    "methodology":   "2  Methodology",
    "data_overview": "3  Data & Candidate Overview",
    "results":       "4  Results",
    "discussion":    "5  Discussion",
    "conclusions":   "6  Conclusions",
}

_SECTION_ORDER = [
    "abstract",
    "introduction",
    "methodology",
    "data_overview",
    "results",
    "discussion",
    "conclusions",
]

# Figure cross-reference tokens that may remain if the refining agent did not
# convert them.  They are cleaned up before rendering.
import re as _re

_FIG_TOKEN_RE = _re.compile(r"\[FIG_(\d+)\]")


def _clean_fig_tokens(text: str) -> str:
    return _FIG_TOKEN_RE.sub(r"Figure \1", text)


# ── Style builder ─────────────────────────────────────────────────────────────

def _build_styles() -> dict[str, Any]:
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib.colors import HexColor

    base   = getSampleStyleSheet()
    brand  = HexColor(_BRAND_BLUE)
    light  = HexColor(_BRAND_LIGHT)
    grey   = HexColor(_ACCENT_GREY)

    def _p(name: str, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, **kw)

    styles: dict[str, Any] = {}

    styles["cover_title"] = _p(
        "cover_title",
        fontSize=28, fontName="Helvetica-Bold",
        textColor=brand, alignment=TA_CENTER, spaceAfter=18,
        leading=34,
    )
    styles["cover_subtitle"] = _p(
        "cover_subtitle",
        fontSize=14, fontName="Helvetica",
        textColor=grey, alignment=TA_CENTER, spaceAfter=8,
        leading=18,
    )
    styles["cover_meta"] = _p(
        "cover_meta",
        fontSize=10, fontName="Helvetica",
        textColor=grey, alignment=TA_CENTER, spaceAfter=4,
    )
    styles["section_heading"] = _p(
        "section_heading",
        fontSize=16, fontName="Helvetica-Bold",
        textColor=brand, spaceBefore=20, spaceAfter=8,
        leading=20,
    )
    styles["subsection_heading"] = _p(
        "subsection_heading",
        fontSize=12, fontName="Helvetica-Bold",
        textColor=light, spaceBefore=12, spaceAfter=5,
        leading=16,
    )
    styles["body"] = _p(
        "body",
        fontSize=10, fontName="Helvetica",
        leading=15, spaceAfter=8,
        alignment=TA_JUSTIFY,
    )
    styles["caption"] = _p(
        "caption",
        fontSize=8.5, fontName="Helvetica-Oblique",
        textColor=grey, spaceAfter=14, spaceBefore=4,
        alignment=TA_CENTER, leading=12,
    )
    styles["figure_label"] = _p(
        "figure_label",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=brand, alignment=TA_CENTER, spaceAfter=2,
    )
    styles["ref_heading"] = _p(
        "ref_heading",
        fontSize=14, fontName="Helvetica-Bold",
        textColor=brand, spaceBefore=24, spaceAfter=10,
    )
    styles["ref_entry"] = _p(
        "ref_entry",
        fontSize=8.5, fontName="Helvetica",
        leading=13, spaceAfter=5,
        leftIndent=18, firstLineIndent=-18,  # hanging indent
    )
    styles["disclaimer"] = _p(
        "disclaimer",
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=grey, spaceBefore=14, spaceAfter=4,
        alignment=TA_CENTER,
    )
    styles["table_header"] = _p(
        "table_header",
        fontSize=8, fontName="Helvetica-Bold",
        textColor=HexColor("#ffffff"), alignment=TA_CENTER,
    )
    styles["table_cell"] = _p(
        "table_cell",
        fontSize=8, fontName="Helvetica",
        alignment=TA_CENTER, leading=10,
    )
    styles["table_cell_left"] = _p(
        "table_cell_left",
        fontSize=8, fontName="Helvetica",
        alignment=TA_LEFT, leading=10,
    )
    return styles


# ── Page template (header / footer) ──────────────────────────────────────────

def _make_page_template(doc: Any, report_date: str) -> Any:
    """Return a PageTemplate with a running header and page-number footer."""
    from reportlab.platypus import Frame
    from reportlab.platypus.doctemplate import PageTemplate
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    brand = HexColor(_BRAND_BLUE)
    grey  = HexColor(_ACCENT_GREY)
    W, H  = doc.pagesize

    def on_page(canvas: Any, doc_: Any) -> None:
        canvas.saveState()
        # Header rule
        canvas.setStrokeColor(brand)
        canvas.setLineWidth(1.2)
        canvas.line(doc_.leftMargin, H - 1.6 * cm,
                    W - doc_.rightMargin, H - 1.6 * cm)
        # Header text
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(grey)
        canvas.drawString(
            doc_.leftMargin, H - 1.35 * cm,
            "Data Centre Site Selection — Technical Report",
        )
        canvas.drawRightString(
            W - doc_.rightMargin, H - 1.35 * cm,
            report_date,
        )
        # Footer rule
        canvas.line(doc_.leftMargin, 1.6 * cm,
                    W - doc_.rightMargin, 1.6 * cm)
        # Footer text
        canvas.drawCentredString(
            W / 2, 1.1 * cm, f"Page {doc_.page}",
        )
        canvas.drawString(
            doc_.leftMargin, 1.1 * cm, "PROTOTYPE — NOT FOR INVESTMENT USE",
        )
        canvas.restoreState()

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
    )
    return PageTemplate(id="running", frames=[frame], onPage=on_page)


# ── Paragraph splitter (handles subsection headings embedded in body text) ───

def _text_to_flowables(
    text: str,
    styles: dict[str, Any],
    section_key: str,
) -> list[Any]:
    """
    Convert raw section text to a list of reportlab Paragraph flowables.
    Lines that look like subheadings (short, no trailing period, preceded by
    a blank line) are rendered in the subsection_heading style.
    """
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import mm

    text = _clean_fig_tokens(text)
    # Escape XML special characters that would break Paragraph
    def _esc(s: str) -> str:
        return (s.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))

    paragraphs = text.split("\n\n")
    flowables: list[Any] = []
    for raw in paragraphs:
        stripped = raw.strip()
        if not stripped:
            flowables.append(Spacer(1, 4 * mm))
            continue

        lines = stripped.split("\n")
        # Detect a subsection heading: single line, ≤60 chars, no trailing "."
        if (
            len(lines) == 1
            and len(stripped) <= 70
            and not stripped.endswith(".")
            and not stripped.startswith("[")
        ):
            flowables.append(Paragraph(_esc(stripped), styles["subsection_heading"]))
        else:
            # Join lines (handle single-newline line wraps in long text)
            joined = " ".join(ln.strip() for ln in lines if ln.strip())
            flowables.append(Paragraph(_esc(joined), styles["body"]))

    return flowables


# ── Ranked table builder ──────────────────────────────────────────────────────

def _build_ranked_table(ranked: pd.DataFrame, top_k: int, styles: dict[str, Any]) -> Any:
    """Build a reportlab Table flowable for the top-k ranked candidates."""
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.colors import HexColor, white

    display_cols = [c for c in [
        "region",
        "overall_score",
        "energy_score_raw",
        "water_score_raw",
        "climate_score_raw",
        "latency_score_raw",
        "resilience_score_raw",
        "land_score_raw",
        "planning_risk_score_raw",
    ] if c in ranked.columns]

    col_labels = {
        "region":                 "Region",
        "overall_score":          "Overall",
        "energy_score_raw":       "Energy",
        "water_score_raw":        "Water",
        "climate_score_raw":      "Climate",
        "latency_score_raw":      "Latency",
        "resilience_score_raw":   "Resilience",
        "land_score_raw":         "Land",
        "planning_risk_score_raw":"Plan Risk",
    }

    header_row = [
        Paragraph(col_labels.get(c, c), styles["table_header"]) for c in display_cols
    ]
    data_rows: list[list[Any]] = [header_row]

    view = ranked.head(top_k)[display_cols].copy()
    for col in display_cols:
        if col != "region":
            view[col] = pd.to_numeric(view[col], errors="coerce").round(2)

    for _, row in view.iterrows():
        cells = []
        for col in display_cols:
            val = row[col]
            val_str = str(val) if col == "region" else (
                f"{float(val):.2f}" if pd.notna(val) else "—"
            )
            style_key = "table_cell_left" if col == "region" else "table_cell"
            cells.append(Paragraph(val_str, styles[style_key]))
        data_rows.append(cells)

    # Column widths (region wider, scores narrower)
    n_score_cols = len(display_cols) - 1
    from reportlab.lib.units import cm
    col_widths = [3.8 * cm] + [1.55 * cm] * n_score_cols

    table = Table(data_rows, colWidths=col_widths, repeatRows=1)

    row_colors: list[tuple] = []
    for i, _ in enumerate(data_rows):
        if i == 0:
            row_colors.append(("BACKGROUND", (0, i), (-1, i), HexColor(_TABLE_HEADER)))
        elif i % 2 == 1:
            row_colors.append(("BACKGROUND", (0, i), (-1, i), HexColor(_TABLE_ROW_A)))
        else:
            row_colors.append(("BACKGROUND", (0, i), (-1, i), HexColor(_TABLE_ROW_B)))

    table.setStyle(TableStyle([
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 0), (-1, 0), HexColor(_TABLE_HEADER)),
        ("TEXTCOLOR",   (0, 0), (-1, 0), white),
        ("GRID",        (0, 0), (-1, -1), 0.3, HexColor("#bdc3c7")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        *row_colors,
    ]))
    return table


# ── Cover page builder ────────────────────────────────────────────────────────

def _build_cover(
    story: list[Any],
    context: Any,           # ReportContext
    styles: dict[str, Any],
) -> None:
    from reportlab.platypus import Paragraph, Spacer, HRFlowable, PageBreak
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor

    brand = HexColor(_BRAND_BLUE)
    grey  = HexColor(_ACCENT_GREY)

    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph(
        "Data Centre Site Selection<br/>Technical Report",
        styles["cover_title"],
    ))
    story.append(HRFlowable(
        width="70%", thickness=2, color=brand,
        spaceAfter=18, spaceBefore=6, hAlign="CENTER",
    ))
    story.append(Spacer(1, 0.4 * cm))

    top = context.ranked.head(1)
    top_region = str(top.iloc[0]["region"]) if len(top) else "N/A"
    top_score  = float(pd.to_numeric(top.iloc[0].get("overall_score", 0), errors="coerce") or 0)

    story.append(Paragraph(
        f"Workload profile: <b>{context.workload.replace('_', ' ').title()}</b>",
        styles["cover_subtitle"],
    ))
    story.append(Paragraph(
        f"Top recommendation: <b>{top_region}</b> &nbsp;({top_score:.2f}/10)",
        styles["cover_subtitle"],
    ))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(f"Generated: {context.generated_at}", styles["cover_meta"]))
    story.append(Paragraph(
        f"Query: &ldquo;{context.query}&rdquo;", styles["cover_meta"]
    ))
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph(
        "PROTOTYPE — This report was produced by an automated multi-agent analysis system "
        "using public open-data sources and heuristic scoring. It is not an investment-grade "
        "site-selection assessment.",
        styles["disclaimer"],
    ))
    story.append(PageBreak())


# ── Main render function ──────────────────────────────────────────────────────

def render_pdf_report(
    draft: Any,                # ReportDraft from pdf_pipeline
    context: Any,              # ReportContext from pdf_pipeline
    output_path: str | None = None,
) -> str:
    """
    Render the final ReportDraft to a PDF file.

    Parameters
    ----------
    draft        : ReportDraft (v4 expected, but any version accepted).
    context      : ReportContext supplying ranked DataFrame and metadata.
    output_path  : Destination path for the PDF; defaults to a temp file.

    Returns
    -------
    str : Absolute path to the written PDF.
    """
    if not _check_reportlab():
        raise ImportError(
            "reportlab is required for PDF generation. "
            "Install it with: pip install reportlab"
        )

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image,
        PageBreak, HRFlowable, KeepTogether,
    )

    if output_path is None:
        tmp = tempfile.mkdtemp(prefix="dcss_pdf_")
        output_path = os.path.join(tmp, "site_selection_report.pdf")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("pdf_renderer: writing PDF to %s", output_path)

    report_date = context.generated_at

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.4 * cm,
        rightMargin=2.4 * cm,
        topMargin=2.6 * cm,
        bottomMargin=2.6 * cm,
        title="Data Centre Site Selection Technical Report",
        author="Automated Multi-Agent Analysis System",
        subject=context.query,
    )

    styles = _build_styles()
    page_tmpl = _make_page_template(doc, report_date)
    doc.addPageTemplates([page_tmpl])

    story: list[Any] = []
    brand = HexColor(_BRAND_BLUE)

    # ── Cover page ────────────────────────────────────────────────────────
    _build_cover(story, context, styles)

    # Build a lookup: plot_id → ReportPlot (for embedding at the right place)
    plot_lookup: dict[str, Any] = {p.plot_id: p for p in draft.plots}

    # ── Sections ──────────────────────────────────────────────────────────
    # Figures are injected after the Results section text.
    for section_key in _SECTION_ORDER:
        title = _SECTION_TITLES.get(section_key, section_key.replace("_", " ").title())
        text  = draft.sections.get(section_key, "")
        if not text:
            continue

        story.append(Paragraph(title, styles["section_heading"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=brand,
            spaceAfter=8, spaceBefore=0,
        ))

        flowables = _text_to_flowables(text, styles, section_key)
        story.extend(flowables)

        # Embed figures immediately after the Results section
        if section_key == "results" and draft.plots:
            story.append(Spacer(1, 6 * mm))
            for plot in draft.plots:
                _embed_figure(story, plot, styles, doc)

        story.append(Spacer(1, 4 * mm))

    # ── References ────────────────────────────────────────────────────────
    if draft.bibliography:
        story.append(PageBreak())
        story.append(Paragraph("References", styles["ref_heading"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=brand,
            spaceAfter=8, spaceBefore=0,
        ))
        for entry in draft.bibliography:
            num  = entry.get("number", "?")
            text = entry.get("text", "")
            story.append(Paragraph(
                f"[{num}] {text}",
                styles["ref_entry"],
            ))

    # ── Appendix: full ranked table ───────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph(
        "Appendix A — Full Ranked Candidates Table",
        styles["section_heading"],
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=brand,
        spaceAfter=8, spaceBefore=0,
    ))
    story.append(Paragraph(
        "The table below shows the full set of evaluation scores for the top candidates. "
        "All scores are on a 0–10 scale. Water and climate scores are heuristic placeholders "
        "pending integration of dedicated datasets.",
        styles["body"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_build_ranked_table(context.ranked, context.top_k, styles))

    # ── Disclaimer footer block ───────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=HexColor(_ACCENT_GREY),
        spaceAfter=4, spaceBefore=0,
    ))
    story.append(Paragraph(
        "This is a hackathon prototype using public open datasets and heuristic scoring. "
        "It is not an investment-grade site-selection tool. Scores marked as heuristic "
        "(water, climate) are placeholders until appropriate datasets are integrated. "
        "This report was generated automatically and has not been reviewed by a human expert.",
        styles["disclaimer"],
    ))

    # ── Build ─────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=lambda c, d: None)
    logger.info("pdf_renderer: PDF successfully written (%d bytes).", Path(output_path).stat().st_size)
    return output_path


# ── Figure embedding helper ───────────────────────────────────────────────────

def _embed_figure(
    story: list[Any],
    plot: Any,          # ReportPlot
    styles: dict[str, Any],
    doc: Any,
) -> None:
    """Embed a single figure (PNG) with its label and caption into the story."""
    from reportlab.platypus import Image, Paragraph, Spacer, KeepTogether
    from reportlab.lib.units import cm, mm

    if not os.path.isfile(plot.path):
        logger.warning("pdf_renderer: figure file not found: %s", plot.path)
        return

    # Scale image to fit within page width with a reasonable max height
    max_w = doc.width * 0.92
    max_h = 8.5 * cm

    try:
        from PIL import Image as PILImage
        with PILImage.open(plot.path) as im:
            img_w, img_h = im.size
    except Exception:
        img_w, img_h = 800, 450

    scale = min(max_w / img_w, max_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    fig_num = plot.plot_id.split("_")[1] if "_" in plot.plot_id else plot.plot_id
    label   = f"Figure {fig_num}: {plot.title}"
    caption = plot.caption or plot.description

    block: list[Any] = [
        Spacer(1, 3 * mm),
        Image(plot.path, width=draw_w, height=draw_h, hAlign="CENTER"),
        Paragraph(label,   styles["figure_label"]),
        Paragraph(caption, styles["caption"]),
        Spacer(1, 4 * mm),
    ]
    story.extend(block)
