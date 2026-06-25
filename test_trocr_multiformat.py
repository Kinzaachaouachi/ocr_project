"""
TEST TrOCR MULTIFORMAT - Test TrOCR sur plusieurs types d'images
Auteur : Kinza Achaouachi
Description : Test complet de TrOCR (Transformer OCR) avec images variées
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("   TEST TrOCR MULTIFORMAT - Kinza Achaouachi")
print("=" * 80)

# Créer le dossier de résultats
results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

# ── Étape 1 : Préparation des images de test ──────────────
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

# 1. Images sélectionnées du corpus (pas toutes pour éviter temps long)
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
    """Évalue la qualité du texte détecté par TrOCR"""
    if not text or len(text.strip()) == 0:
        return {"overall": "vide", "readability": 0, "structure": 0}
    
    # Mesures simples
    text_lower = text.lower()
    
    # Lisibilité basique
    word_count = len(text.split())
    avg_word_len = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0
    
    # Indicateurs de qualité
    has_punctuation = any(c in text for c in '.!?,;:')
    has_numbers = any(c.isdigit() for c in text)
    has_letters = any(c.isalpha() for c in text)
    
    # Score de lisibilité (0-100)
    readability_score = 0
    if word_count >= 3:
        readability_score += 30
    if avg_word_len >= 3 and avg_word_len <= 10:
        readability_score += 30
    if has_punctuation:
        readability_score += 20
    if has_letters and has_numbers:
        readability_score += 20
    
    # Évaluation globale
    if readability_score >= 80:
        overall = "excellente"
    elif readability_score >= 60:
        overall = "bonne"
    elif readability_score >= 40:
        overall = "moyenne"
    elif readability_score >= 20:
        overall = "faible"
    else:
        overall = "très faible"
    
    # Ajuster selon la difficulté attendue
    if expected_difficulty in ["difficile", "complexe"] and readability_score >= 40:
        overall = "bonne (pour difficulté élevée)"
    
    return {
        "overall": overall,
        "readability_score": readability_score,
        "word_count": word_count,
        "avg_word_length": round(avg_word_len, 1),
        "has_punctuation": has_punctuation,
        "has_numbers": has_numbers,
        "has_letters": has_letters
    }

# ── Étape 2 : Initialisation de TrOCR ──────────────
print("\n[2/6] Initialisation de TrOCR...")

try:
    init_start = time.time()
    
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch
    from PIL import Image
    
    print("    Téléchargement du modèle TrOCR...")
    print("    Ceci peut prendre du temps (modèle ~1.5GB)")
    print("    Patientez...")
    
    # Utiliser le modèle small-printed (plus rapide)
    model_name = "microsoft/trocr-small-printed"
    
    processor = TrOCRProcessor.from_pretrained(model_name)
    model = VisionEncoderDecoderModel.from_pretrained(model_name)
    
    # Configuration
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        model.to(device)
    
    init_time = time.time() - init_start
    
    print(f"    [OK] TrOCR initialise en {init_time:.2f}s")
    print(f"    Modèle : {model_name}")
    print(f"    Device : {device}")
    print(f"    Taille modèle : ~360M paramètres (small version)")
    
except Exception as e:
    print(f"    [X] Erreur d'initialisation : {e}")
    print("    Installation : pip install transformers torch torchvision")
    print("    Note : Premier téléchargement ~1.5GB, patience requise")
    sys.exit(1)

# ── Étape 3 : Tests sur chaque image ──────────────
print("\n[3/6] Exécution des tests sur chaque image...")
print("-" * 80)

results = []
total_start = time.time()

for i, test_image in enumerate(test_images, 1):
    print(f"\n    Test {i}/{len(test_images)} : {test_image['description']}")
    print(f"    Compatibilité : {test_image['model_suitability']} | Difficulté : {test_image['expected_difficulty']}")
    
    image_result = {
        "file": test_image['path'],
        "type": test_image['type'],
        "description": test_image['description'],
        "expected_difficulty": test_image['expected_difficulty'],
        "model_suitability": test_image['model_suitability'],
        "status": "non testé"
    }
    
    try:
        # Vérifier que le fichier existe
        if not Path(test_image['path']).exists():
            image_result["status"] = "échec"
            image_result["error"] = "Fichier non trouvé"
            print(f"      [X] Fichier non trouve")
            continue
        
        # Charger et prétraiter l'image
        img = Image.open(test_image['path']).convert("RGB")
        
        # Mesurer le temps de traitement
        process_start = time.time()
        
        # Préparer l'image pour le modèle
        pixel_values = processor(images=img, return_tensors="pt").pixel_values
        
        # Déplacer sur device si GPU
        if device == "cuda":
            pixel_values = pixel_values.to(device)
        
        # Générer le texte
        with torch.no_grad():
            generated_ids = model.generate(pixel_values)
            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        process_time = time.time() - process_start
        
        # Analyser les résultats
        if generated_text and generated_text.strip():
            # Nettoyer le texte
            cleaned_text = generated_text.strip()
            
            # Analyser la sortie
            text_length = len(cleaned_text)
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text.replace(" ", ""))
            
            # Évaluer la qualité (TrOCR ne donne pas de score de confiance)
            quality_indicators = _assess_quality(cleaned_text, test_image['expected_difficulty'])
            
            image_result.update({
                "status": "succès",
                "processing_time": round(process_time, 2),
                "detected_text": cleaned_text,
                "text_length": text_length,
                "word_count": word_count,
                "character_count": char_count,
                "quality_assessment": quality_indicators,
                "sample": cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
            })
            
            print(f"      [OK] Succes : {process_time:.2f}s")
            print(f"        Texte détecté : {text_length} caractères, {word_count} mots")
            print(f"        Qualité : {quality_indicators['overall']}")
            
            # Afficher un extrait
            if cleaned_text:
                sample = cleaned_text[:80] + "..." if len(cleaned_text) > 80 else cleaned_text
                print(f"        Extrait : '{sample}'")
                
            # Informations spécifiques
            if test_image['expected_difficulty'] == 'optimal':
                print(f"        [*] Texte optimal pour TrOCR")
            elif test_image['model_suitability'] == 'faible':
                print(f"        [!] Compatibilite faible, resultats variables attendus")
                
        else:
            image_result.update({
                "status": "échec",
                "processing_time": round(process_time, 2),
                "error": "Texte vide ou non détecté"
            })
            print(f"      [X] Texte vide detecte : {process_time:.2f}s")
            
    except Exception as e:
        image_result.update({
            "status": "échec",
            "error": str(e),
            "processing_time": 0
        })
        print(f"      [X] Erreur : {e}")
    
    results.append(image_result)

total_time = time.time() - total_start

# ── Étape 4 : Résultats par compatibilité ──────────────
print("\n[4/6] Résultats par niveau de compatibilité...")
print("-" * 80)

# Grouper par compatibilité
compatibility_results = {}
for res in results:
    compatibility = res.get("model_suitability", "inconnue")
    if compatibility not in compatibility_results:
        compatibility_results[compatibility] = []
    compatibility_results[compatibility].append(res)

print("\n    [Stats] PERFORMANCE PAR COMPATIBILITE :")
print("    " + "-" * 50)

for compatibility, comp_res in sorted(compatibility_results.items()):
    succès = [r for r in comp_res if r["status"] == "succès"]
    échecs = [r for r in comp_res if r["status"] == "échec"]
    
    total = len(comp_res)
    success_rate = len(succès) / total * 100 if total > 0 else 0
    
    if succès:
        avg_time = sum(r.get("processing_time", 0) for r in succès) / len(succès)
        avg_text_len = sum(r.get("text_length", 0) for r in succès) / len(succès)
        avg_quality = sum(r.get("quality_assessment", {}).get("readability_score", 0) for r in succès) / len(succès)
    else:
        avg_time = avg_text_len = avg_quality = 0
    
    print(f"\n    [Config] {compatibility.upper()} ({total} images) :")
    print(f"      [OK] Succes : {len(succès)} | [X] Echecs : {len(échecs)}")
    print(f"      [Graph] Taux de succes : {success_rate:.1f}%")
    print(f"      [Temps] Temps moyen : {avg_time:.2f}s")
    print(f"      [Note] Longueur texte moyenne : {avg_text_len:.0f} caracteres")
    print(f"      [Cible] Score qualite moyen : {avg_quality:.1f}/100")

# ── Étape 5 : Statistiques globales ──────────────
print("\n[5/6] Statistiques globales...")
print("-" * 80)

succès_total = len([r for r in results if r["status"] == "succès"])
échecs_total = len([r for r in results if r["status"] == "échec"])

if succès_total > 0:
    avg_global_time = sum(r.get("processing_time", 0) for r in results if r["status"] == "succès") / succès_total
    avg_global_text_len = sum(r.get("text_length", 0) for r in results if r["status"] == "succès") / succès_total
    avg_global_quality = sum(r.get("quality_assessment", {}).get("readability_score", 0) for r in results if r["status"] == "succès") / succès_total
else:
    avg_global_time = avg_global_text_len = avg_global_quality = 0

print(f"    [Stats] TOTAL DES TESTS : {len(results)} images")
print(f"      [OK] Succes : {succès_total}")
print(f"      [X] Echecs : {échecs_total}")
print(f"      [Cible] Taux de succes global : {succès_total/len(results)*100:.1f}%")
print(f"      [Cible] Qualite moyenne : {avg_global_quality:.1f}/100")
print(f"      [Note] Longueur texte moyenne : {avg_global_text_len:.0f} caracteres")
print(f"      [Temps] Temps moyen par image : {avg_global_time:.2f}s")
print(f"      [Temps] Temps total : {total_time:.2f}s")
print(f"      [Temps] Temps initialisation (modele) : {init_time:.2f}s")

print("\n    [Rapide] PERFORMANCE TrOCR :")
print(f"      - Device utilise : {device}")
print(f"      - Modele : microsoft/trocr-small-printed")
print(f"      - Architecture : Vision Transformer + Decoder")
print(f"      - Specialisation : Texte imprime")

# ── Étape 6 : Sauvegarde des résultats ──────────────
print("\n[6/6] Sauvegarde des résultats...")

results_file = results_dir / "trocr_multiformat_results.json"
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump({
        "test_date": datetime.now().isoformat(),
        "tool": "TrOCR",
        "configuration": f"{model_name}, {device}",
        "total_tests": len(results),
        "success_rate": succès_total/len(results)*100,
        "average_quality_score": avg_global_quality,
        "average_processing_time": avg_global_time,
        "total_time": total_time,
        "initialization_time": init_time,
        "device": device,
        "results": results
    }, f, indent=2, ensure_ascii=False)

print(f"    [Fichier] Resultats sauvegardes : {results_file}")

# ── Conclusion ────────────────────────────────────
print("\n" + "=" * 80)
print("   CONCLUSION DU TEST TrOCR MULTIFORMAT")
print("=" * 80)

print("\n[Info] TrOCR EST EXCELLENT POUR :")
print("  [OK] Texte imprime standard (polices courantes)")
print("  [OK] Architecture state-of-the-art (transformers)")
print("  [OK] Bonne generalisation sur texte propre")
print("  [OK] Modeles pre-entraines de haute qualite")
print("  [OK] Support de nombreuses langues")

print("\n[!] LIMITATIONS TrOCR :")
print("  [!] Modeles tres volumineux (telechargement long)")
print("  [!] Pas de score de confiance (evaluation qualitative)")
print("  [!] Plus lent que les solutions traditionnelles")
print("  [!] Difficulte avec texte decoratif/complexe")
print("  [!] Necessite plus de ressources (GPU recommande)")

print("\n[Cible] RECOMMANDATIONS :")
print("  - Utiliser pour texte imprime de haute qualite")
print("  - Ideal pour documents numerises propres")
print("  - Bon pour recherche/benchmarks")
print("  - Utiliser GPU pour de meilleures performances")
print("  - Choisir modele adapte (small, base, large)")

print("\n[Config] COMPATIBILITE PAR TYPE :")
print("  - Optimal (texte standard) : Excellents resultats")
print("  - Standard : Bonne detection")
print("  - Moyen (italique/couleur) : Resultats variables")
print("  - Difficile (petit/special) : Faible compatibilite")
print("  - Complexe (documents) : Detection partielle")

print("\n[Lancement] AVANTAGES TECHNOLOGIQUES :")
print("  - Base sur transformers (architecture moderne)")
print("  - Fine-tuning possible sur donnees specifiques")
print("  - Bonne comprehension du contexte")
print("  - Evolution rapide (recherche active)")

print("\n" + "=" * 80)
print("   TEST TERMINÉ - Kinza Achaouachi")
print("=" * 80)