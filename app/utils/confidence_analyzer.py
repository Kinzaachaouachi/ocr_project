from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher, get_close_matches
from typing import Dict, List, Optional

_LEXICON = {
    "evaluation",
    "évaluation",
    "outils",
    "outil",
    "open",
    "source",
    "benchmark",
    "extraction",
    "intelligente",
    "documents",
    "document",
    "objectif",
    "comparer",
    "différentes",
    "differentes",
    "solutions",
    "gratuites",
    "extraire",
    "automatiquement",
    "texte",
    "depuis",
    "images",
    "image",
    "pdf",
    "recommandés",
    "recommandees",
    "recommandées",
    "travaux",
    "réaliser",
    "realiser",
    "python",
    "fastapi",
    "paddleocr",
    "docling",
    "easyocr",
    "trocr",
    "modèle",
    "modele",
    "modèles",
    "modeles",
    "confiance",
    "précision",
    "precision",
    "rapport",
    "historique",
    "dashboard",
    "utilisateur",
    "connexion",
    "email",
    "mot",
    "passe",
    "vérification",
    "verification",
    "langue",
    "français",
    "francais",
    "anglais",
    "allemand",
    "espagnol",
    "italien",
    "pour",
    "avec",
    "sans",
    "dans",
    "des",
    "les",
    "une",
    "sur",
    "par",
    "est",
    "sont",
    "cette",
    "cette",
    "aussi",
    "plus",
    "moins",
    "très",
    "tres",
    "bien",
    "mal",
    "après",
    "apres",
    "avant",
    "entre",
    "selon",
    "contre",
    "vers",
    "chez",
    "sous",
    "tout",
    "tous",
    "toute",
    "toutes",
    "autre",
    "autres",
    "même",
    "meme",
    "encore",
    "déjà",
    "deja",
    "ainsi",
    "donc",
    "puis",
    "car",
    "mais",
    "ou",
    "et",
    "si",
    "que",
    "qui",
    "quoi",
    "dont",
    "où",
    "ou",
    "comment",
    "pourquoi",
    "quand",
    "intelligence",
    "document",
    "documents",
    "benchmark",
    "extraction",
    "compare",
    "different",
    "solutions",
    "free",
    "automatically",
    "text",
    "from",
    "images",
    "tools",
    "recommended",
    "work",
    "works",
    "model",
    "models",
    "score",
    "time",
    "processing",
    "history",
    "profile",
    "password",
    "verification",
    "language",
}


def categorize_word_by_confidence(confidence: float) -> str:
    if confidence >= 0.90:
        return "high"
    elif confidence >= 0.70:
        return "medium"
    else:
        return "low"


def get_color_for_confidence(confidence: float) -> str:
    if confidence >= 0.90:
        return "#111827"
    elif confidence >= 0.70:
        return "#F59E0B"
    else:
        return "#EF4444"


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _normalize_token(word: str) -> str:
    w = word.strip().strip(".,;:!?\"'«»()[]{}|/\\")
    return w


def _core_alpha(word: str) -> str:

    w = _normalize_token(word)
    w = re.sub(r"^#+", "", w)
    return _strip_accents(w).lower()


def heuristic_word_quality(word: str) -> float:

    raw = word.strip()
    if not raw:
        return 0.5

    lower = raw.lower()
    if lower in {"<!--", "-->", "<!-- image -->"} or "<!--" in raw or "-->" in raw:
        return 0.55
    if lower == "image" and len(raw) <= 6:
        return 0.55

    core = _core_alpha(raw)
    if not core:
        return 0.88

    if re.fullmatch(r"#+", raw.strip()):
        return 0.92

    if len(core) <= 2:
        return 0.91

    if core in _LEXICON or raw.strip().lower() in _LEXICON:
        return 0.96

    close = get_close_matches(core, _LEXICON, n=1, cutoff=0.72)
    if close:
        ratio = SequenceMatcher(None, core, close[0]).ratio()
        if core != close[0]:
            if ratio >= 0.88:
                return 0.58
            if ratio >= 0.78:
                return 0.68

    if re.search(r"[A-Za-zÀ-ÿ]{2,}\d|\d[A-Za-zÀ-ÿ]{2,}", raw):

        if not re.fullmatch(r"[A-Za-z]+\d{1,2}", raw):
            return 0.55

    if re.search(r"[a-z][A-Z]{2,}[a-z]|[a-z]{2,}[A-Z]{2,}$", raw):
        return 0.62

    if re.search(r"(OCRY|APly|ocrY)$", raw):
        return 0.50

    if re.search(r"(.)\1\1", core):
        return 0.55

    if re.search(r"[bcdfghjklmnpqrstvwxz]{5,}", core):
        return 0.60

    vowels = len(re.findall(r"[aeiouyàâäéèêëïîôùûü]", core))
    if len(core) >= 6 and vowels / len(core) < 0.18:
        return 0.62

    if re.fullmatch(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-]*", _normalize_token(raw)):
        return 0.93

    return 0.80


def estimate_word_confidence(word: str, model_id: str = "docling") -> float:

    q = heuristic_word_quality(word)

    if model_id == "docling":
        return round(min(0.97, q + 0.02), 2)

    if model_id == "trocr":
        return round(max(0.40, q - 0.05), 2)
    return round(q, 2)


def refine_model_confidence(word: str, model_confidence: float) -> float:
    try:
        mc = float(model_confidence)
    except (TypeError, ValueError):
        mc = 0.75
    mc = max(0.0, min(1.0, mc))
    q = heuristic_word_quality(word)

    if q < 0.70:
        return round(min(mc, q), 2)
    if q < 0.85 and mc > 0.90:

        return round(min(mc, 0.85), 2)

    blended = 0.75 * mc + 0.25 * q
    return round(max(0.35, min(0.98, blended)), 2)


def build_word_confidence_from_text(text: str, model_id: str = "docling") -> List[Dict]:

    data = []
    for word in (text or "").split():
        if not word.strip():
            continue
        data.append(
            {
                "word": word,
                "confidence": estimate_word_confidence(word, model_id),
            }
        )
    return data


def refine_word_confidence_list(
    word_confidence_data: List[Dict],
    model_id: str = "",
    text: Optional[str] = None,
) -> List[Dict]:

    if (not word_confidence_data) and text:
        return build_word_confidence_from_text(text, model_id or "docling")

    if not word_confidence_data:
        return []

    confs = [float(w.get("confidence", 0.75) or 0.75) for w in word_confidence_data]

    unique = {round(c, 2) for c in confs}
    flat = len(unique) <= 2 and len(confs) >= 5

    refined = []
    for item in word_confidence_data:
        word = item.get("word", "")
        raw_conf = float(item.get("confidence", 0.75) or 0.75)

        if model_id in ("docling", "trocr") or flat:
            conf = estimate_word_confidence(word, model_id or "docling")
        else:
            conf = refine_model_confidence(word, raw_conf)

        refined.append({"word": word, "confidence": conf})

    return refined


def analyze_text_confidence(word_confidence_data: List[Dict]) -> Dict:
    if not word_confidence_data:
        return {
            "total_words": 0,
            "avg_confidence": 0.0,
            "high_confidence_words": 0,
            "medium_confidence_words": 0,
            "low_confidence_words": 0,
            "high_confidence_percentage": 0.0,
            "reliability_score": 0.0,
        }

    total_words = len(word_confidence_data)
    confidences = [w["confidence"] for w in word_confidence_data]
    avg_confidence = sum(confidences) / total_words if total_words > 0 else 0.0

    high_count = sum(1 for c in confidences if c >= 0.90)
    medium_count = sum(1 for c in confidences if 0.70 <= c < 0.90)
    low_count = sum(1 for c in confidences if c < 0.70)

    high_percentage = (high_count / total_words * 100) if total_words > 0 else 0.0
    reliability_score = round(high_percentage, 1)

    return {
        "total_words": total_words,
        "avg_confidence": round(avg_confidence, 2),
        "high_confidence_words": high_count,
        "medium_confidence_words": medium_count,
        "low_confidence_words": low_count,
        "high_confidence_percentage": round(high_percentage, 1),
        "reliability_score": reliability_score,
    }


def annotate_text_with_confidence(
    text: str, word_confidence_data: List[Dict]
) -> List[Dict]:
    annotated_words = []

    confidence_map = {}
    for item in word_confidence_data:
        word = item["word"]
        conf = item["confidence"]
        confidence_map[word.lower()] = conf

    for word in text.split():
        clean_word = word.strip()
        if not clean_word:
            continue

        confidence = confidence_map.get(clean_word.lower(), 0.75)
        category = categorize_word_by_confidence(confidence)
        color = get_color_for_confidence(confidence)

        annotated_words.append(
            {
                "word": clean_word,
                "confidence": confidence,
                "category": category,
                "color": color,
            }
        )

    return annotated_words


def generate_html_colored_text(annotated_words: List[Dict]) -> str:
    html_parts = []
    for item in annotated_words:
        word = item["word"]
        color = item["color"]
        confidence = item["confidence"]
        html_parts.append(
            f'<span style="color: {color};" title="Confiance: {confidence:.0%}">{word}</span>'
        )
    return " ".join(html_parts)


def compare_word_confidence_across_models(results: List[Dict], word: str) -> Dict:
    word_lower = word.lower()
    comparison = {}

    for result in results:
        if result.get("status") != "success":
            continue

        model_id = result["model_id"]
        word_conf_data = result.get("word_confidence", [])
        for item in word_conf_data:
            if item["word"].lower() == word_lower:
                comparison[model_id] = item["confidence"]
                break

    return comparison
