import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("   TEST DOCLING MULTIFORMAT - Kinza Achaouachi")
print("=" * 80)

results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

print("\n[1/6] Préparation des fichiers de test...")

test_files = []

text_file = Path("test_files/test_document.txt")
if not text_file.exists():
    print(f"    Création du fichier texte : {text_file}")
    text_file.parent.mkdir(exist_ok=True)
    
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)

test_files.append({
    "type": "Texte",
    "path": str(text_file),
    "description": "Fichier texte structuré"
})


corpus_dir = Path("corpus_test")
if corpus_dir.exists():
    image_files = list(corpus_dir.glob("*.png"))
    for i, img_file in enumerate(image_files[:3]):  
        test_files.append({
            "type": "Image",
            "path": str(img_file),
            "description": f"Image test {i+1}: {img_file.stem}"
        })

demo_image = Path("demo_images/demo_text.png")
if demo_image.exists():
    test_files.append({
        "type": "Image",
        "path": str(demo_image),
        "description": "Image de démonstration standard"
    })

print(f"    {len(test_files)} fichiers de test préparés")
for i, tf in enumerate(test_files, 1):
    print(f"    [{i}] {tf['type']}: {tf['description']}")

print("\n[2/6] Initialisation de DocumentConverter...")

try:
    from docling.document_converter import DocumentConverter
    import warnings
    warnings.filterwarnings('ignore')
    
    init_start = time.time()
    converter = DocumentConverter()
    init_time = time.time() - init_start
    
    print(f"    [OK] DocumentConverter initialise en {init_time:.2f}s")
    print("    Note : Le premier lancement télécharge les modèles (~20-60s)")
    
except Exception as e:
    print(f"    [X] Erreur d'initialisation : {e}")
    print("    Installation : pip install docling docling-core")
    sys.exit(1)

print("\n[3/6] Exécution des tests sur chaque fichier...")
print("-" * 80)

results = []
total_start = time.time()

for i, test_file in enumerate(test_files, 1):
    print(f"\n    Test {i}/{len(test_files)} : {test_file['description']}")
    print(f"    Type : {test_file['type']} | Fichier : {Path(test_file['path']).name}")
    
    file_result = {
        "file": test_file['path'],
        "type": test_file['type'],
        "description": test_file['description'],
        "status": "non testé"
    }
    
    try:
        if not Path(test_file['path']).exists():
            file_result["status"] = "échec"
            file_result["error"] = "Fichier non trouvé"
            print(f"    Fichier non trouve")
            continue
        
        process_start = time.time()
        result = converter.convert(test_file['path'])
        process_time = time.time() - process_start
        
        if hasattr(result, 'document'):
            doc = result.document
            markdown_content = ""
            if hasattr(doc, 'export_to_markdown'):
                markdown_content = doc.export_to_markdown()
            elif hasattr(doc, 'text'):
                markdown_content = doc.text
            else:
                markdown_content = str(doc)
            
            char_count = len(markdown_content)
            lines = [l for l in markdown_content.split('\n') if l.strip()]
            line_count = len(lines)
            
            file_result.update({
                "status": "succès",
                "processing_time": round(process_time, 2),
                "characters_extracted": char_count,
                "lines_extracted": line_count,
                "sample": lines[0] if lines else ""
            })
            
            print(f"      [OK] Succes : {process_time:.2f}s")
            print(f"        Caractères extraits : {char_count}")
            print(f"        Lignes extraites : {line_count}")
            if lines:
                sample = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]
                print(f"        Extrait : '{sample}'")
            
        else:
            file_result.update({
                "status": "succès_partiel",
                "processing_time": round(process_time, 2),
                "note": "Document converti mais structure non standard"
            })
            print(f"      [!] Succes partiel : {process_time:.2f}s")
            
    except Exception as e:
        file_result.update({
            "status": "échec",
            "error": str(e),
            "processing_time": 0
        })
        print(f"      [X] Echec : {e}")
    
    results.append(file_result)

total_time = time.time() - total_start

print("\n[4/6] Résultats détaillés par type de fichier...")
print("-" * 80)

type_results = {}
for res in results:
    file_type = res["type"]
    if file_type not in type_results:
        type_results[file_type] = []
    type_results[file_type].append(res)

for file_type, type_res in type_results.items():
    print(f"\n    [Dossier] Type : {file_type} ({len(type_res)} fichiers)")
    
    succès = [r for r in type_res if r["status"] == "succès"]
    partiels = [r for r in type_res if r["status"] == "succès_partiel"]
    échecs = [r for r in type_res if r["status"] == "échec"]
    
    print(f"       Succes : {len(succès)}")
    print(f"     Partiels : {len(partiels)}")
    print(f"       Echecs : {len(échecs)}")
    
    if succès:
        avg_time = sum(r.get("processing_time", 0) for r in succès) / len(succès)
        avg_chars = sum(r.get("characters_extracted", 0) for r in succès) / len(succès)
        print(f"      [Temps] Temps moyen : {avg_time:.2f}s")
        print(f"      [Note] Caracteres moyens : {avg_chars:.0f}")

print("\n[5/6] Statistiques globales...")
print("-" * 80)

succès_total = len([r for r in results if r["status"] == "succès"])
partiels_total = len([r for r in results if r["status"] == "succès_partiel"])
échecs_total = len([r for r in results if r["status"] == "échec"])

print(f"   TOTAL DES TESTS : {len(results)} fichiers")
print(f"    Succes complets : {succès_total}")
print(f"    Succes partiels : {partiels_total}")
print(f"     Echecs : {échecs_total}")
print(f"      Taux de succes : {(succès_total + partiels_total)/len(results)*100:.1f}%")
print(f"     Temps total : {total_time:.2f}s")
print(f"      Temps initialisation : {init_time:.2f}s")

print("\n[6/6] Sauvegarde des résultats...")

results_file = results_dir / "docling_multiformat_results.json"
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump({
        "test_date": datetime.now().isoformat(),
        "tool": "Docling",
        "total_tests": len(results),
        "success_rate": (succès_total + partiels_total)/len(results)*100,
        "total_time": total_time,
        "initialization_time": init_time,
        "results": results
    }, f, indent=2, ensure_ascii=False)

print(f"    [Fichier] Resultats sauvegardes : {results_file}")

print("\n" + "=" * 80)
print("   CONCLUSION DU TEST DOCLING MULTIFORMAT")
print("=" * 80)

print("\n DOCLING EST EXCELLENT POUR :")
print("   Fichiers texte structures")
print(" Extraction de documents en Markdown")
print("   Conservation de la structure (titres, listes, paragraphes)")
print("  Support multi-format (texte, images, PDF, DOCX)")

print("\n LIMITATIONS :")
print("  Plus lent pour les images simples")
print(" Necessite telechargement de modeles au premier lancement")
print("  Meilleur avec documents structures qu'images brutes")

print("\n[Cible] RECOMMANDATIONS :")
print("  - Utiliser pour documents PDF/DOCX/textes structures")
print("  - Parfait pour conversion vers Markdown/HTML")
print("  - Moins adapte aux images OCR simples")

print("\n" + "=" * 80)
print("   TEST TERMINÉ - Kinza Chaouachi")
print("=" * 80)