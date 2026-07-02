# -*- coding: utf-8 -*-
"""
Analyseur de confiance pour les résultats OCR
Catégorise les mots selon leur niveau de confiance
"""

from typing import List, Dict, Tuple


def categorize_word_by_confidence(confidence: float) -> str:
    """
    Catégorise un mot selon son score de confiance.
    
    Args:
        confidence: Score de confiance entre 0 et 1
        
    Returns:
        Catégorie: "high" (noir), "medium" (orange), "low" (rouge)
    """
    if confidence >= 0.85:
        return "high"      # Noir - 100% correcte
    elif confidence >= 0.60:
        return "medium"    # Orange - Peut être incorrecte
    else:
        return "low"       # Rouge - Probablement incorrecte


def get_color_for_confidence(confidence: float) -> str:
    """
    Retourne la couleur CSS correspondant au niveau de confiance.
    
    Args:
        confidence: Score de confiance entre 0 et 1
        
    Returns:
        Code couleur hexadécimal
    """
    if confidence >= 0.85:
        return "#0F172A"   # Noir
    elif confidence >= 0.60:
        return "#F59E0B"   # Orange
    else:
        return "#DC2626"   # Rouge


def analyze_text_confidence(word_confidence_data: List[Dict]) -> Dict:
    """
    Analyse la confiance globale d'un texte extrait.
    
    Args:
        word_confidence_data: Liste de dictionnaires {"word": str, "confidence": float}
        
    Returns:
        Statistiques de confiance
    """
    if not word_confidence_data:
        return {
            "total_words": 0,
            "avg_confidence": 0.0,
            "high_confidence_words": 0,
            "medium_confidence_words": 0,
            "low_confidence_words": 0,
            "high_confidence_percentage": 0.0,
            "reliability_score": 0.0
        }
    
    total_words = len(word_confidence_data)
    confidences = [w["confidence"] for w in word_confidence_data]
    avg_confidence = sum(confidences) / total_words if total_words > 0 else 0.0
    
    high_count = sum(1 for c in confidences if c >= 0.85)
    medium_count = sum(1 for c in confidences if 0.60 <= c < 0.85)
    low_count = sum(1 for c in confidences if c < 0.60)
    
    high_percentage = (high_count / total_words * 100) if total_words > 0 else 0.0
    
    # Score de fiabilité global (basé sur pourcentage de mots haute confiance)
    reliability_score = round(high_percentage, 1)
    
    return {
        "total_words": total_words,
        "avg_confidence": round(avg_confidence, 2),
        "high_confidence_words": high_count,
        "medium_confidence_words": medium_count,
        "low_confidence_words": low_count,
        "high_confidence_percentage": round(high_percentage, 1),
        "reliability_score": reliability_score
    }


def annotate_text_with_confidence(text: str, word_confidence_data: List[Dict]) -> List[Dict]:
    """
    Annote chaque mot du texte avec sa catégorie de confiance.
    
    Args:
        text: Texte complet
        word_confidence_data: Données de confiance par mot
        
    Returns:
        Liste de dictionnaires avec word, confidence, category, color
    """
    annotated_words = []
    
    # Créer un mapping des mots avec leur confiance
    confidence_map = {}
    for item in word_confidence_data:
        word = item["word"]
        conf = item["confidence"]
        # Utiliser le mot en minuscule comme clé pour correspondance insensible à la casse
        confidence_map[word.lower()] = conf
    
    # Parcourir le texte et annoter chaque mot
    words_in_text = text.split()
    
    for word in words_in_text:
        clean_word = word.strip()
        if not clean_word:
            continue
            
        # Chercher la confiance du mot (insensible à la casse)
        confidence = confidence_map.get(clean_word.lower(), 0.75)  # Par défaut 0.75
        category = categorize_word_by_confidence(confidence)
        color = get_color_for_confidence(confidence)
        
        annotated_words.append({
            "word": clean_word,
            "confidence": confidence,
            "category": category,
            "color": color
        })
    
    return annotated_words


def generate_html_colored_text(annotated_words: List[Dict]) -> str:
    """
    Génère du HTML avec le texte coloré selon la confiance.
    
    Args:
        annotated_words: Mots annotés avec confiance et couleur
        
    Returns:
        HTML string
    """
    html_parts = []
    
    for item in annotated_words:
        word = item["word"]
        color = item["color"]
        confidence = item["confidence"]
        
        # Créer un span avec la couleur et un title pour afficher la confiance
        html_parts.append(
            f'<span style="color: {color};" title="Confiance: {confidence:.0%}">{word}</span>'
        )
    
    return " ".join(html_parts)


def compare_word_confidence_across_models(results: List[Dict], word: str) -> Dict:
    """
    Compare la confiance d'un mot spécifique à travers plusieurs modèles.
    
    Args:
        results: Liste des résultats de tous les modèles
        word: Mot à comparer
        
    Returns:
        Dictionnaire avec la confiance par modèle
    """
    word_lower = word.lower()
    comparison = {}
    
    for result in results:
        if result.get("status") != "success":
            continue
            
        model_id = result["model_id"]
        word_conf_data = result.get("word_confidence", [])
        
        # Chercher le mot dans les données de confiance
        for item in word_conf_data:
            if item["word"].lower() == word_lower:
                comparison[model_id] = item["confidence"]
                break
    
    return comparison
