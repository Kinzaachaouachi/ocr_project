#!/usr/bin/env python

from api.olm_benchmark_matrix import (
    OLM_BENCHMARK_MATRIX,
    CRITERIA_LABELS,
    CRITERIA_DESCRIPTIONS,
    get_top_models,
    get_model_strengths,
    get_model_weaknesses
)

def generate_olm_report_html():

    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>olmOCR-Bench - Matrice de Benchmark Complète</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary: #2563EB; --primary-dark: #1D4ED8; --primary-light: #DBEAFE;
            --secondary: #F8FAFC; --accent: #059669; --text-primary: #0F172A;
            --text-secondary: #475569; --text-muted: #94A3B8; --border: #E2E8F0;
            --surface: #FFFFFF; --success: #059669; --warning: #F59E0B; --error: #DC2626;
            --gold: #F59E0B; --silver: #94A3B8; --bronze: #CD7F32;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--secondary); color: var(--text-primary); min-height: 100vh;
        }
        
        .back-button {
            position: fixed; top: 20px; left: 20px; z-index: 1000;
        }
        .back-button a {
            display: inline-flex; align-items: center; gap: 0.5rem;
            background: var(--primary); color: white; padding: 0.75rem 1.25rem;
            border-radius: 8px; text-decoration: none; font-weight: 600;
            font-size: 0.9rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        .back-button a:hover {
            background: var(--primary-dark); transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(37, 99, 235, 0.3);
        }
        
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563EB 100%);
            padding: 2rem 1.5rem; color: white;
        }
        .header-content {
            max-width: 1600px; margin: 0 auto;
        }
        .header-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
        .header-subtitle { font-size: 1rem; opacity: 0.9; }
        .header-info { margin-top: 1rem; font-size: 0.875rem; opacity: 0.85; }
        
        .container { max-width: 1600px; margin: 0 auto; padding: 2rem 1rem; }
        
        .section {
            background: var(--surface); border-radius: 16px; border: 1px solid var(--border);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 2rem; overflow: hidden;
        }
        .section-header {
            padding: 1.5rem 2rem; border-bottom: 1px solid var(--border);
            background: linear-gradient(to right, var(--primary-light), var(--surface));
        }
        .section-title { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); }
        .section-subtitle { font-size: 0.875rem; color: var(--text-muted); margin-top: 0.25rem; }
        .section-body { padding: 1.5rem 2rem; }
        
        /* Table principale */
        .benchmark-table {
            width: 100%; border-collapse: collapse; font-size: 0.875rem;
        }
        .benchmark-table thead {
            background: linear-gradient(to bottom, var(--secondary), #EEF2FF);
        }
        .benchmark-table th {
            padding: 1rem 0.75rem; text-align: center; font-size: 0.75rem; font-weight: 700;
            color: var(--text-secondary); border-bottom: 2px solid var(--border);
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .benchmark-table th:first-child {
            text-align: left; position: sticky; left: 0; background: inherit; z-index: 10;
        }
        .benchmark-table tbody tr {
            border-bottom: 1px solid var(--border); transition: all 0.2s ease;
        }
        .benchmark-table tbody tr:hover {
            background: linear-gradient(to right, var(--primary-light), var(--secondary));
        }
        .benchmark-table td {
            padding: 1rem 0.75rem; text-align: center;
        }
        .benchmark-table td:first-child {
            text-align: left; font-weight: 600; position: sticky; left: 0;
            background: var(--surface); z-index: 5;
        }
        .benchmark-table tbody tr:hover td:first-child {
            background: linear-gradient(to right, var(--primary-light), var(--secondary));
        }
        
        .rank-badge {
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 50%; font-weight: 700;
            font-size: 0.75rem; margin-right: 0.5rem;
        }
        .rank-1 { background: var(--gold); color: white; }
        .rank-2 { background: var(--silver); color: white; }
        .rank-3 { background: var(--bronze); color: white; }
        .rank-other { background: var(--border); color: var(--text-secondary); }
        
        .score-cell {
            font-weight: 600; font-family: 'SF Mono', Monaco, monospace;
        }
        .score-excellent { color: #059669; background: rgba(5, 150, 105, 0.1); }
        .score-good { color: #10B981; }
        .score-medium { color: #F59E0B; }
        .score-poor { color: #DC2626; }
        .score-overall {
            font-size: 1rem; font-weight: 700; padding: 0.5rem 1rem;
            border-radius: 6px; display: inline-block;
        }
        
        /* Top modèles */
        .top-models {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem;
        }
        @media (max-width: 1024px) { .top-models { grid-template-columns: 1fr; } }
        
        .model-card {
            padding: 1.5rem; border-radius: 12px; border: 2px solid var(--border);
            background: var(--secondary); transition: all 0.3s ease;
        }
        .model-card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
        .model-card.rank-1 { border-color: var(--gold); }
        .model-card.rank-2 { border-color: var(--silver); }
        .model-card.rank-3 { border-color: var(--bronze); }
        
        .model-card-header {
            display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;
        }
        .model-card-title { font-size: 1.1rem; font-weight: 700; }
        .model-card-score {
            font-size: 2rem; font-weight: 800; text-align: center; margin: 1rem 0;
        }
        .model-card.rank-1 .model-card-score { color: var(--gold); }
        .model-card.rank-2 .model-card-score { color: var(--silver); }
        .model-card.rank-3 .model-card-score { color: var(--bronze); }
        
        .strengths-list {
            list-style: none; padding: 0; margin: 0;
        }
        .strengths-list li {
            padding: 0.5rem; margin-bottom: 0.25rem; background: rgba(5, 150, 105, 0.1);
            border-radius: 4px; font-size: 0.75rem; color: var(--text-secondary);
        }
        
        .table-wrapper {
            overflow-x: auto; margin-top: 1rem;
        }
        
        .footer {
            text-align: center; color: var(--text-muted); font-size: 0.8rem;
            margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border);
        }
    </style>
</head>
<body>
    <div class="back-button">
        <a href="/">← Retour à l'extraction</a>
    </div>
    
    <div class="header">
        <div class="header-content">
            <div class="header-title">📊 olmOCR-Bench - Matrice de Benchmark Complète</div>
            <div class="header-subtitle">Benchmark complet couvrant plus de 7,000 cas de test sur 1,400 documents</div>
            <div class="header-info">
                Source: <a href="https://github.com/allenai/olmocr" style="color: white; text-decoration: underline;">olmOCR v0.4.0</a> 
                | 9 systèmes OCR comparés sur 8 critères différents
            </div>
        </div>
    </div>
    
    <div class="container">
"""
    
    html += """
        <div class="section">
            <div class="section-header">
                <div class="section-title">🏆 Top 3 Modèles</div>
                <div class="section-subtitle">Classement selon le score global</div>
            </div>
            <div class="section-body">
                <div class="top-models">
"""
    
    top_3 = get_top_models(n=3)
    for model_id, model_data in top_3:
        rank = model_data["rank"]
        rank_emoji = ["🥇", "🥈", "🥉"][rank - 1]
        strengths = get_model_strengths(model_id)[:3]
        
        html += f"""
                    <div class="model-card rank-{rank}">
                        <div class="model-card-header">
                            <span class="rank-badge rank-{rank}">{rank}</span>
                            <div>
                                <div>{rank_emoji}</div>
                                <div class="model-card-title">{model_data["name"]}</div>
                            </div>
                        </div>
                        <div class="model-card-score">{model_data["scores"]["overall"]}%</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-bottom: 1rem;">
                            Score Global
                        </div>
                        <div style="font-weight: 600; font-size: 0.8rem; margin-bottom: 0.5rem;">Forces principales:</div>
                        <ul class="strengths-list">
"""
        for strength in strengths:
            html += f"""                            <li>{strength["label"]}: {strength["score"]}%</li>\n"""
        
        html += """                        </ul>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
"""

    html += """
        <div class="section">
            <div class="section-header">
                <div class="section-title">📈 Matrice Complète de Benchmark</div>
                <div class="section-subtitle">Scores détaillés par modèle et par critère (sur 100)</div>
            </div>
            <div class="section-body">
                <div class="table-wrapper">
                    <table class="benchmark-table">
                        <thead>
                            <tr>
                                <th>Modèle</th>
"""
    
    criteria_order = ["arxiv", "old_scans_math", "tables", "old_scans", "headers_footers", "multi_column", "long_tiny_text", "base", "overall"]
    for criteria in criteria_order:
        label = CRITERIA_LABELS[criteria]
        html += f"""                                <th title="{CRITERIA_DESCRIPTIONS[criteria]}">{label}</th>\n"""
    
    html += """                            </tr>
                        </thead>
                        <tbody>
"""
   
    models_sorted = sorted(OLM_BENCHMARK_MATRIX.items(), key=lambda x: x[1]["rank"])
    
    for model_id, model_data in models_sorted:
        rank = model_data["rank"]
        rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
        
        html += f"""                            <tr>
                                <td>
                                    <span class="rank-badge {rank_class}">{rank}</span>
                                    {model_data["name"]}
                                </td>
"""
        
        for criteria in criteria_order:
            score = model_data["scores"][criteria]
            
            if score >= 85:
                color_class = "score-excellent"
            elif score >= 70:
                color_class = "score-good"
            elif score >= 50:
                color_class = "score-medium"
            else:
                color_class = "score-poor"
            
            if criteria == "overall":
                std_dev = f" ±{model_data['std_dev']}" if model_data['std_dev'] else ""
                html += f"""                                <td>
                                    <span class="score-cell score-overall {color_class}">{score:.1f}{std_dev}</span>
                                </td>
"""
            else:
                html += f"""                                <td class="score-cell {color_class}">{score:.1f}</td>\n"""
        
        html += """                            </tr>
"""
    
    html += """                        </tbody>
                    </table>
                </div>
            </div>
        </div>
"""
    
    html += """
        <div class="section">
            <div class="section-header">
                <div class="section-title">📖 Description des Critères</div>
                <div class="section-subtitle">Explication de chaque catégorie de test</div>
            </div>
            <div class="section-body">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
"""
    
    for criteria in criteria_order[:-1]: 
        label = CRITERIA_LABELS[criteria]
        desc = CRITERIA_DESCRIPTIONS[criteria]
        html += f"""
                    <div style="padding: 1rem; background: var(--secondary); border-radius: 8px;">
                        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                            {label}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-muted);">
                            {desc}
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>📊 olmOCR-Bench © 2024 - Allen Institute for AI</p>
            <p style="margin-top: 0.5rem;">Données de benchmark complètes pour systèmes OCR</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    html_content = generate_olm_report_html()
    
    with open("olm_benchmark_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✓ Rapport olmOCR-Bench généré: olm_benchmark_report.html")
