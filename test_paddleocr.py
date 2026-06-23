"""
Script de test pour PaddleOCR
Auteur : Kinza Achaouachi
Description : Test simple de PaddleOCR avec une image générée automatiquement
"""

import os
import sys
import time

# Désactiver oneDNN pour éviter les conflits Windows
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
from PIL import Image, ImageDraw, ImageFont

print("=" * 60)
print("   TEST PADDLEOCR - Kinza Achaouachi")
print("=" * 60)

# ── Étape 1 : Créer une image de test avec du texte ──────────────
print("\n[1/4] Création de l'image de test...")

img = Image.new("RGB", (600, 200), color=(255, 255, 255))
draw = ImageDraw.Draw(img)

texte = "Bonjour, je teste PaddleOCR avec Python !"
draw.text((30, 40),  texte,              fill=(0, 0, 0))
draw.text((30, 100), "PaddleOCR v2.7",   fill=(30, 100, 200))
draw.text((30, 140), "Test reussi !",    fill=(0, 150, 0))

image_path = "test_image.png"
img.save(image_path)
print(f"    Image créée : {image_path} (600x200 px)")

# ── Étape 2 : Initialiser PaddleOCR ──────────────────────────────
print("\n[2/4] Initialisation de PaddleOCR...")
debut_init = time.time()

from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    lang="fr",          # langue française
    use_gpu=False,
    show_log=False
)

fin_init = time.time()
print(f"    PaddleOCR prêt en {fin_init - debut_init:.2f}s")

# ── Étape 3 : Lancer l'OCR ────────────────────────────────────────
print("\n[3/4] Reconnaissance du texte en cours...")
debut_ocr = time.time()

resultats = ocr.ocr(image_path, cls=True)

fin_ocr = time.time()
duree = fin_ocr - debut_ocr
print(f"    OCR terminé en {duree:.2f}s")

# ── Étape 4 : Afficher les résultats ─────────────────────────────
print("\n[4/4] Résultats :")
print("-" * 60)

if resultats and resultats[0]:
    scores = []
    for ligne in resultats[0]:
        boite, (texte_detect, score) = ligne
        scores.append(score)
        print(f"  Texte   : {texte_detect}")
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
print("   Fin du test PaddleOCR")
print("=" * 60)
