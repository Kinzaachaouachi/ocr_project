from typing import List, Dict, Optional

BENCHMARK_METADATA = {
    "name": "olmOCR-Bench",
    "version": "v1.0",
    "source": "Allen Institute for AI (AI2)",
    "description": "Suite de benchmark complète couvrant plus de 7,000 cas de test sur 1,400 documents pour mesurer la performance des systèmes OCR.",
    "github_url": "https://github.com/allenai/olmocr",
    "huggingface_url": "https://huggingface.co/datasets/allenai/olmOCR-bench",
    "demo_url": "https://olmocr.allenai.org",
    "arxiv_paper_v1": "https://arxiv.org/abs/2502.18443",
    "arxiv_paper_v2": "https://arxiv.org/abs/2510.19817",
    "discord_url": "https://discord.gg/sZq3jTNVNG",
    "license": "Apache 2.0",
    "total_documents": 1403,
    "total_tests": 7010,
    "test_categories": 8,
    "scoring_method": "Pourcentage de réussite des tests unitaires par catégorie, avec moyenne pondérée pour le score global.",
    "last_updated": "2025-10-21",
}

SCORING_METHODOLOGY = {
    "overview": (
        "olmOCR-Bench évalue les systèmes OCR sur 1,403 fichiers PDF réels avec 7,010 tests unitaires "
        "répartis en 8 catégories. Chaque test vérifie si le texte extrait contient ou préserve "
        "correctement un élément spécifique du document original."
    ),
    "categories_detail": (
        "Les catégories couvrent : documents scientifiques ArXiv, formules mathématiques dans les scans anciens, "
        "tableaux complexes, anciens documents scannés, en-têtes/pieds de page, mise en page multi-colonnes, "
        "texte long en petite taille, et texte de base standard."
    ),
    "scoring_formula": (
        "Score par catégorie = (Tests réussis / Tests totaux) × 100. "
        "Le score global (Overall) est la moyenne des scores de toutes les catégories. "
        "L'écart-type (±) est calculé par bootstrap sur les tests."
    ),
    "interpretation": {
        "excellent": "≥ 90% — Performance excellente, production-ready",
        "good": "80-89% — Bonne performance, résultats fiables",
        "acceptable": "60-79% — Performance acceptable, nécessite vérification manuelle",
        "poor": "< 60% — Performance faible, non recommandé pour cette catégorie",
    },
}

OLM_BENCHMARK_MATRIX = {
    "chandra_ocr": {
        "name": "Chandra OCR 0.1.0",
        "version": "0.1.0",
        "is_official": False,
        "note": "Résultats soumis par la communauté (*)",
        "model_type": "Commercial / Propriétaire",
        "scores": {
            "arxiv": 82.2,
            "old_scans_math": 80.3,
            "tables": 88.0,
            "old_scans": 50.4,
            "headers_footers": 90.8,
            "multi_column": 81.2,
            "long_tiny_text": 92.3,
            "base": 99.9,
            "overall": 83.1,
        },
        "std_dev": 0.9,
        "rank": 1,
    },
    "infinity_parser": {
        "name": "Infinity-Parser 7B",
        "version": "7B",
        "is_official": False,
        "note": "Résultats soumis par la communauté (*). Écart-type non communiqué.",
        "model_type": "Open-source / 7B paramètres",
        "scores": {
            "arxiv": 84.4,
            "old_scans_math": 83.8,
            "tables": 85.0,
            "old_scans": 47.9,
            "headers_footers": 88.7,
            "multi_column": 84.2,
            "long_tiny_text": 86.4,
            "base": 99.8,
            "overall": 82.5,
        },
        "std_dev": None,
        "rank": 2,
    },
    "olmocr": {
        "name": "olmOCR v0.4.0",
        "version": "v0.4.0",
        "is_official": True,
        "note": "Modèle phare d'Allen AI. v0.4.0 utilise des données synthétiques et l'entraînement RL.",
        "model_type": "Open-source / 7B paramètres (VLM)",
        "huggingface_model": "allenai/olmOCR-2-7B-1025-FP8",
        "release_date": "2025-10-21",
        "scores": {
            "arxiv": 83.0,
            "old_scans_math": 82.3,
            "tables": 84.9,
            "old_scans": 47.7,
            "headers_footers": 96.1,
            "multi_column": 83.7,
            "long_tiny_text": 81.9,
            "base": 99.7,
            "overall": 82.4,
        },
        "std_dev": 1.1,
        "rank": 3,
    },
    "paddleocr_vl": {
        "name": "PaddleOCR-VL",
        "version": "VL",
        "is_official": False,
        "note": "Résultats soumis par la communauté (*)",
        "model_type": "Open-source",
        "scores": {
            "arxiv": 85.7,
            "old_scans_math": 71.0,
            "tables": 84.1,
            "old_scans": 37.8,
            "headers_footers": 97.0,
            "multi_column": 79.9,
            "long_tiny_text": 85.7,
            "base": 98.5,
            "overall": 80.0,
        },
        "std_dev": 1.0,
        "rank": 4,
    },
    "marker": {
        "name": "Marker 1.10.1",
        "version": "1.10.1",
        "is_official": True,
        "note": "Résultats officiels du benchmark olmOCR-Bench.",
        "model_type": "Open-source",
        "scores": {
            "arxiv": 83.8,
            "old_scans_math": 66.8,
            "tables": 72.9,
            "old_scans": 33.5,
            "headers_footers": 86.6,
            "multi_column": 80.0,
            "long_tiny_text": 85.7,
            "base": 99.3,
            "overall": 76.1,
        },
        "std_dev": 1.1,
        "rank": 5,
    },
    "mistral_ocr_api": {
        "name": "Mistral OCR API",
        "version": "API",
        "is_official": True,
        "note": "Résultats officiels du benchmark olmOCR-Bench.",
        "model_type": "Commercial / API",
        "scores": {
            "arxiv": 77.2,
            "old_scans_math": 67.5,
            "tables": 60.6,
            "old_scans": 29.3,
            "headers_footers": 93.6,
            "multi_column": 71.3,
            "long_tiny_text": 77.1,
            "base": 99.4,
            "overall": 72.0,
        },
        "std_dev": 1.1,
        "rank": 6,
    },
    "mineru": {
        "name": "MinerU 2.5.4",
        "version": "2.5.4",
        "is_official": False,
        "note": "Résultats soumis par la communauté (*)",
        "model_type": "Open-source",
        "scores": {
            "arxiv": 76.6,
            "old_scans_math": 54.6,
            "tables": 84.9,
            "old_scans": 33.7,
            "headers_footers": 96.6,
            "multi_column": 78.2,
            "long_tiny_text": 83.5,
            "base": 93.7,
            "overall": 75.2,
        },
        "std_dev": 1.1,
        "rank": 7,
    },
    "deepseek_ocr": {
        "name": "DeepSeek-OCR",
        "version": "N/A",
        "is_official": True,
        "note": "Résultats officiels du benchmark olmOCR-Bench.",
        "model_type": "Commercial / API",
        "scores": {
            "arxiv": 77.2,
            "old_scans_math": 73.6,
            "tables": 80.2,
            "old_scans": 33.3,
            "headers_footers": 96.1,
            "multi_column": 66.4,
            "long_tiny_text": 79.4,
            "base": 99.8,
            "overall": 75.7,
        },
        "std_dev": 1.0,
        "rank": 8,
    },
    "nanonets_ocr2": {
        "name": "Nanonets-OCR2-3B",
        "version": "3B",
        "is_official": True,
        "note": "Résultats officiels du benchmark olmOCR-Bench.",
        "model_type": "Open-source / 3B paramètres",
        "scores": {
            "arxiv": 75.4,
            "old_scans_math": 46.1,
            "tables": 86.8,
            "old_scans": 40.9,
            "headers_footers": 32.1,
            "multi_column": 81.9,
            "long_tiny_text": 93.0,
            "base": 99.6,
            "overall": 69.5,
        },
        "std_dev": 1.1,
        "rank": 9,
    },
}

CRITERIA_DESCRIPTIONS = {
    "arxiv": "Documents scientifiques ArXiv avec formules mathématiques LaTeX, graphiques, et mise en page académique complexe.",
    "old_scans_math": "Anciens documents scannés contenant des formules mathématiques — teste la capacité à reconnaître les symboles mathématiques dans des images de faible qualité.",
    "tables": "Tableaux complexes et structures tabulaires avec bordures, cellules fusionnées, et alignements variés.",
    "old_scans": "Documents anciens scannés de qualité variable — teste la robustesse face au bruit, aux taches, et à la dégradation du papier.",
    "headers_footers": "En-têtes et pieds de page — teste la capacité à identifier et séparer ces éléments du contenu principal.",
    "multi_column": "Documents multi-colonnes — teste la capacité à maintenir l'ordre de lecture naturel malgré les colonnes.",
    "long_tiny_text": "Texte long en petite taille — teste la capacité à reconnaître du texte fin et dense.",
    "base": "Performance de base sur du texte standard — mesure le plancher de performance minimale attendu.",
    "overall": "Score global moyen pondéré de toutes les catégories — indicateur principal de performance.",
}

CRITERIA_LABELS = {
    "arxiv": "ArXiv",
    "old_scans_math": "Old scans math",
    "tables": "Tables",
    "old_scans": "Old scans",
    "headers_footers": "Headers & footers",
    "multi_column": "Multi column",
    "long_tiny_text": "Long tiny text",
    "base": "Base",
    "overall": "Overall",
}

CRITERIA_ICONS = {
    "arxiv": "📐",
    "old_scans_math": "🔢",
    "tables": "📊",
    "old_scans": "📜",
    "headers_footers": "📋",
    "multi_column": "📰",
    "long_tiny_text": "🔍",
    "base": "📝",
    "overall": "🏆",
}

OLMOCR_CHANGELOG = [
    {
        "version": "v0.4.0",
        "date": "2025-10-21",
        "description": "Nouveau modèle : +4 points de score grâce aux données synthétiques et entraînement RL.",
        "model": "allenai/olmOCR-2-7B-1025-FP8",
    },
    {
        "version": "v0.3.0",
        "date": "2025-08-13",
        "description": "Correction de la détection d'auto-rotation et des hallucinations sur les documents vides.",
        "model": "allenai/olmOCR-7B-0825-FP8",
    },
    {
        "version": "v0.2.1",
        "date": "2025-07-24",
        "description": "+3 points sur olmOCR-Bench. Modèle FP8 par défaut (plus rapide), moins de retries.",
        "model": "allenai/olmOCR-7B-0725-FP8",
    },
    {
        "version": "v0.2.0",
        "date": "2025-07-23",
        "description": "Nouveau code d'entraînement nettoyé pour simplifier l'entraînement de modèles.",
        "model": None,
    },
    {
        "version": "v0.1.75",
        "date": "2025-06-17",
        "description": "Migration de sglang vers vllm. Image Docker mise à jour vers CUDA 12.8.",
        "model": None,
    },
    {
        "version": "v0.1.68",
        "date": "2025-05-19",
        "description": "Lancement d'olmOCR-Bench avec score initial de 77.4. +2 points grâce à des corrections de prompts.",
        "model": None,
    },
    {
        "version": "v0.1.58",
        "date": "2025-02-25",
        "description": "Lancement public initial avec démo en ligne.",
        "model": None,
    },
]

LOCAL_TO_OLM_MAPPING = {
    "PaddleOCR": {
        "olm_id": "paddleocr_vl",
        "similarity": "direct",
        "note": "PaddleOCR-VL est la variante Vision-Language de PaddleOCR, similaire au modèle local.",
    },
    "Docling": {
        "olm_id": "marker",
        "similarity": "similar",
        "note": "Docling et Marker utilisent des architectures similaires de conversion de documents.",
    },
    "EasyOCR": {
        "olm_id": None,
        "similarity": "none",
        "note": "EasyOCR n'a pas d'équivalent direct dans olmOCR-Bench. Les recommandations se basent sur le benchmark global.",
    },
    "TrOCR": {
        "olm_id": None,
        "similarity": "none",
        "note": "TrOCR n'a pas d'équivalent direct dans olmOCR-Bench. Les recommandations se basent sur le benchmark global.",
    },
}


def get_olm_matrix():
    """Return the full OLM benchmark matrix."""
    return OLM_BENCHMARK_MATRIX


def get_benchmark_metadata():
    """Return benchmark metadata."""
    return BENCHMARK_METADATA


def get_scoring_methodology():
    """Return scoring methodology details."""
    return SCORING_METHODOLOGY


def get_changelog():
    """Return olmOCR version history."""
    return OLMOCR_CHANGELOG


def get_top_models(n=5, criteria="overall"):
    """Get top N models sorted by a specific criteria score."""
    models = []
    for model_id, data in OLM_BENCHMARK_MATRIX.items():
        score = data["scores"].get(criteria, 0)
        models.append((model_id, data, score))

    models.sort(key=lambda x: x[2], reverse=True)

    return [(m[0], m[1]) for m in models[:n]]


def compare_with_olm_models(model_name):
    """Compare a local model with its OLM Bench equivalent."""
    mapping = LOCAL_TO_OLM_MAPPING.get(model_name)

    if mapping and mapping["olm_id"] and mapping["olm_id"] in OLM_BENCHMARK_MATRIX:
        data = OLM_BENCHMARK_MATRIX[mapping["olm_id"]]
        return {
            "has_olm_data": True,
            "rank": data["rank"],
            "overall_score": data["scores"]["overall"],
            "name": data["name"],
            "similarity": mapping["similarity"],
            "note": mapping["note"],
            "scores": data["scores"],
        }

    return {
        "has_olm_data": False,
        "similarity": mapping["similarity"] if mapping else "none",
        "note": (
            mapping["note"] if mapping else "Modèle non référencé dans olmOCR-Bench."
        ),
        "message": "Ce modèle n'a pas de données dans olmOCR-Bench",
    }


def get_criteria_description(criteria):
    """Get detailed description for a criteria."""
    return CRITERIA_DESCRIPTIONS.get(criteria, "")


def get_criteria_label(criteria):
    """Get display label for a criteria."""
    return CRITERIA_LABELS.get(criteria, criteria)


def get_criteria_icon(criteria):
    """Get emoji icon for a criteria."""
    return CRITERIA_ICONS.get(criteria, "📊")


def get_model_strengths(model_id):
    """Get the strengths (scores ≥ 80) of a model."""
    if model_id not in OLM_BENCHMARK_MATRIX:
        return []

    scores = OLM_BENCHMARK_MATRIX[model_id]["scores"]
    strengths = []

    for criteria, score in scores.items():
        if criteria != "overall" and score >= 80:
            strengths.append(
                {
                    "criteria": criteria,
                    "label": get_criteria_label(criteria),
                    "icon": get_criteria_icon(criteria),
                    "score": score,
                    "description": get_criteria_description(criteria),
                }
            )

    strengths.sort(key=lambda x: x["score"], reverse=True)

    return strengths


def get_model_weaknesses(model_id):
    """Get the weaknesses (scores < 60) of a model."""
    if model_id not in OLM_BENCHMARK_MATRIX:
        return []

    scores = OLM_BENCHMARK_MATRIX[model_id]["scores"]
    weaknesses = []

    for criteria, score in scores.items():
        if criteria != "overall" and score < 60:
            weaknesses.append(
                {
                    "criteria": criteria,
                    "label": get_criteria_label(criteria),
                    "icon": get_criteria_icon(criteria),
                    "score": score,
                    "description": get_criteria_description(criteria),
                }
            )

    weaknesses.sort(key=lambda x: x["score"])

    return weaknesses


def get_performance_level(score: float) -> Dict:
    """Classify a score into a performance level with color coding."""
    if score >= 90:
        return {
            "level": "Excellent",
            "color": "#059669",
            "badge": "🟢",
            "css_class": "score-excellent",
        }
    elif score >= 80:
        return {
            "level": "Bon",
            "color": "#2563eb",
            "badge": "🔵",
            "css_class": "score-high",
        }
    elif score >= 60:
        return {
            "level": "Acceptable",
            "color": "#d97706",
            "badge": "🟡",
            "css_class": "score-medium",
        }
    else:
        return {
            "level": "Faible",
            "color": "#dc2626",
            "badge": "🔴",
            "css_class": "score-low",
        }


def get_model_recommendations(model_name: str) -> str:
    """
    Get OLM Bench based recommendations for a model.

    Args:
        model_name: Name of the OCR model used locally

    Returns:
        Recommendation text based on OLM Bench data
    """
    mapping = LOCAL_TO_OLM_MAPPING.get(model_name)

    if not mapping:
        return (
            f"Le modèle '{model_name}' n'est pas référencé dans olmOCR-Bench. "
            f"Pour des résultats optimaux, consultez le classement global OLM Bench."
        )

    olm_id = mapping.get("olm_id")

    if not olm_id or olm_id not in OLM_BENCHMARK_MATRIX:

        top_models = get_top_models(n=3, criteria="overall")
        top_names = ", ".join([m[1]["name"] for m in top_models])
        return (
            f"{mapping['note']} "
            f"Les modèles les mieux classés sont : {top_names}. "
            f"Utilisez le rapport OLM Bench pour choisir le modèle le plus adapté à votre type de document."
        )

    model_data = OLM_BENCHMARK_MATRIX[olm_id]
    strengths = get_model_strengths(olm_id)
    weaknesses = get_model_weaknesses(olm_id)
    perf = get_performance_level(model_data["scores"]["overall"])

    std_text = f"±{model_data['std_dev']}" if model_data["std_dev"] else ""
    recommendation = (
        f"Score global OLM Bench : {model_data['scores']['overall']}{std_text} "
        f"(Rang #{model_data['rank']}/9 — {perf['level']}). "
    )

    if mapping["similarity"] == "similar":
        recommendation += f"Note : {mapping['note']} "

    if strengths:
        top_2 = strengths[:2]
        strength_text = ", ".join([f"{s['label']} ({s['score']}%)" for s in top_2])
        recommendation += f"Points forts : {strength_text}. "

    if weaknesses:
        weak_text = ", ".join([f"{w['label']} ({w['score']}%)" for w in weaknesses[:2]])
        recommendation += f"Points faibles : {weak_text}. "

    if model_data["rank"] > 3:
        best = get_best_model_for_criteria("overall")[0]
        recommendation += (
            f"Pour de meilleurs résultats globaux, considérez '{best['name']}' "
            f"(Rang #{best['rank']}, Score {best['scores']['overall']})."
        )

    return recommendation


def get_best_model_for_criteria(criteria: str = "overall", n: int = 1) -> List[Dict]:
    """
    Get the best performing model(s) for a specific criteria.

    Args:
        criteria: Criteria key from CRITERIA_LABELS
        n: Number of top models to return

    Returns:
        List of top n models with their data
    """
    if criteria not in CRITERIA_LABELS:
        criteria = "overall"

    sorted_models = sorted(
        [{"model_id": mid, **data} for mid, data in OLM_BENCHMARK_MATRIX.items()],
        key=lambda x: x["scores"].get(criteria, 0),
        reverse=True,
    )

    return sorted_models[:n]


def get_category_leaders() -> Dict[str, Dict]:
    """
    Get the leading model for each evaluation category.

    Returns:
        Dict mapping category name to best model info
    """
    leaders = {}
    for criteria in CRITERIA_LABELS:
        if criteria != "overall":
            best = get_best_model_for_criteria(criteria, n=1)[0]
            leaders[criteria] = {
                "label": get_criteria_label(criteria),
                "icon": get_criteria_icon(criteria),
                "model_name": best["name"],
                "score": best["scores"][criteria],
                "model_id": best["model_id"],
            }
    return leaders


def get_model_comparison_table() -> List[Dict]:
    """
    Generate a full comparison table sorted by rank.

    Returns:
        List of model dictionaries sorted by rank
    """
    table = []
    for model_id, data in OLM_BENCHMARK_MATRIX.items():
        entry = {
            "model_id": model_id,
            "name": data["name"],
            "version": data["version"],
            "rank": data["rank"],
            "is_official": data["is_official"],
            "note": data["note"],
            "model_type": data["model_type"],
            "scores": data["scores"],
            "std_dev": data["std_dev"],
            "performance": get_performance_level(data["scores"]["overall"]),
            "strengths": get_model_strengths(model_id),
            "weaknesses": get_model_weaknesses(model_id),
        }
        table.append(entry)

    table.sort(key=lambda x: x["rank"])
    return table


def get_score_for_document_type(document_type: str) -> List[Dict]:
    """
    Recommend models based on document type.

    Args:
        document_type: Type of document (e.g., "scientific", "table", "scan", "standard")

    Returns:
        Sorted list of models best suited for this document type
    """
    type_to_criteria = {
        "scientific": "arxiv",
        "math": "old_scans_math",
        "table": "tables",
        "scan": "old_scans",
        "header": "headers_footers",
        "multi_column": "multi_column",
        "small_text": "long_tiny_text",
        "standard": "base",
    }

    criteria = type_to_criteria.get(document_type, "overall")
    return get_best_model_for_criteria(criteria, n=9)
