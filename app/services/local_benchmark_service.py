import io
import csv
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.ocr_history import OCRHistory
from ..utils.olm_benchmark_matrix import (
    OLM_BENCHMARK_MATRIX,
    BENCHMARK_METADATA,
    CRITERIA_LABELS,
    CRITERIA_ICONS,
    get_best_model_for_criteria,
    get_model_recommendations,
    get_performance_level,
    get_model_comparison_table,
    compare_with_olm_models,
)


def calculate_user_benchmark_data(db: Session, user_id: int) -> Dict:
    """
    Calculate comprehensive benchmark data for a specific user,
    enriched with OLM Bench global comparison data.
    """

    total_extractions = (
        db.query(OCRHistory).filter(OCRHistory.user_id == user_id).count()
    )

    successful = db.query(OCRHistory).filter(
        OCRHistory.user_id == user_id, OCRHistory.status == "success"
    )

    success_count = successful.count()
    success_rate = (
        round((success_count / total_extractions * 100), 2)
        if total_extractions > 0
        else 0
    )

    model_stats = (
        db.query(
            OCRHistory.model_name,
            func.count(OCRHistory.id).label("total_uses"),
            func.avg(OCRHistory.precision_score).label("avg_precision"),
            func.avg(OCRHistory.ocr_time_s).label("avg_time"),
            func.avg(OCRHistory.robustness).label("avg_robustness"),
            func.avg(OCRHistory.global_score).label("avg_global_score"),
            func.max(OCRHistory.global_score).label("max_score"),
            func.min(OCRHistory.global_score).label("min_score"),
        )
        .filter(OCRHistory.user_id == user_id, OCRHistory.status == "success")
        .group_by(OCRHistory.model_name)
        .all()
    )

    models_performance = []
    for stat in model_stats:
        model_data = {
            "model_name": stat.model_name,
            "total_uses": stat.total_uses,
            "avg_precision": round(float(stat.avg_precision or 0), 2),
            "avg_time": round(float(stat.avg_time or 0), 2),
            "avg_robustness": round(float(stat.avg_robustness or 0), 2),
            "avg_global_score": round(float(stat.avg_global_score or 0), 2),
            "max_score": round(float(stat.max_score or 0), 2),
            "min_score": round(float(stat.min_score or 0), 2),
            "usage_percentage": (
                round((stat.total_uses / success_count * 100), 2)
                if success_count > 0
                else 0
            ),
        }

        model_data["performance_level"] = get_performance_level(
            model_data["avg_global_score"]
        )

        olm_comparison = compare_with_olm_models(stat.model_name)
        model_data["olm_comparison"] = olm_comparison

        model_data["olm_recommendations"] = get_model_recommendations(stat.model_name)

        models_performance.append(model_data)

    models_performance.sort(key=lambda x: x["avg_global_score"], reverse=True)

    best_model = models_performance[0] if models_performance else None

    overall_metrics = successful.with_entities(
        func.avg(OCRHistory.precision_score).label("avg_precision"),
        func.avg(OCRHistory.ocr_time_s).label("avg_time"),
        func.avg(OCRHistory.robustness).label("avg_robustness"),
        func.avg(OCRHistory.global_score).label("avg_global_score"),
    ).first()

    olm_top3 = get_best_model_for_criteria("overall", n=3)
    olm_top3_summary = [
        {"rank": m["rank"], "name": m["name"], "score": m["scores"]["overall"]}
        for m in olm_top3
    ]

    return {
        "generated_at": datetime.now(),
        "user_id": user_id,
        "total_extractions": total_extractions,
        "success_count": success_count,
        "success_rate": success_rate,
        "overall_avg_precision": round(float(overall_metrics.avg_precision or 0), 2),
        "overall_avg_time": round(float(overall_metrics.avg_time or 0), 2),
        "overall_avg_robustness": round(float(overall_metrics.avg_robustness or 0), 2),
        "overall_avg_global_score": round(
            float(overall_metrics.avg_global_score or 0), 2
        ),
        "best_model": best_model,
        "models_performance": models_performance,
        "olm_top3": olm_top3_summary,
        "olm_benchmark_source": BENCHMARK_METADATA["source"],
        "olm_total_models": len(OLM_BENCHMARK_MATRIX),
    }


def generate_csv_report(data: Dict) -> str:
    """Generate CSV report from benchmark data."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Rapport Benchmark Local OCR"])
    writer.writerow([f"Généré le : {data['generated_at'].strftime('%d/%m/%Y %H:%M')}"])
    writer.writerow([])

    writer.writerow(["Statistiques Globales"])
    writer.writerow(["Extractions totales", data["total_extractions"]])
    writer.writerow(["Extractions réussies", data["success_count"]])
    writer.writerow(["Taux de succès (%)", data["success_rate"]])
    writer.writerow(["Précision moyenne (%)", data["overall_avg_precision"]])
    writer.writerow(["Temps moyen (s)", data["overall_avg_time"]])
    writer.writerow(["Robustesse moyenne", data["overall_avg_robustness"]])
    writer.writerow(["Score global moyen", data["overall_avg_global_score"]])
    writer.writerow([])

    writer.writerow(["Performance par Modèle"])
    writer.writerow(
        [
            "Modèle",
            "Utilisations",
            "% Usage",
            "Précision Moy.",
            "Temps Moy. (s)",
            "Robustesse Moy.",
            "Score Global Moy.",
            "Score Max",
            "Score Min",
            "Niveau Performance",
            "Recommandation OLM",
        ]
    )

    for model in data["models_performance"]:
        perf = model.get("performance_level", {})
        writer.writerow(
            [
                model["model_name"],
                model["total_uses"],
                f"{model['usage_percentage']}%",
                f"{model['avg_precision']}%",
                model["avg_time"],
                model["avg_robustness"],
                model["avg_global_score"],
                model["max_score"],
                model["min_score"],
                perf.get("level", "N/A"),
                model.get("olm_recommendations", ""),
            ]
        )

    return output.getvalue()


def generate_excel_report(data: Dict) -> bytes:
    """Generate Excel report from benchmark data with OLM comparison."""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Benchmark Local"

        header_fill = PatternFill(
            start_color="1E3A8A", end_color="1E3A8A", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True, size=11)
        title_font = Font(bold=True, size=14, color="1E3A8A")
        green_font = Font(color="059669", bold=True)
        red_font = Font(color="DC2626", bold=True)
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        ws.merge_cells("A1:I1")
        ws["A1"] = "📊 Rapport Benchmark Local OCR"
        ws["A1"].font = Font(bold=True, size=16, color="1E3A8A")
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:I2")
        ws["A2"] = f"Généré le {data['generated_at'].strftime('%d/%m/%Y à %H:%M')}"
        ws["A2"].alignment = Alignment(horizontal="center")

        row = 4
        ws[f"A{row}"] = "Statistiques Globales"
        ws[f"A{row}"].font = title_font
        ws.merge_cells(f"A{row}:B{row}")

        row += 1
        stats_items = [
            ("Extractions totales", data["total_extractions"]),
            ("Extractions réussies", data["success_count"]),
            ("Taux de succès", f"{data['success_rate']}%"),
            ("Précision moyenne", f"{data['overall_avg_precision']}%"),
            ("Temps moyen", f"{data['overall_avg_time']}s"),
            ("Robustesse moyenne", data["overall_avg_robustness"]),
            ("Score global moyen", data["overall_avg_global_score"]),
        ]

        for label, value in stats_items:
            ws[f"A{row}"] = label
            ws[f"A{row}"].font = Font(bold=True)
            ws[f"B{row}"] = value
            row += 1

        row += 2
        ws[f"A{row}"] = "Performance par Modèle"
        ws[f"A{row}"].font = title_font
        ws.merge_cells(f"A{row}:I{row}")

        row += 1
        headers = [
            "Modèle",
            "Utilisations",
            "% Usage",
            "Précision Moy.",
            "Temps Moy. (s)",
            "Robustesse",
            "Score Global",
            "Score Max",
            "Niveau",
        ]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = border

        for model in data["models_performance"]:
            row += 1
            perf = model.get("performance_level", {})
            ws.cell(row=row, column=1, value=model["model_name"]).border = border
            ws.cell(row=row, column=2, value=model["total_uses"]).border = border
            ws.cell(row=row, column=3, value=f"{model['usage_percentage']}%").border = (
                border
            )
            ws.cell(row=row, column=4, value=f"{model['avg_precision']}%").border = (
                border
            )
            ws.cell(row=row, column=5, value=model["avg_time"]).border = border
            ws.cell(row=row, column=6, value=model["avg_robustness"]).border = border

            score_cell = ws.cell(row=row, column=7, value=model["avg_global_score"])
            score_cell.border = border
            if model["avg_global_score"] >= 80:
                score_cell.font = green_font
            elif model["avg_global_score"] < 60:
                score_cell.font = red_font

            ws.cell(row=row, column=8, value=model["max_score"]).border = border
            ws.cell(row=row, column=9, value=perf.get("level", "N/A")).border = border

        for col, w in {
            "A": 20,
            "B": 14,
            "C": 12,
            "D": 16,
            "E": 14,
            "F": 14,
            "G": 14,
            "H": 12,
            "I": 14,
        }.items():
            ws.column_dimensions[col].width = w

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    except ImportError:
        raise Exception(
            "openpyxl n'est pas installé. Installez-le avec: pip install openpyxl"
        )


def generate_pdf_report(data: Dict) -> bytes:
    """Generate PDF report with OLM Bench comparison and recommendations."""
    try:
        from weasyprint import HTML

        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #333; line-height: 1.6; font-size: 11pt;
        }}
        .header {{
            text-align: center; padding-bottom: 20px;
            border-bottom: 3px solid #1e3a8a; margin-bottom: 30px;
        }}
        .header h1 {{ color: #1e3a8a; margin-bottom: 5px; font-size: 1.8em; }}
        .header p {{ color: #64748b; font-size: 0.9em; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #1e3a8a; border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px; margin-bottom: 15px; font-size: 1.3em;
        }}
        .section h3 {{ color: #334155; font-size: 1.1em; margin: 12px 0 8px; }}
        .stats-grid {{
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 12px; margin-bottom: 20px;
        }}
        .stat-item {{
            background: #f8fafc; padding: 14px; border-radius: 8px;
            border-left: 3px solid #2563eb;
        }}
        .stat-label {{ font-weight: 600; color: #475569; font-size: 0.88em; }}
        .stat-value {{ font-size: 1.4em; color: #1e3a8a; font-weight: 700; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.92em; }}
        th {{
            background: #1e3a8a; color: white; padding: 10px;
            text-align: left; font-size: 0.88em;
        }}
        td {{ padding: 8px 10px; border: 1px solid #e2e8f0; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .best-badge {{
            background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #78350f;
            padding: 2px 8px; border-radius: 10px; font-size: 0.78em; font-weight: 700;
        }}
        .score-excellent {{ color: #059669; font-weight: 700; }}
        .score-good {{ color: #2563eb; font-weight: 600; }}
        .score-medium {{ color: #d97706; }}
        .score-low {{ color: #dc2626; font-weight: 600; }}
        .recommendation {{
            background: #eff6ff; padding: 10px; margin-top: 6px;
            border-radius: 6px; font-size: 0.85em; border-left: 3px solid #2563eb;
        }}
        .olm-ref {{
            background: #f0fdf4; border-left: 3px solid #059669;
            padding: 14px; border-radius: 0 8px 8px 0; margin: 15px 0;
        }}
        .olm-ref h3 {{ color: #166534; margin-bottom: 8px; }}
        .footer {{
            text-align: center; margin-top: 40px; padding-top: 20px;
            border-top: 2px solid #e2e8f0; color: #64748b; font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport Benchmark Local OCR</h1>
        <p>Analyse personnalisée de vos extractions — basée sur olmOCR-Bench</p>
        <p>Généré le {data['generated_at'].strftime('%d/%m/%Y à %H:%M')}</p>
    </div>
"""

        html_content += f"""
    <div class="section">
        <h2>📈 Statistiques Globales</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">Extractions Totales</div>
                <div class="stat-value">{data['total_extractions']}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Taux de Succès</div>
                <div class="stat-value">{data['success_rate']}%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Précision Moyenne</div>
                <div class="stat-value">{data['overall_avg_precision']}%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Score Global Moyen</div>
                <div class="stat-value">{data['overall_avg_global_score']}/100</div>
            </div>
        </div>
    </div>
"""

        if data["best_model"]:
            bm = data["best_model"]
            perf = bm.get("performance_level", {})
            html_content += f"""
    <div class="section">
        <h2>🏆 Meilleur Modèle</h2>
        <p><strong>{bm['model_name']}</strong> — Score moyen : <strong>{bm['avg_global_score']}</strong>/100
        <span class="best-badge">{perf.get('level', '')}</span></p>
        <p>Utilisé {bm['total_uses']} fois ({bm['usage_percentage']}% de vos extractions)</p>
    </div>
"""

        html_content += """
    <div class="section">
        <h2>📊 Performance par Modèle</h2>
        <table>
            <thead>
                <tr>
                    <th>Modèle</th>
                    <th>Utilisations</th>
                    <th>Précision</th>
                    <th>Temps (s)</th>
                    <th>Score Global</th>
                    <th>Niveau</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, model in enumerate(data["models_performance"]):
            badge = '<span class="best-badge">MEILLEUR</span>' if i == 0 else ""
            perf = model.get("performance_level", {})
            score_cls = perf.get("css_class", "")

            html_content += f"""
                <tr>
                    <td>{model['model_name']} {badge}</td>
                    <td>{model['total_uses']} ({model['usage_percentage']}%)</td>
                    <td>{model['avg_precision']}%</td>
                    <td>{model['avg_time']}</td>
                    <td class="{score_cls}"><strong>{model['avg_global_score']}</strong></td>
                    <td>{perf.get('badge', '')} {perf.get('level', '')}</td>
                </tr>
"""

            if model.get("olm_recommendations"):
                html_content += f"""
                <tr>
                    <td colspan="6">
                        <div class="recommendation">
                            <strong>💡 Recommandation OLM Bench :</strong> {model['olm_recommendations']}
                        </div>
                    </td>
                </tr>
"""

            olm_comp = model.get("olm_comparison", {})
            if olm_comp.get("has_olm_data"):
                html_content += f"""
                <tr>
                    <td colspan="6">
                        <div class="recommendation" style="background: #f0fdf4; border-left-color: #059669;">
                            <strong>📊 Comparaison OLM Bench :</strong>
                            Équivalent : {olm_comp['name']} (Rang #{olm_comp['rank']}, Score {olm_comp['overall_score']})
                        </div>
                    </td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p><strong>Rapport généré par OCR Intelligence</strong></p>
        <p>Données de référence : olmOCR-Bench par Allen Institute for AI (AI2)</p>
        <p>Les recommandations sont basées sur la matrice de benchmark global olmOCR-Bench</p>
    </div>
</body>
</html>
"""

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

    except ImportError:
        raise Exception(
            "WeasyPrint n'est pas installé. Installez-le avec: pip install weasyprint"
        )


def generate_word_report(data: Dict) -> bytes:
    """Generate Word document report with OLM Bench comparison."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)

        title = doc.add_heading("Rapport Benchmark Local OCR", 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in title.runs:
            run.font.color.rgb = RGBColor(30, 58, 138)

        subtitle = doc.add_paragraph("Analyse personnalisée — basée sur olmOCR-Bench")
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

        date_para = doc.add_paragraph(
            f'Généré le {data["generated_at"].strftime("%d/%m/%Y à %H:%M")}'
        )
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()

        doc.add_heading("📈 Statistiques Globales", 1)
        doc.add_paragraph(f'Extractions totales : {data["total_extractions"]}')
        doc.add_paragraph(f'Extractions réussies : {data["success_count"]}')
        doc.add_paragraph(f'Taux de succès : {data["success_rate"]}%')
        doc.add_paragraph(f'Précision moyenne : {data["overall_avg_precision"]}%')
        doc.add_paragraph(f'Temps moyen : {data["overall_avg_time"]}s')
        doc.add_paragraph(
            f'Score global moyen : {data["overall_avg_global_score"]}/100'
        )

        doc.add_page_break()

        if data["best_model"]:
            bm = data["best_model"]
            perf = bm.get("performance_level", {})
            doc.add_heading("🏆 Meilleur Modèle", 1)
            doc.add_paragraph(
                f'{bm["model_name"]} — Score moyen : {bm["avg_global_score"]} ({perf.get("level", "")})'
            )
            doc.add_paragraph(
                f'Utilisé {bm["total_uses"]} fois ({bm["usage_percentage"]}% de vos extractions)'
            )

        doc.add_heading("📊 Performance par Modèle", 1)

        table = doc.add_table(rows=1, cols=7)
        table.style = "Light Grid Accent 1"

        headers = [
            "Modèle",
            "Utilisations",
            "% Usage",
            "Précision",
            "Temps (s)",
            "Score Global",
            "Niveau",
        ]
        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = header
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.bold = True
                    run.font.size = Pt(9)

        for model in data["models_performance"]:
            perf = model.get("performance_level", {})
            row = table.add_row()
            row.cells[0].text = model["model_name"]
            row.cells[1].text = str(model["total_uses"])
            row.cells[2].text = f"{model['usage_percentage']}%"
            row.cells[3].text = f"{model['avg_precision']}%"
            row.cells[4].text = str(model["avg_time"])
            row.cells[5].text = str(model["avg_global_score"])
            row.cells[6].text = perf.get("level", "N/A")

            if model.get("olm_recommendations"):
                doc.add_paragraph(
                    f'💡 {model["model_name"]} : {model["olm_recommendations"]}',
                    style="List Bullet",
                )

            olm_comp = model.get("olm_comparison", {})
            if olm_comp.get("has_olm_data"):
                doc.add_paragraph(
                    f'📊 Équivalent OLM : {olm_comp["name"]} (Rang #{olm_comp["rank"]}, Score {olm_comp["overall_score"]})',
                    style="List Bullet",
                )

        doc.add_paragraph()
        footer = doc.add_paragraph(
            "Rapport généré par OCR Intelligence — Données de référence : olmOCR-Bench (AI2)"
        )
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

        output = io.BytesIO()
        doc.save(output)
        return output.getvalue()

    except ImportError:
        raise Exception(
            "python-docx n'est pas installé. Installez-le avec: pip install python-docx"
        )
