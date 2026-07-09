OLM_BENCHMARK_MATRIX = {
    "mistral_ocr_api": {
        "name": "Mistral OCR API",
        "scores": {
            "arxiv": 77.2,
            "old_scans_math": 67.5,
            "tables": 60.6,
            "old_scans": 29.3,
            "headers_footers": 93.6,
            "multi_column": 71.3,
            "long_tiny_text": 77.1,
            "base": 99.4,
            "overall": 72.0
        },
        "std_dev": 1.1,
        "rank": 6
    },
    "marker": {
        "name": "Marker 1.10.1",
        "scores": {
            "arxiv": 83.8,
            "old_scans_math": 66.8,
            "tables": 72.9,
            "old_scans": 33.5,
            "headers_footers": 86.6,
            "multi_column": 80.0,
            "long_tiny_text": 85.7,
            "base": 99.3,
            "overall": 76.1
        },
        "std_dev": 1.1,
        "rank": 5
    },
    "mineru": {
        "name": "MinerU 2.5.4",
        "scores": {
            "arxiv": 76.6,
            "old_scans_math": 54.6,
            "tables": 84.9,
            "old_scans": 33.7,
            "headers_footers": 96.6,
            "multi_column": 78.2,
            "long_tiny_text": 83.5,
            "base": 93.7,
            "overall": 75.2
        },
        "std_dev": 1.1,
        "rank": 7
    },
    "deepseek_ocr": {
        "name": "DeepSeek-OCR",
        "scores": {
            "arxiv": 77.2,
            "old_scans_math": 73.6,
            "tables": 80.2,
            "old_scans": 33.3,
            "headers_footers": 96.1,
            "multi_column": 66.4,
            "long_tiny_text": 79.4,
            "base": 99.8,
            "overall": 75.7
        },
        "std_dev": 1.0,
        "rank": 8
    },
    "nanonets_ocr2": {
        "name": "Nanonets-OCR2-3B",
        "scores": {
            "arxiv": 75.4,
            "old_scans_math": 46.1,
            "tables": 86.8,
            "old_scans": 40.9,
            "headers_footers": 32.1,
            "multi_column": 81.9,
            "long_tiny_text": 93.0,
            "base": 99.6,
            "overall": 69.5
        },
        "std_dev": 1.1,
        "rank": 9
    },
    "paddleocr_vl": {
        "name": "PaddleOCR-VL",
        "scores": {
            "arxiv": 85.7,
            "old_scans_math": 71.0,
            "tables": 84.1,
            "old_scans": 37.8,
            "headers_footers": 97.0,
            "multi_column": 79.9,
            "long_tiny_text": 85.7,
            "base": 98.5,
            "overall": 80.0
        },
        "std_dev": 1.0,
        "rank": 4
    },
    "infinity_parser": {
        "name": "Infinity-Parser 7B",
        "scores": {
            "arxiv": 84.4,
            "old_scans_math": 83.8,
            "tables": 85.0,
            "old_scans": 47.9,
            "headers_footers": 88.7,
            "multi_column": 84.2,
            "long_tiny_text": 86.4,
            "base": 99.8,
            "overall": 82.5
        },
        "std_dev": None,  
        "rank": 2
    },
    "chandra_ocr": {
        "name": "Chandra OCR 0.1.0",
        "scores": {
            "arxiv": 82.2,
            "old_scans_math": 80.3,
            "tables": 88.0,
            "old_scans": 50.4,
            "headers_footers": 90.8,
            "multi_column": 81.2,
            "long_tiny_text": 92.3,
            "base": 99.9,
            "overall": 83.1
        },
        "std_dev": 0.9,
        "rank": 1
    },
    "olmocr": {
        "name": "olmOCR v0.4.0",
        "scores": {
            "arxiv": 83.0,
            "old_scans_math": 82.3,
            "tables": 84.9,
            "old_scans": 47.7,
            "headers_footers": 96.1,
            "multi_column": 83.7,
            "long_tiny_text": 81.9,
            "base": 99.7,
            "overall": 82.4
        },
        "std_dev": 1.1,
        "rank": 3
    }
}

CRITERIA_DESCRIPTIONS = {
    "arxiv": "Documents scientifiques ArXiv (formules mathématiques, graphiques)",
    "old_scans_math": "Anciens documents scannés avec mathématiques",
    "tables": "Tableaux complexes et structures tabulaires",
    "old_scans": "Documents anciens scannés (qualité variable)",
    "headers_footers": "En-têtes et pieds de page",
    "multi_column": "Documents multi-colonnes",
    "long_tiny_text": "Texte long en petite taille",
    "base": "Performance de base (texte standard)",
    "overall": "Score global moyen"
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
    "overall": "Overall"
}


def get_olm_matrix():
    return OLM_BENCHMARK_MATRIX


def get_top_models(n=5, criteria="overall"):
    models = []
    for model_id, data in OLM_BENCHMARK_MATRIX.items():
        score = data["scores"].get(criteria, 0)
        models.append((model_id, data, score))
    
  
    models.sort(key=lambda x: x[2], reverse=True)
    
    return [(m[0], m[1]) for m in models[:n]]


def compare_with_olm_models(model_name):

    local_to_olm = {
        "paddleocr": "paddleocr_vl",
        "docling": None,  
        "easyocr": None,  
        "trocr": None     
    }
    
    olm_equivalent = local_to_olm.get(model_name)
    
    if olm_equivalent and olm_equivalent in OLM_BENCHMARK_MATRIX:
        data = OLM_BENCHMARK_MATRIX[olm_equivalent]
        return {
            "has_olm_data": True,
            "rank": data["rank"],
            "overall_score": data["scores"]["overall"],
            "name": data["name"]
        }
    
    return {
        "has_olm_data": False,
        "message": "Ce modèle n'a pas de données dans olmOCR-Bench"
    }


def get_criteria_description(criteria):
    return CRITERIA_DESCRIPTIONS.get(criteria, "")


def get_criteria_label(criteria):
    return CRITERIA_LABELS.get(criteria, criteria)


def get_model_strengths(model_id):
    if model_id not in OLM_BENCHMARK_MATRIX:
        return []
    
    scores = OLM_BENCHMARK_MATRIX[model_id]["scores"]
    strengths = []
    
    for criteria, score in scores.items():
        if criteria != "overall" and score >= 80:
            strengths.append({
                "criteria": criteria,
                "label": get_criteria_label(criteria),
                "score": score,
                "description": get_criteria_description(criteria)
            })

    strengths.sort(key=lambda x: x["score"], reverse=True)
    
    return strengths


def get_model_weaknesses(model_id):
    if model_id not in OLM_BENCHMARK_MATRIX:
        return []
    
    scores = OLM_BENCHMARK_MATRIX[model_id]["scores"]
    weaknesses = []
    
    for criteria, score in scores.items():
        if criteria != "overall" and score < 60:
            weaknesses.append({
                "criteria": criteria,
                "label": get_criteria_label(criteria),
                "score": score,
                "description": get_criteria_description(criteria)
            })
    

    weaknesses.sort(key=lambda x: x["score"])
    
    return weaknesses
