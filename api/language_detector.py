

import re
from typing import List, Tuple, Optional

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

MODEL_LANGUAGE_SUPPORT = {
    "paddleocr": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru", "tr", "nl", "pl", "vi", "th", "hi"],
    "docling": ["fr", "en", "es", "de", "it", "pt", "zh", "ja"],
    "easyocr": ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru", "tr", "nl", "pl", "vi", "th", "he", "hi"],
    "trocr": ["en", "fr", "de", "es", "it"]
}


def detect_language_from_text(text: str) -> Tuple[str, float]:
    if not text or len(text.strip()) < 10:
        return ("en", 0.5)  
    
    try:
        import langdetect
        from langdetect import detect_langs
        langs = detect_langs(text)
        if langs:
            best_lang = langs[0]
            return (best_lang.lang, best_lang.prob)
        
        return ("en", 0.5)
    except Exception:
        return detect_language_by_charset(text)


def detect_language_by_charset(text: str) -> Tuple[str, float]:
    text_sample = text[:500]  
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
    if char_counts["arabic"] > total_chars * 0.3:
        return ("ar", 0.9)
    
    if char_counts["chinese"] > total_chars * 0.3:
        return ("zh", 0.9)
    
    if char_counts["cyrillic"] > total_chars * 0.3:
        return ("ru", 0.85)
    
    if (char_counts["japanese_hira"] + char_counts["japanese_kata"]) > total_chars * 0.2:
        return ("ja", 0.9)
    
    if char_counts["korean"] > total_chars * 0.3:
        return ("ko", 0.9)
    
    if char_counts["hebrew"] > total_chars * 0.3:
        return ("he", 0.9)
    
    if char_counts["thai"] > total_chars * 0.3:
        return ("th", 0.9)
    
    if char_counts["devanagari"] > total_chars * 0.3:
        return ("hi", 0.85)
    
    return detect_latin_language(text_sample)


def detect_latin_language(text: str) -> Tuple[str, float]:
    text_lower = text.lower()
    
    keywords = {
        "fr": ["le", "la", "les", "un", "une", "des", "de", "et", "à", "dans", "pour", "est", "que", "qui"],
        "en": ["the", "and", "of", "to", "in", "is", "it", "you", "that", "was", "for", "on", "are"],
        "es": ["el", "la", "los", "las", "un", "una", "de", "y", "en", "es", "para", "que", "por"],
        "de": ["der", "die", "das", "und", "in", "ist", "den", "zu", "mit", "auf", "für", "des"],
        "it": ["il", "la", "di", "e", "un", "una", "che", "per", "in", "del", "è", "non"],
        "pt": ["o", "a", "os", "as", "um", "uma", "de", "e", "em", "para", "que", "do", "da"]
    }
    
   
    scores = {}
    for lang, words in keywords.items():
        count = sum(1 for word in words if f" {word} " in f" {text_lower} ")
        scores[lang] = count
    if scores:
        best_lang = max(scores, key=scores.get)
        max_score = scores[best_lang]
        
        total_matches = sum(scores.values())
        confidence = min(0.95, (max_score / max(total_matches, 1)) * 0.9) if total_matches > 0 else 0.5
        
        if max_score >= 3:  
            return (best_lang, confidence)
    
    return ("en", 0.5)


def get_best_models_for_language(language_code: str) -> List[str]:
 
    supported_models = []
    
    for model_id, supported_langs in MODEL_LANGUAGE_SUPPORT.items():
        if language_code in supported_langs:
            supported_models.append(model_id)
    
   
    if not supported_models:
        return ["paddleocr", "easyocr", "docling", "trocr"]
    
    priority_order = {
        "ar": ["easyocr", "paddleocr", "docling"],  
        "zh": ["paddleocr", "easyocr", "docling"],  
        "ja": ["paddleocr", "easyocr", "docling"],  
        "ko": ["paddleocr", "easyocr"],
        "en": ["paddleocr", "docling", "easyocr", "trocr"], 
        "fr": ["paddleocr", "docling", "easyocr", "trocr"],
        "de": ["paddleocr", "docling", "easyocr", "trocr"],
        "es": ["paddleocr", "docling", "easyocr", "trocr"],
        "it": ["paddleocr", "docling", "easyocr", "trocr"],
        "pt": ["paddleocr", "docling", "easyocr"]
    }
    
    preferred_order = priority_order.get(language_code, supported_models)
    
    
    for model in supported_models:
        if model not in preferred_order:
            preferred_order.append(model)
    
    return preferred_order


def detect_language_from_filename(filename: str) -> Optional[str]:

    filename_lower = filename.lower()
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
    return LANGUAGE_NAMES.get(language_code, language_code.upper())


def configure_model_for_language(model_id: str, language_code: str) -> dict:

    configs = {
        "paddleocr": {
            "lang": language_code,
            "use_angle_cls": True,
            "show_log": False
        },
        "easyocr": {
            "languages": [language_code, "en"],  
            "gpu": False
        },
        "docling": {},  
        "trocr": {} 
    }
    
    return configs.get(model_id, {})
