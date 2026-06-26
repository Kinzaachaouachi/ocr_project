
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("   TEST TrOCR MULTIFORMAT - Kinza Chaouachi")
print("=" * 80)

# Créer le dossier de résultats
results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

print("\n[1/6] Préparation des images de test...")

test_images = []

# Fonction pour estimer la difficulté pour TrOCR
def _estimate_difficulty_trocr(filename):
    filename_lower = filename.lower()
    if "simple" in filename_lower or "demo" in filename_lower:
        return "optimal"  # Texte standard, parfait pour TrOCR
    elif "petit" in filename_lower:
        return "difficile"  # Texte petit
    elif "italique" in filename_lower:
        return "moyen"  # Italique peut être OK
    elif "multicolore" in filename_lower:
        return "moyen"  # Couleurs différentes
    elif "tableau" in filename_lower:
        return "structuré"  # Plus difficile pour TrOCR
    elif "liste" in filename_lower:
        return "moyen"  # Listes peuvent être OK
    elif "complet" in filename_lower or "grand" in filename_lower:
        return "complexe"  # Documents complets
    elif "nombres" in filename_lower:
        return "optimal"  # TrOCR bon avec chiffres
    elif "special" in filename_lower:
        return "difficile"  # Caractères spéciaux
    else:
        return "standard"

# Fonction pour évaluer la compatibilité modèle
def _get_model_suitability(difficulty):
    suitability_map = {
        "optimal": "excellente",
        "standard": "bonne",
        "moyen": "moyenne",
        "difficile": "faible",
        "complexe": "variable",
        "structuré": "limitée"
    }
    return suitability_map.get(difficulty, "variable")

corpus_dir = Path("corpus_test")
if corpus_dir.exists():
    # Sélectionner des images représentatives
    selected_files = [
        "01_texte_simple.png",      # Optimal
        "02_texte_multicolore.png", # Moyen
        "05_texte_nombres.png",     # Optimal (chiffres)
        "08_texte_italique.png",    # Moyen
        "10_document_complet.png"   # Complexe
    ]
    
    for filename in selected_files:
        img_path = corpus_dir / filename
        if img_path.exists():
            difficulty = _estimate_difficulty_trocr(filename)
            test_images.append({
                "type": "Corpus test",
                "path": str(img_path),
                "description": f"Corpus: {img_path.stem}",
                "expected_difficulty": difficulty,
                "model_suitability": _get_model_suitability(difficulty)
            })

# 2. Image de démonstration
demo_image = Path("demo_images/demo_text.png")
if demo_image.exists():
    test_images.append({
        "type": "Démo",
        "path": str(demo_image),
        "description": "Image démonstration standard",
        "expected_difficulty": "optimal",
        "model_suitability": "excellente"
    })

# Mettre à jour les compatibilités
for img in test_images:
    if "model_suitability" not in img:
        img["model_suitability"] = _get_model_suitability(img["expected_difficulty"])

print(f"    {len(test_images)} images de test préparées")
print("    Sélection adaptée à TrOCR :")
for i, img in enumerate(test_images, 1):
    print(f"    [{i}] {img['description']}")
    print(f"        Difficulté : {img['expected_difficulty']} | Compatibilité : {img['model_suitability']}")

print("\n    [!] NOTE : TrOCR utilise des modeles volumineux (~1.5GB)")
print("    Le premier telechargement peut prendre plusieurs minutes")

# Fonction pour évaluer la qualité du texte
def _assess_quality(text, expected_difficulty):
    return "N/A"  # TrOCR non adapté aux images multi-lignes