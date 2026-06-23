"""
Script de test pour TrOCR (Transformer-based OCR)
Auteur : Kinza Achaouachi (mis à jour)
Description : Test simple de TrOCR avec une image de démonstration
"""

import os
import sys
import time
from PIL import Image

print("=" * 60)
print("   TEST TROCR (Hugging Face Transformers)")
print("=" * 60)

# Définir le chemin de l'image de test
image_path = os.path.join("demo_images", "demo_text.png")
if not os.path.exists(image_path):
    image_path = "test_image.png"

print(f"\n[1/3] Utilisation de l'image : {image_path}")

# ── Étape 1 : Initialiser TrOCR ──────────────────────────────
print("\n[2/3] Initialisation de TrOCR (modèle: microsoft/trocr-small-printed)...")
print("    Remarque : Le premier chargement va télécharger le modèle (~246MB).")
debut_init = time.time()

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch

    # Utiliser le GPU si disponible, sinon CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"    Périphérique utilisé : {device.upper()}")

    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed").to(device)

    fin_init = time.time()
    print(f"    TrOCR prêt en {fin_init - debut_init:.2f}s")

    # ── Étape 2 : Lancer l'OCR ────────────────────────────────────────
    print("\n[3/3] Reconnaissance du texte en cours...")
    debut_ocr = time.time()

    # Charger l'image et la convertir en RGB
    image = Image.open(image_path).convert("RGB")
    
    # Prétraitement de l'image
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
    
    # Génération du texte
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    fin_ocr = time.time()
    duree = fin_ocr - debut_ocr
    print(f"    OCR terminé en {duree:.2f}s")

    # ── Étape 3 : Afficher les résultats ─────────────────────────────
    print("\nRésultats :")
    print("-" * 60)
    print(f"  Texte reconnu : {generated_text}")
    print(f"  Durée OCR     : {duree:.2f}s")
    print("-" * 60)
    
    # TrOCR est conçu pour des lignes de texte uniques, donc on vérifie s'il y a du contenu reconnu
    if generated_text.strip():
        print("\n  RÉSULTAT : SUCCÈS [OK]")
    else:
        print("  Aucun texte détecté.")
        print("\n  RÉSULTAT : ÉCHEC [FAIL]")

except Exception as e:
    print(f"\n  ERREUR lors de l'exécution du test : {e}")
    print("\n  RÉSULTAT : ÉCHEC ✗")

print("\n" + "=" * 60)
print("   Fin du test TrOCR")
print("=" * 60)
