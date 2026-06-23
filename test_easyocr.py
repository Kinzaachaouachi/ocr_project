"""
Script de test pour EasyOCR
Auteur : Kinza Achaouachi (mis à jour)
Description : Test simple d'EasyOCR avec une image de démonstration
"""

import os
import sys
import time
import easyocr

print("=" * 60)
print("   TEST EASYOCR")
print("=" * 60)

# Définir le chemin de l'image de test
image_path = os.path.join("demo_images", "demo_text.png")
if not os.path.exists(image_path):
    # Si le fichier n'existe pas, on tente avec test_image.png
    image_path = "test_image.png"

print(f"\n[1/3] Utilisation de l'image : {image_path}")

# ── Étape 1 : Initialiser EasyOCR ──────────────────────────────
print("\n[2/3] Initialisation de EasyOCR (langues: fr, en)...")
debut_init = time.time()

# Initialisation du lecteur pour le français et l'anglais
reader = easyocr.Reader(['fr', 'en'], gpu=False)

fin_init = time.time()
print(f"    EasyOCR prêt en {fin_init - debut_init:.2f}s")

# ── Étape 2 : Lancer l'OCR ────────────────────────────────────────
print("\n[3/3] Reconnaissance du texte en cours...")
debut_ocr = time.time()

resultats = reader.readtext(image_path)

fin_ocr = time.time()
duree = fin_ocr - debut_ocr
print(f"    OCR terminé en {duree:.2f}s")

# ── Étape 3 : Afficher les résultats ─────────────────────────────
print("\nRésultats :")
print("-" * 60)

if resultats:
    scores = []
    for (bbox, texte_detect, score) in resultats:
        scores.append(score)
        print(f"  Texte     : {texte_detect}")
        print(f"  Confiance : {score * 100:.1f}%")
        print()

    moyenne = sum(scores) / len(scores) * 100
    print("-" * 60)
    print(f"  Lignes détectées   : {len(scores)}")
    print(f"  Confiance moyenne  : {moyenne:.1f}%")
    print(f"  Durée OCR          : {duree:.2f}s")
    print("-" * 60)
    print("\n  RÉSULTAT : SUCCÈS [OK]")
else:
    print("  Aucun texte détecté.")
    print("\n  RÉSULTAT : ÉCHEC [FAIL]")

print("\n" + "=" * 60)
print("   Fin du test EasyOCR")
print("=" * 60)
