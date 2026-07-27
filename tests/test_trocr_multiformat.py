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


results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

print("\n[1/6] Préparation des images de test...")

test_images = []

def _estimate_difficulty_trocr(filename):
    filename_lower = filename.lower()
    if "simple" in filename_lower or "demo" in filename_lower:
        return "optimal"  
    elif "petit" in filename_lower:
        return "difficile"  
    elif "italique" in filename_lower:
        return "moyen"  
    elif "multicolore" in filename_lower:
        return "moyen" 
    elif "tableau" in filename_lower:
        return "structuré" 
    elif "liste" in filename_lower:
        return "moyen"  
    elif "complet" in filename_lower or "grand" in filename_lower:
        return "complexe" 
    elif "nombres" in filename_lower:
        return "optimal"  
    elif "special" in filename_lower:
        return "difficile" 
    else:
        return "standard"


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
   
    selected_files = [
        "01_texte_simple.png",      
        "02_texte_multicolore.png",
        "05_texte_nombres.png",     
        "08_texte_italique.png",   
        "10_document_complet.png"   
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

demo_image = Path("demo_images/demo_text.png")
if demo_image.exists():
    test_images.append({
        "type": "Démo",
        "path": str(demo_image),
        "description": "Image démonstration standard",
        "expected_difficulty": "optimal",
        "model_suitability": "excellente"
    })


for img in test_images:
    if "model_suitability" not in img:
        img["model_suitability"] = _get_model_suitability(img["expected_difficulty"])

print(f"    {len(test_images)} images de test préparées")
print("    Sélection adaptée à TrOCR :")
for i, img in enumerate(test_images, 1):
    print(f"    [{i}] {img['description']}")
    print(f"        Difficulté : {img['expected_difficulty']} | Compatibilité : {img['model_suitability']}")

print("\n     NOTE : TrOCR utilise des modeles volumineux (~1.5GB)")
print("    Le premier telechargement peut prendre plusieurs minutes")


def _assess_quality(text, expected_difficulty):
    return "N/A"  