# -*- coding: utf-8 -*-
"""
Détection automatique de langue pour les fichiers OCR
Supporte la détection via le contenu texte ou les métadonnées du fichier
"""

import re
from typing import List, Tuple, Optional

# Mappage des codes de langue ISO 639-1 vers les noms complets
LANGUAGE_NAMES = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ar": "العربية",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "ru": "Русский",
    "tr": "Türkçe",
    "nl": "Nederlands",
    "pl": "Polski",
    "vi": "Tiếng Việt",
    "th": "ไทย",
    "he": "עברית",
    "hi": "हिन्दी"
}

# Mapping des modèles OCR vers les langues supportées
MODEL_LANGUAGE_SUPPORT = {
    "paddleocr": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru", "tr", "nl", "pl", "vi", "th", "hi"],
    "docling": ["fr", "en", "es", "de", "it", "pt", "zh", "ja"],
    "easyocr": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru", "tr", "nl", "pl", "vi", "th", "he", "hi"],
    "trocr": ["en", "fr", "de", "es", "it"]
}


def detect_language_from_text(text: str) -> Tuple[str, float]:
    """
    Détecte la langue d'un texte en utilisant langdetect.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Tuple (code_langue, score_confiance) ex: ("fr", 0.95)
    """
    if not text or len(text.strip()) < 10:
        return ("en", 0.5)  # Par défaut anglais si texte trop court
    
    try:
        import langdetect
        from langdetect import detect_langs
        
        # Détecter avec scores de confiance
        langs = detect_langs(text)
        if langs:
            best_lang = langs[0]
            return (best_lang.lang, best_lang.prob)
        
        return ("en", 0.5)
    except Exception:
        # Fallback: détection par patterns de caractères
        return detect_language_by_charset(text)


def detect_language_by_charset(text: str) -> Tuple[str, float]:
    """
    Détecte la langue par analyse des caractères (fallback method).
    Utile pour les langues avec alphabets distincts.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Tuple (code_langue, score_confiance)
    """
    text_sample = text[:500]  # Analyser les premiers 500 caractères
    
    # Compter les caractères par script
    char_counts = {
        "arabic": len(re.findall(r'[\u0600-\u06FF]', text_sample)),
        "chinese": len(re.findall(r'[\u4E00-\u9FFF]', text_sample)),
        "cyrillic": len(re.findall(r'[\u0400-\u04FF]', text_sample)),
        "japanese_hira": len(re.findall(r'[\u3040-\u309F]', text_sample)),
        "japanese_kata": len(re.findall(r'[\u30A0-\u30FF]', text_sample)),
        "korean": len(re.findall(r'[\uAC00-\uD7AF]', text_sample)),
        "hebrew": len(re.findall(r'[\u0590-\u05FF]', text_sample)),
        "thai": len(re.findall(r'[\u0E00-\u0E7F]', text_sample)),
        "devanagari": len(re.findall(r'[\u0900-\u097F]', text_sample))
    }
    
    total_chars = len(text_sample)
    
    # Si plus de 30% de caractères arabes
    if char_counts["arabic"] > total_chars * 0.3:
        return ("ar", 0.9)
    
    # Si plus de 30% de caractères chinois
    if char_counts["chinese"] > total_chars * 0.3:
        return ("zh", 0.9)
    
    # Si plus de 30% de caractères cyrilliques
    if char_counts["cyrillic"] > total_chars * 0.3:
        return ("ru", 0.85)
    
    # Si hiragana ou katakana présents
    if (char_counts["japanese_hira"] + char_counts["japanese_kata"]) > total_chars * 0.2:
        return ("ja", 0.9)
    
    # Si caractères coréens
    if char_counts["korean"] > total_chars * 0.3:
        return ("ko", 0.9)
    
    # Si hébreu
    if char_counts["hebrew"] > total_chars * 0.3:
        return ("he", 0.9)
    
    # Si thaï
    if char_counts["thai"] > total_chars * 0.3:
        return ("th", 0.9)
    
    # Si devanagari (hindi)
    if char_counts["devanagari"] > total_chars * 0.3:
        return ("hi", 0.85)
    
    # Langues latines - analyse par mots communs
    return detect_latin_language(text_sample)


def detect_latin_language(text: str) -> Tuple[str, float]:
    """
    Détecte les langues utilisant l'alphabet latin par mots clés.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Tuple (code_langue, score_confiance)
    """
    text_lower = text.lower()
    
    # Mots clés caractéristiques par langue
    keywords = {
        "fr": ["le", "la", "les", "un", "une", "des", "de", "et", "à", "dans", "pour", "est", "que", "qui"],
        "en": ["the", "and", "of", "to", "in", "is", "it", "you", "that", "was", "for", "on", "are"],
        "es": ["el", "la", "los", "las", "un", "una", "de", "y", "en", "es", "para", "que", "por"],
        "de": ["der", "die", "das", "und", "in", "ist", "den", "zu", "mit", "auf", "für", "des"],
        "it": ["il", "la", "di", "e", "un", "una", "che", "per", "in", "del", "è", "non"],
        "pt": ["o", "a", "os", "as", "um", "uma", "de", "e", "em", "para", "que", "do", "da"]
    }
    
    # Compter les occurrences de mots clés pour chaque langue
    scores = {}
    for lang, words in keywords.items():
        count = sum(1 for word in words if f" {word} " in f" {text_lower} ")
        scores[lang] = count
    
    # Trouver la langue avec le plus de correspondances
    if scores:
        best_lang = max(scores, key=scores.get)
        max_score = scores[best_lang]
        
        # Calculer un score de confiance
        total_matches = sum(scores.values())
        confidence = min(0.95, (max_score / max(total_matches, 1)) * 0.9) if total_matches > 0 else 0.5
        
        if max_score >= 3:  # Au moins 3 mots clés trouvés
            return (best_lang, confidence)
    
    # Par défaut, anglais avec faible confiance
    return ("en", 0.5)


def get_best_models_for_language(language_code: str) -> List[str]:
    """
    Retourne les modèles OCR recommandés pour une langue donnée,
    triés par ordre de préférence.
    
    Args:
        language_code: Code ISO 639-1 de la langue (ex: "fr", "ar", "zh")
        
    Returns:
        Liste des model_id triés par pertinence
    """
    supported_models = []
    
    for model_id, supported_langs in MODEL_LANGUAGE_SUPPORT.items():
        if language_code in supported_langs:
            supported_models.append(model_id)
    
    # Si aucun modèle ne supporte la langue, retourner tous les modèles
    if not supported_models:
        return ["paddleocr", "easyocr", "docling", "trocr"]
    
    # Tri personnalisé selon la langue
    priority_order = {
        "ar": ["easyocr", "paddleocr", "docling"],  # EasyOCR excellent pour l'arabe
        "zh": ["paddleocr", "easyocr", "docling"],  # PaddleOCR excellent pour le chinois
        "ja": ["paddleocr", "easyocr", "docling"],  # PaddleOCR excellent pour le japonais
        "ko": ["paddleocr", "easyocr"],
        "en": ["paddleocr", "docling", "easyocr", "trocr"],  # Tous excellents pour l'anglais
        "fr": ["paddleocr", "docling", "easyocr", "trocr"],
        "de": ["paddleocr", "docling", "easyocr", "trocr"],
        "es": ["paddleocr", "docling", "easyocr", "trocr"],
        "it": ["paddleocr", "docling", "easyocr", "trocr"],
        "pt": ["paddleocr", "docling", "easyocr"]
    }
    
    preferred_order = priority_order.get(language_code, supported_models)
    
    # Ajouter les modèles supportés qui ne sont pas dans l'ordre préféré
    for model in supported_models:
        if model not in preferred_order:
            preferred_order.append(model)
    
    return preferred_order


def detect_language_from_filename(filename: str) -> Optional[str]:
    """
    Tente de détecter la langue à partir du nom du fichier.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Code de langue ou None si non détectable
    """
    filename_lower = filename.lower()
    
    # Patterns de détection dans le nom de fichier
    patterns = {
        "fr": ["_fr", "_french", "_francais", "france"],
        "en": ["_en", "_english", "_eng"],
        "es": ["_es", "_spanish", "_espanol"],
        "de": ["_de", "_german", "_deutsch"],
        "ar": ["_ar", "_arabic"],
        "zh": ["_zh", "_chinese", "_cn"],
        "ja": ["_ja", "_japanese", "_jp"],
        "ko": ["_ko", "_korean", "_kr"]
    }
    
    for lang_code, keywords in patterns.items():
        if any(keyword in filename_lower for keyword in keywords):
            return lang_code
    
    return None


def get_language_name(language_code: str) -> str:
    """
    Retourne le nom complet de la langue.
    
    Args:
        language_code: Code ISO 639-1
        
    Returns:
        Nom de la langue ou le code si inconnu
    """
    return LANGUAGE_NAMES.get(language_code, language_code.upper())


def configure_model_for_language(model_id: str, language_code: str) -> dict:
    """
    Retourne la configuration recommandée pour un modèle selon la langue.
    
    Args:
        model_id: Identifiant du modèle OCR
        language_code: Code de langue
        
    Returns:
        Dictionnaire de configuration
    """
    configs = {
        "paddleocr": {
            "lang": language_code,
            "use_angle_cls": True,
            "show_log": False
        },
        "easyocr": {
            "languages": [language_code, "en"],  # Toujours ajouter l'anglais
            "gpu": False
        },
        "docling": {},  # Docling détecte automatiquement
        "trocr": {}  # TrOCR utilise le modèle pré-entraîné
    }
    
    return configs.get(model_id, {})
