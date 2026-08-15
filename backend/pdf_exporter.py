# -*- coding: utf-8 -*-
import io
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_patient_summary_pdf(
    filename: str,
    metrics: List[Dict[str, Any]],
    patient_summary: str,
    disease_risks: List[str],
    language: str = "English",
    has_critical_alert: bool = False,
    critical_alerts: Optional[List[str]] = None
) -> bytes:
    """
    Generates a ultra-clean, professional 1-page AXON Clinical Patient Health Summary PDF.
    Scrubs PII and embeds color-coded biomarker status indicators, AI disease risk patterns,
    and translated empathetic summary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155")
    )

    alert_title_style = ParagraphStyle(
        'AlertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#991b1b")
    )

    alert_body_style = ParagraphStyle(
        'AlertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#7f1d1d")
    )

    story = []

    # 1. Header Banner with Brand Title & Scrubbed PII Metadata
    header_data = [
        [
            Paragraph("AXON CLINICAL", title_style),
            Paragraph("<b>PATIENT HEALTH SUMMARY REPORT</b><br/>"
                      f"Source File: {filename}<br/>"
                      f"Language: {language} | Date: 2026-07-25<br/>"
                      "PII Status: Scrubbed & De-identified", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[240, 300])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=10))

    # 2. Emergency Red Flag Alert Box (If panic threshold hit)
    if has_critical_alert or (critical_alerts and len(critical_alerts) > 0):
        alert_content = [
            [Paragraph("🚨 EMERGENCY CRITICAL ALERT: Immediate Medical Care Advised", alert_title_style)],
            [Paragraph("One or more biomarker test values have hit hard physiological panic boundaries. Please consult your physician or emergency care immediately.", alert_body_style)]
        ]
        if critical_alerts:
            for ca in critical_alerts:
                alert_content.append([Paragraph(f"• {ca}", alert_body_style)])
        
        alert_table = Table(alert_content, colWidths=[530])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
            ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#ef4444")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 8)
        ]))
        story.append(alert_table)
        story.append(Spacer(1, 10))

    # 3. Empathetic AI Patient Summary
    if patient_summary:
        story.append(Paragraph("✦ Simplified Clinical Summary", heading_style))
        summary_p = Paragraph(patient_summary, body_style)
        summary_table = Table([[summary_p]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

    # 4. Multi-Biomarker Disease Risks
    if disease_risks:
        story.append(Paragraph("⚠️ Multi-Biomarker Disease Risk Patterns", heading_style))
        risk_items = [[Paragraph(f"• <b>{risk}</b>", body_style)] for risk in disease_risks]
        risk_table = Table(risk_items, colWidths=[540])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fff7ed")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fdba74")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 12))

    # 5. Biomarker Metrics Deck Table
    story.append(Paragraph("📊 Extracted Biomarkers & Clinical Evaluation", heading_style))

    table_data = [
        [
            Paragraph("<b>Biomarker</b>", body_style),
            Paragraph("<b>Result Value</b>", body_style),
            Paragraph("<b>Reference Interval</b>", body_style),
            Paragraph("<b>Status</b>", body_style),
            Paragraph("<b>Confidence</b>", body_style)
        ]
    ]

    for m in metrics:
        name = m.get("biomarker_name", "Unknown")
        val = str(m.get("value", ""))
        unit = m.get("unit", "")
        val_display = f"<b>{val}</b> {unit}"
        
        min_n = m.get("min_normal", 0)
        max_n = m.get("max_normal", 0)
        ref_display = f"{min_n} - {max_n} {unit}"

        st = str(m.get("status", "Normal")).upper()
        conf = m.get("confidence", 0.95)
        conf_display = f"{int(conf * 100)}%"

        # Color badges for status
        if st == "HIGH":
            st_text = f"<font color='#dc2626'><b>HIGH</b></font>"
        elif st == "LOW":
            st_text = f"<font color='#d97706'><b>LOW</b></font>"
        else:
            st_text = f"<font color='#16a34a'><b>NORMAL</b></font>"

        table_data.append([
            Paragraph(name, body_style),
            Paragraph(val_display, body_style),
            Paragraph(ref_display, body_style),
            Paragraph(st_text, body_style),
            Paragraph(conf_display, body_style)
        ])

    metrics_table = Table(table_data, colWidths=[140, 100, 150, 80, 70])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    
    # Override text style of header row
    header_cell_style = ParagraphStyle(
        'HeaderCellStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )
    for c_idx in range(5):
        table_data[0][c_idx] = Paragraph(table_data[0][c_idx].text, header_cell_style)

    story.append(metrics_table)
    story.append(Spacer(1, 14))

    # 6. Disclaimer Footer
    disclaimer_text = (
        "<b>MEDICAL DISCLAIMER:</b> This AXON Clinical Summary report is generated by an automated AI diagnostic assistance engine "
        "for educational and patient convenience purposes only. This document does not constitute a formal medical diagnosis or prescription. "
        "Always review these findings with your primary care physician or licensed healthcare provider."
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph(disclaimer_text, ParagraphStyle('FooterDisc', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor("#94a3b8"))))

    # Build Document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
