

MODEL_MATRIX = {
    "paddleocr": {
        "name": "PaddleOCR",
        "version": "2.7.0",
        "provider": "Baidu",
        "description": "Moteur OCR rapide et précis, optimisé pour la production",
        
       
        "advantages": [
            "Très rapide (1-2s par page)",
            "Excellente précision sur texte imprimé",
            "Support multi-langue (80+ langues)",
            "Détection automatique de l'orientation du texte",
            "Faible consommation mémoire",
            "Idéal pour le traitement en batch"
        ],
        
        
        "disadvantages": [
            "Moins performant sur documents manuscrits",
            "Nécessite des images de bonne qualité",
            "Mise en page complexe parfois approximative"
        ],
        
        
        "scoring": {
            "speed": 95,              
            "accuracy_print": 98,     
            "accuracy_handwritten": 60,  
            "multilanguage": 95,      
            "layout_preservation": 75,  
            "ease_of_use": 90,        
            "memory_usage": 85,       
            "confidence_scores": 90   
        },
      
        "languages": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru"],
        
        "supported_formats": ["image", "pdf"],
        
        "use_cases": [
            "Documents administratifs",
            "Factures et reçus",
            "Cartes d'identité",
            "Plaques d'immatriculation",
            "Documents scannés de qualité"
        ]
    },
    
    "docling": {
        "name": "Docling",
        "version": "2.10.0",
        "provider": "IBM Research",
        "description": "Analyse documentaire native avec extraction structurée en Markdown",
        
        "advantages": [
            "Excellent pour documents structurés (PDF, Word, Excel)",
            "Préservation parfaite de la mise en page",
            "Export en Markdown structuré",
            "Support natif des tableaux et listes",
            "Analyse sémantique du document",
            "Multiformat (PDF, DOCX, XLSX, TXT)"
        ],
        
        "disadvantages": [
            "Plus lent (10-15s par page)",
            "Consommation mémoire élevée",
            "Moins précis sur images de faible qualité",
            "Complexité d'intégration"
        ],
        
        "scoring": {
            "speed": 40,
            "accuracy_print": 96,
            "accuracy_handwritten": 50,
            "multilanguage": 85,
            "layout_preservation": 98,
            "ease_of_use": 85,
            "memory_usage": 60,
            "confidence_scores": 70
        },
        
        "languages": ["fr", "en", "es", "de", "it", "pt", "zh", "ja"],
        
        "supported_formats": ["image", "pdf", "txt", "docx", "xlsx"],
        
        "use_cases": [
            "Documents juridiques",
            "Rapports d'entreprise",
            "Tableaux de données",
            "Fichiers Excel et Word",
            "Archives PDF structurées"
        ]
    },
    
    "easyocr": {
        "name": "EasyOCR",
        "version": "1.7.2",
        "provider": "JaidedAI",
        "description": "OCR basé sur PyTorch, simple et multi-langue",
        
        "advantages": [
            "Très facile à utiliser",
            "Excellente détection multi-langue",
            "Bon équilibre précision/vitesse",
            "Support de 80+ langues",
            "Bonne gestion des textes mélangés",
            "Scores de confiance fiables"
        ],
        
        "disadvantages": [
            "Consommation GPU/CPU élevée",
            "Temps de chargement initial long",
            "Moins précis que PaddleOCR sur certains cas",
            "Nécessite PyTorch (lourd)"
        ],
        
        "scoring": {
            "speed": 70,
            "accuracy_print": 93,
            "accuracy_handwritten": 65,
            "multilanguage": 98,
            "layout_preservation": 70,
            "ease_of_use": 95,
            "memory_usage": 65,
            "confidence_scores": 95
        },
        
        "languages": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru", "th", "vi"],
        
        "supported_formats": ["image", "pdf"],
        
        "use_cases": [
            "Documents multilingues",
            "Prototypage rapide",
            "Textes mélangés (français + arabe)",
            "Scénarios d'apprentissage",
            "Applications mobiles"
        ]
    },
    
    "trocr": {
        "name": "TrOCR",
        "version": "microsoft/trocr-small-printed",
        "provider": "Microsoft Research",
        "description": "Modèle Transformer pour reconnaissance de texte manuscrit et imprimé",
        
        "advantages": [
            "Excellent sur texte manuscrit",
            "Basé sur architecture Transformer (SOTA)",
            "Très précis sur lignes isolées",
            "Gestion des écritures complexes",
            "Bon sur textes dégradés"
        ],
        
        "disadvantages": [
            "Conçu pour lignes isolées uniquement",
            "Nécessite segmentation préalable",
            "Très lent (0.5-1s par ligne)",
            "Pas de détection de mise en page",
            "Consommation mémoire importante"
        ],
        
        "scoring": {
            "speed": 30,
            "accuracy_print": 85,
            "accuracy_handwritten": 92,
            "multilanguage": 70,
            "layout_preservation": 40,
            "ease_of_use": 60,
            "memory_usage": 50,
            "confidence_scores": 80
        },
        
        "languages": ["en", "fr", "de", "es", "it"],
        
        "supported_formats": ["image", "pdf"],
        
        "use_cases": [
            "Notes manuscrites",
            "Formulaires remplis à la main",
            "Signatures et annotations",
            "Texte historique dégradé",
            "Recherche académique"
        ]
    }
}


def calculate_overall_score(model_id: str) -> float:

    if model_id not in MODEL_MATRIX:
        return 0.0
    
    scoring = MODEL_MATRIX[model_id]["scoring"]
    
    weights = {
        "speed": 0.20,
        "accuracy_print": 0.25,
        "accuracy_handwritten": 0.10,
        "multilanguage": 0.10,
        "layout_preservation": 0.15,
        "ease_of_use": 0.05,
        "memory_usage": 0.05,
        "confidence_scores": 0.10
    }
    
    overall = sum(scoring[criterion] * weight for criterion, weight in weights.items())
    return round(overall, 1)


def get_best_model_for_task(task_type: str, language: str = "fr") -> str:

    recommendations = {
        "document": "docling",      
        "image": "paddleocr",     
        "handwritten": "trocr",     
        "multilingual": "easyocr", 
        "fast": "paddleocr",        
        "table": "docling",         
        "invoice": "paddleocr"      
    }
    
    return recommendations.get(task_type, "paddleocr")


def rank_models_by_criteria(criteria: str) -> list:

    rankings = []
    for model_id, data in MODEL_MATRIX.items():
        if criteria in data["scoring"]:
            rankings.append((model_id, data["scoring"][criteria]))
    
    return sorted(rankings, key=lambda x: x[1], reverse=True)


def get_model_info(model_id: str) -> dict:

    if model_id not in MODEL_MATRIX:
        return {}
    
    model_data = MODEL_MATRIX[model_id].copy()
    model_data["overall_score"] = calculate_overall_score(model_id)
    return model_data


def compare_models(model_ids: list = None) -> dict:
    if model_ids is None:
        model_ids = list(MODEL_MATRIX.keys())
    
    comparison = {
        "models": {},
        "rankings": {}
    }

    for model_id in model_ids:
        comparison["models"][model_id] = get_model_info(model_id)
    
    criteria = ["speed", "accuracy_print", "accuracy_handwritten", "multilanguage", 
                "layout_preservation", "ease_of_use", "confidence_scores"]
    
    for criterion in criteria:
        comparison["rankings"][criterion] = rank_models_by_criteria(criterion)
    
    return comparison
