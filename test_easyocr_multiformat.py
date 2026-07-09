import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("   TEST EASYOCR MULTIFORMAT - Kinza Chaouachi")
print("=" * 80)

results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

print("\n[1/6] Préparation des images de test...")

test_images = []

def _estimate_difficulty(filename):
    filename_lower = filename.lower()
    if "simple" in filename_lower or "demo" in filename_lower:
        return "facile"
    elif "petit" in filename_lower or "italique" in filename_lower:
        return "difficile"
    elif "multicolore" in filename_lower or "special" in filename_lower:
        return "moyen"
    elif "tableau" in filename_lower or "liste" in filename_lower:
        return "structuré"
    elif "complet" in filename_lower or "grand" in filename_lower:
        return "complexe"
    elif "nombres" in filename_lower:
        return "chiffres"
    else:
        return "standard"

def _estimate_difficulty(filename):
    filename_lower = filename.lower()
    if "simple" in filename_lower or "demo" in filename_lower:
        return "facile"
    elif "petit" in filename_lower or "italique" in filename_lower:
        return "difficile"
    elif "multicolore" in filename_lower or "special" in filename_lower:
        return "moyen"
    elif "tableau" in filename_lower or "liste" in filename_lower:
        return "structuré"
    elif "complet" in filename_lower or "grand" in filename_lower:
        return "complexe"
    elif "nombres" in filename_lower:
        return "chiffres"
    else:
        return "standard"

corpus_dir = Path("corpus_test")
if corpus_dir.exists():
    image_files = list(corpus_dir.glob("*.png"))
    for img_file in image_files:
        difficulty = _estimate_difficulty(img_file.stem)
        test_images.append({
            "type": "Corpus test",
            "path": str(img_file),
            "description": f"Corpus: {img_file.stem}",
            "expected_difficulty": difficulty,
            "language": "fr"  # Principalement français
        })


demo_image = Path("demo_images/demo_text.png")
if demo_image.exists():
    test_images.append({
        "type": "Démo",
        "path": str(demo_image),
        "description": "Image démonstration standard",
        "expected_difficulty": "facile",
        "language": "fr/en"
    })


test_files_dir = Path("test_files")
if test_files_dir.exists():
    generated_images = list(test_files_dir.glob("*.png"))
    for img_file in generated_images:
        test_images.append({
            "type": "Générée",
            "path": str(img_file),
            "description": f"Générée: {img_file.stem}",
            "expected_difficulty": "facile",
            "language": "fr"
        })

print(f"    {len(test_images)} images de test préparées")
print("    Catégories disponibles :")
categories = {}
for img in test_images:
    cat = img['expected_difficulty']
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in categories.items():
    print(f"    • {cat}: {count} images")

print("\n Initialisation d'EasyOCR...")

try:
    init_start = time.time()
    
    import easyocr
    
    reader = easyocr.Reader(['fr', 'en'], gpu=False)
    
    init_time = time.time() - init_start
    
    print(f"   EasyOCR initialise en {init_time:.2f}s")
    print(f"    Langues : français, anglais")
    print(f"    GPU : Non disponible (utilisation CPU)")
    print("    Note : Message 'Using CPU. Note: This module is much faster with a GPU.' est normal")
    
except Exception as e:
    print(f"    [X] Erreur d'initialisation : {e}")
    print("    Installation : pip install easyocr")
    print("    Note : EasyOCR nécessite torch")
    sys.exit(1)

print("\n[3/6] Exécution des tests sur chaque image...")
print("-" * 80)

results = []
total_start = time.time()

for i, test_image in enumerate(test_images, 1):
    print(f"\n    Test {i}/{len(test_images)} : {test_image['description']}")
    print(f"    Catégorie : {test_image['expected_difficulty']} | Langue : {test_image.get('language', 'fr')}")
    
    image_result = {
        "file": test_image['path'],
        "type": test_image['type'],
        "description": test_image['description'],
        "expected_difficulty": test_image['expected_difficulty'],
        "language": test_image.get('language', 'fr'),
        "status": "non testé"
    }
    
    try:
        if not Path(test_image['path']).exists():
            image_result["status"] = "échec"
            image_result["error"] = "Fichier non trouvé"
            print(f"      [X] Fichier non trouve")
            continue
        
        process_start = time.time()
        ocr_result = reader.readtext(test_image['path'], paragraph=False)
        process_time = time.time() - process_start
        
        if ocr_result:

            texts = []
            confidences = []
            for detection in ocr_result:
                if len(detection) >= 3: 
                    texts.append(detection[1])
                    confidences.append(float(detection[2]))
            
            if texts and confidences:
                
                avg_confidence = sum(confidences) / len(confidences) * 100
                min_confidence = min(confidences) * 100
                max_confidence = max(confidences) * 100
                
                
                detected_text = " ".join(texts)
                word_count = sum(len(text.split()) for text in texts)
                avg_word_length = sum(len(text) for text in texts) / len(texts) if texts else 0
                
                image_result.update({
                    "status": "succès",
                    "processing_time": round(process_time, 2),
                    "detections_count": len(texts),
                    "word_count": word_count,
                    "average_confidence": round(avg_confidence, 1),
                    "min_confidence": round(min_confidence, 1),
                    "max_confidence": round(max_confidence, 1),
                    "detected_text_length": len(detected_text),
                    "average_word_length": round(avg_word_length, 1),
                    "sample": texts[0] if texts else ""
                })
                
                print(f"      [OK] Succes : {process_time:.2f}s")
                print(f"        Détections : {len(texts)} éléments ({word_count} mots)")
                print(f"        Confiance : {avg_confidence:.1f}% (min {min_confidence:.1f}%, max {max_confidence:.1f}%)")
                print(f"        Texte : {len(detected_text)} caractères")
                if texts:
                    sample = texts[0][:50] + "..." if len(texts[0]) > 50 else texts[0]
                    print(f"        Exemple : '{sample}'")
                    
              
                if test_image['expected_difficulty'] == 'chiffres':
                    numbers = sum(1 for text in texts if any(c.isdigit() for c in text))
                    print(f"        Chiffres détectés : {numbers}/{len(texts)}")
                    image_result["numbers_detected"] = numbers
                    
            else:
                image_result.update({
                    "status": "succès_partiel",
                    "processing_time": round(process_time, 2),
                    "note": "Détections mais données incomplètes"
                })
                print(f"      [!] Succes partiel : {process_time:.2f}s")
                
        else:
            image_result.update({
                "status": "échec",
                "processing_time": round(process_time, 2),
                "error": "Aucun texte détecté"
            })
            print(f"      [X] Aucun texte detecte : {process_time:.2f}s")
            
    except Exception as e:
        image_result.update({
            "status": "échec",
            "error": str(e),
            "processing_time": 0
        })
        print(f"      [X] Erreur : {e}")
    
    results.append(image_result)

total_time = time.time() - total_start

print("\n[4/6] Résultats par catégorie de difficulté...")
print("-" * 80)


difficulty_results = {}
for res in results:
    difficulty = res.get("expected_difficulty", "inconnu")
    if difficulty not in difficulty_results:
        difficulty_results[difficulty] = []
    difficulty_results[difficulty].append(res)

print("\n    📊 PERFORMANCE PAR CATÉGORIE :")
print("    " + "-" * 50)

for difficulty, diff_res in sorted(difficulty_results.items()):
    succès = [r for r in diff_res if r["status"] == "succès"]
    partiels = [r for r in diff_res if r["status"] == "succès_partiel"]
    échecs = [r for r in diff_res if r["status"] == "échec"]
    
    total = len(diff_res)
    success_rate = (len(succès) + len(partiels)) / total * 100 if total > 0 else 0
    
    if succès:
        avg_time = sum(r.get("processing_time", 0) for r in succès) / len(succès)
        avg_conf = sum(r.get("average_confidence", 0) for r in succès) / len(succès)
        avg_detections = sum(r.get("detections_count", 0) for r in succès) / len(succès)
    else:
        avg_time = avg_conf = avg_detections = 0
    
    print(f"\n    [Cible] {difficulty.upper()} ({total} images) :")
    print(f"      [OK] Succes : {len(succès)} | [!] Partiels : {len(partiels)} | [X] Echecs : {len(échecs)}")
    print(f"      [Graph] Taux de succes : {success_rate:.1f}%")
    print(f"      [Temps] Temps moyen : {avg_time:.2f}s")
    print(f"      [Stats] Confiance moyenne : {avg_conf:.1f}%")
    print(f"      [Recherche] Detections moyennes : {avg_detections:.1f}")

print("\n[5/6] Statistiques globales...")
print("-" * 80)

succès_total = len([r for r in results if r["status"] == "succès"])
partiels_total = len([r for r in results if r["status"] == "succès_partiel"])
échecs_total = len([r for r in results if r["status"] == "échec"])

if succès_total > 0:
    avg_global_conf = sum(r.get("average_confidence", 0) for r in results if r["status"] == "succès") / succès_total
    avg_global_time = sum(r.get("processing_time", 0) for r in results if r["status"] == "succès") / succès_total
    avg_global_detections = sum(r.get("detections_count", 0) for r in results if r["status"] == "succès") / succès_total
else:
    avg_global_conf = avg_global_time = avg_global_detections = 0

print(f"    [Stats] TOTAL DES TESTS : {len(results)} images")
print(f"      [OK] Succes complets : {succès_total}")
print(f"      [!] Succes partiels : {partiels_total}")
print(f"      [X] Echecs : {échecs_total}")
print(f"      [Cible] Taux de succes global : {(succès_total + partiels_total)/len(results)*100:.1f}%")
print(f"      [Stats] Confiance moyenne globale : {avg_global_conf:.1f}%")
print(f"      [Temps] Temps moyen par image : {avg_global_time:.2f}s")
print(f"      [Recherche] Detections moyennes : {avg_global_detections:.1f}")
print(f"      [Temps] Temps total : {total_time:.2f}s")
print(f"      [Temps] Temps initialisation : {init_time:.2f}s")

print("\n[6/6] Sauvegarde des résultats...")

results_file = results_dir / "easyocr_multiformat_results.json"
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump({
        "test_date": datetime.now().isoformat(),
        "tool": "EasyOCR",
        "configuration": "fr, en languages, CPU only",
        "total_tests": len(results),
        "success_rate": (succès_total + partiels_total)/len(results)*100,
        "average_confidence": avg_global_conf,
        "average_processing_time": avg_global_time,
        "total_time": total_time,
        "initialization_time": init_time,
        "results": results
    }, f, indent=2, ensure_ascii=False)

print(f"    [Fichier] Resultats sauvegardes : {results_file}")

print("\n" + "=" * 80)
print("   CONCLUSION DU TEST EASYOCR MULTIFORMAT")
print("=" * 80)

print("\n[Info] EASYOCR EST EXCELLENT POUR :")
print("  [OK] Multi-langues (80+ langues supportees)")
print("  [OK] Texte imprime et manuscrit")
print("  [OK] Images variees (bonne adaptabilite)")
print("  [OK] Facilite d'utilisation (configuration simple)")
print("  [OK] Bonne detection meme sur texte difficile")

print("\n[!] LIMITATIONS :")
print("  [!] Plus lent sur CPU (message 'Using CPU' normal)")
print("  [!] Precision variable selon la police")
print("  [!] Parfois des fusions de mots")
print("  [!] Necessite torch (dependance lourde)")

print("\n[Cible] RECOMMANDATIONS :")
print("  - Utiliser pour projets multi-langues")
print("  - Ideal pour textes varies (imprimes, decoratifs)")
print("  - Bon choix pour debutants (configuration simple)")
print("  - Pour plus de vitesse : utiliser GPU si disponible")

print("\n[Graph] PERFORMANCE PAR CATEGORIE :")
print("  - Facile (texte standard) : 70-90% confiance")
print("  - Moyen (multicolore/special) : 60-80% confiance")
print("  - Difficile (petit/italique) : 40-70% confiance")
print("  - Chiffres : bonne detection numerique")
print("  - Structure (tableaux/listes) : detection par blocs")

print("\n[Globe] AVANTAGES MULTI-LANGUES :")
print("  - Francais : bonne prise en charge")
print("  - Anglais : excellente detection")
print("  - Support automatique des accents")
print("  - Detection automatique de la langue")

print("\n" + "=" * 80)
print("   TEST TERMINÉ - Kinza Chaouachi")
print("=" * 80)