"""
SCRIPT PRINCIPAL - Tests Multiformat des 4 Solutions OCR
Auteur : Kinza Achaouachi
Description : Exécute tous les tests multiformat et génère un rapport comparatif
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

print("=" * 100)
print("   TESTS MULTIFORMAT COMPLETS - 4 SOLUTIONS OCR")
print("=" * 100)
print("   Ce script exécute les tests multiformat pour chaque solution OCR")
print("   et génère un rapport comparatif détaillé.")
print("=" * 100)

# Créer le dossier de résultats
results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

# Fichiers de test à exécuter
test_files = [
    {
        "name": "Docling Multiformat",
        "file": "test_docling_multiformat.py",
        "description": "Test Docling sur fichiers texte et images",
        "expected_time": "2-5 minutes"
    },
    {
        "name": "PaddleOCR Multiformat",
        "file": "test_paddleocr_multiformat.py",
        "description": "Test PaddleOCR sur images variées",
        "expected_time": "3-7 minutes"
    },
    {
        "name": "EasyOCR Multiformat",
        "file": "test_easyocr_multiformat.py",
        "description": "Test EasyOCR multi-langues sur images",
        "expected_time": "5-10 minutes"
    },
    {
        "name": "TrOCR Multiformat",
        "file": "test_trocr_multiformat.py",
        "description": "Test TrOCR (transformers) sur images sélectionnées",
        "expected_time": "5-15 minutes (inclut téléchargement modèle)"
    }
]

# ── Étape 1 : Vérification des fichiers ──────────────
print("\n[1/5] Vérification des fichiers de test...")
print("-" * 100)

available_tests = []
for test in test_files:
    if Path(test["file"]).exists():
        available_tests.append(test)
        print(f"    [OK] {test['name']}: {test['file']}")
        print(f"        Description: {test['description']}")
        print(f"        Temps estimé: {test['expected_time']}")
    else:
        print(f"    [X] {test['name']}: Fichier non trouve - {test['file']}")

if not available_tests:
    print("\n    [!] Aucun fichier de test trouve!")
    print("    Executez d'abord la creation des scripts de test.")
    sys.exit(1)

print(f"\n    [Stats] {len(available_tests)}/4 tests disponibles")
print("    [Temps] Temps total estime: 15-35 minutes")

# ── Étape 2 : Configuration ──────────────
print("\n[2/5] Configuration...")
print("-" * 100)

print("\n    [!] AVERTISSEMENTS IMPORTANTS :")
print("    1. Premier lancement: Telechargement de modeles (peut prendre du temps)")
print("    2. TrOCR: Modele ~1.5GB, telechargement long au premier lancement")
print("    3. Docling/PaddleOCR: Telechargement modeles ~20-60 secondes")
print("    4. EasyOCR: Fonctionne sur CPU (plus lent), message normal")
print("    5. PaddleOCR: Necessite numpy 1.26.4 (incompatible numpy 2.x)")

print("\n    [Info] CONSEILS :")
print("    - Gardez une connexion internet stable")
print("    - Patientez pendant les telechargements")
print("    - Les messages d'avertissement sont normaux")
print("    - Les resultats sont sauvegardes automatiquement")

print("\n    Appuyez sur Entrée pour commencer les tests...")
input()

# ── Étape 3 : Exécution des tests ──────────────
print("\n[3/5] Exécution des tests...")
print("=" * 100)

test_results = []
global_start_time = time.time()

for i, test in enumerate(available_tests, 1):
    print(f"\n    [Test] TEST {i}/{len(available_tests)}: {test['name']}")
    print(f"    [Info] {test['description']}")
    print(f"    [Temps] Temps estime: {test['expected_time']}")
    print("    " + "-" * 80)
    
    test_start_time = time.time()
    
    try:
        # Exécuter le script Python
        print(f"    [Lancement] Demarrage de {test['file']}...")
        
        result = subprocess.run(
            [sys.executable, test["file"]],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        test_duration = time.time() - test_start_time
        
        # Analyser les résultats
        if result.returncode == 0:
            status = "succès"
            print(f"    [OK] TEST REUSSI en {test_duration:.0f}s")
            
            # Extraire des informations du résultat
            output_lines = result.stdout.split('\n')
            summary_lines = [line for line in output_lines if "TOTAL DES TESTS" in line or "Statistiques" in line or "Résultats" in line]
            
            if summary_lines:
                print(f"    [Stats] Resume :")
                for line in summary_lines[:3]:  # Afficher les 3 premières lignes de résumé
                    if line.strip():
                        print(f"        {line.strip()}")
            
        else:
            status = "échec"
            print(f"    [X] TEST ECHOUE en {test_duration:.0f}s")
            print(f"    Code d'erreur: {result.returncode}")
            
            if result.stderr:
                error_lines = result.stderr.split('\n')[:5]  # Afficher les 5 premières lignes d'erreur
                print(f"    Erreurs :")
                for line in error_lines:
                    if line.strip():
                        print(f"        {line.strip()}")
        
        # Sauvegarder le résultat du test
        test_results.append({
            "name": test["name"],
            "file": test["file"],
            "status": status,
            "duration": round(test_duration, 2),
            "returncode": result.returncode,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"    [Sauvegarde] Resultats enregistres")
        
    except Exception as e:
        test_duration = time.time() - test_start_time
        print(f"    [X] ERREUR D'EXECUTION: {e}")
        
        test_results.append({
            "name": test["name"],
            "file": test["file"],
            "status": "erreur",
            "duration": round(test_duration, 2),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    
    # Pause entre les tests
    if i < len(available_tests):
        print(f"\n    [Pause] Pause avant le test suivant... (3 secondes)")
        time.sleep(3)

global_duration = time.time() - global_start_time

# ── Étape 4 : Collecte des résultats ──────────────
print("\n[4/5] Collecte et analyse des résultats...")
print("-" * 100)

# Chercher les fichiers de résultats JSON
result_files = list(results_dir.glob("*_multiformat_results.json"))
detailed_results = []

print(f"    [Dossier] Fichiers de resultats trouves: {len(result_files)}")

for result_file in result_files:
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        tool_name = data.get("tool", "Inconnu")
        success_rate = data.get("success_rate", 0)
        total_tests = data.get("total_tests", 0)
        
        detailed_results.append({
            "tool": tool_name,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "file": result_file.name,
            "test_date": data.get("test_date", "")
        })
        
        print(f"    [Fichier] {tool_name}: {success_rate:.1f}% succes ({total_tests} tests)")
        
    except Exception as e:
        print(f"    [!] Erreur lecture {result_file.name}: {e}")

# ── Étape 5 : Rapport comparatif ──────────────
print("\n[5/5] Génération du rapport comparatif...")
print("=" * 100)

# Statistiques globales
successful_tests = [r for r in test_results if r["status"] == "succès"]
failed_tests = [r for r in test_results if r["status"] in ["échec", "erreur"]]

print("\n    [Stats] RAPPORT GLOBAL DES TESTS")
print("    " + "=" * 50)
print(f"    [Temps] Temps total d'execution: {global_duration:.0f} secondes")
print(f"    [OK] Tests reussis: {len(successful_tests)}/{len(test_results)}")
print(f"    [X] Tests echoues: {len(failed_tests)}/{len(test_results)}")
print(f"    [Cible] Taux de reussite global: {len(successful_tests)/len(test_results)*100:.1f}%")

print("\n    [Info] DETAIL PAR SOLUTION OCR :")
print("    " + "-" * 50)

for test in test_results:
    status_icon = "[OK]" if test["status"] == "succès" else "[X]"
    print(f"    {status_icon} {test['name']}: {test['status']} en {test['duration']:.0f}s")

print("\n    [Trophee] COMPARAISON DES PERFORMANCES :")
print("    " + "-" * 50)

if detailed_results:
    # Trier par taux de succès
    detailed_results.sort(key=lambda x: x["success_rate"], reverse=True)
    
    for i, result in enumerate(detailed_results, 1):
        rank_icon = "[1er]" if i == 1 else "[2e]" if i == 2 else "[3e]" if i == 3 else "[Stats]"
        print(f"    {rank_icon} {result['tool']}: {result['success_rate']:.1f}% succes")
else:
    print("    [!] Aucun resultat detaille trouve")

print("\n    [Dossier] FICHIERS DE RESULTATS GENERES :")
print("    " + "-" * 50)

for result_file in result_files:
    file_size = result_file.stat().st_size / 1024  # Taille en KB
    print(f"    - {result_file.name} ({file_size:.1f} KB)")

# Générer un rapport JSON global
global_report = {
    "report_date": datetime.now().isoformat(),
    "total_execution_time": global_duration,
    "total_tests_executed": len(test_results),
    "successful_tests": len(successful_tests),
    "failed_tests": len(failed_tests),
    "success_rate": len(successful_tests)/len(test_results)*100 if test_results else 0,
    "test_execution_results": test_results,
    "detailed_results": detailed_results,
    "result_files": [str(f.name) for f in result_files]
}

report_file = results_dir / "global_multiformat_report.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(global_report, f, indent=2, ensure_ascii=False)

print(f"\n    [Fichier] Rapport global sauvegarde: {report_file}")

# ── Conclusion ────────────────────────────────────
print("\n" + "=" * 100)
print("   CONCLUSION FINALE - TESTS MULTIFORMAT OCR")
print("=" * 100)

print("\n    [Cible] RECOMMANDATIONS FINALES :")
print("    " + "-" * 50)

if detailed_results:
    best_tool = max(detailed_results, key=lambda x: x["success_rate"])
    print(f"    1. MEILLEUR TAUX DE SUCCES: {best_tool['tool']} ({best_tool['success_rate']:.1f}%)")
    
    # Recommandations par cas d'usage
    print("\n    2. CHOIX PAR CAS D'USAGE :")
    print("       - Documents structures (PDF, DOCX, texte) -> DOCLING")
    print("       - Images avec texte standard -> PADDLEOCR")
    print("       - Multi-langues et facilite d'utilisation -> EASYOCR")
    print("       - Texte imprime haute qualite/recherche -> TrOCR")
    
    print("\n    3. TEMPS D'EXECUTION :")
    print(f"       - Total: {global_duration:.0f} secondes")
    print(f"       - Moyenne par test: {global_duration/len(test_results):.0f}s")
    
    print("\n    4. PROCHAINES ETAPES :")
    print("       - Analyser les fichiers de resultats JSON")
    print("       - Comparer les performances sur types specifiques")
    print("       - Tester avec vos propres fichiers")
    print("       - Optimiser la configuration pour votre usage")

print("\n    [Dossier] FICHIERS DISPONIBLES :")
print("    " + "-" * 50)
print(f"    - Rapport global: test_results/global_multiformat_report.json")
print(f"    - Resultats detailles: {len(result_files)} fichiers dans test_results/")
print(f"    - Logs d'execution: disponibles dans la console")

print("\n    [Succes] TESTS MULTIFORMAT TERMINES AVEC SUCCES !")
print("\n" + "=" * 100)
print("   Kinza Achaouachi - " + datetime.now().strftime("%d/%m/%Y %H:%M"))
print("=" * 100)