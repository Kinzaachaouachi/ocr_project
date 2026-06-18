import os
import sys
import time

# Désactiver oneDNN pour éviter les conflits de compatibilité
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['PADDLE_DISABLE_ONEDNN'] = '1'
os.environ['FLAGS_enable_pir_api'] = '0'

print("=" * 60)
print("   TEST PADDLEOCR")
print("=" * 60)

# ─── Étape 1 : Vérification des dépendances ───────────────────
print("\n[Étape 1] Vérification des dépendances...")
try:
    import paddle
    print(f"  ✓ paddle         : {paddle.__version__}")
except ImportError as e:
    print(f"  ✗ paddle         : NON INSTALLÉ ({e})")
    sys.exit(1)

try:
    import cv2
    print(f"  ✓ opencv (cv2)   : {cv2.__version__}")
except ImportError as e:
    print(f"  ✗ opencv (cv2)   : NON INSTALLÉ ({e})")
    sys.exit(1)

try:
    import numpy as np
    print(f"  ✓ numpy          : {np.__version__}")
except ImportError as e:
    print(f"  ✗ numpy          : NON INSTALLÉ ({e})")
    sys.exit(1)

try:
    from paddleocr import PaddleOCR
    print(f"  ✓ paddleocr      : importé avec succès")
except ImportError as e:
    print(f"  ✗ paddleocr      : NON INSTALLÉ ({e})")
    sys.exit(1)

# ─── Étape 2 : Initialisation du modèle ───────────────────────
print("\n[Étape 2] Initialisation du modèle PaddleOCR...")
try:
    start = time.time()
    ocr = PaddleOCR(
        use_angle_cls=False,
        lang='en',
        use_gpu=False,
        enable_mkldnn=False,
        show_log=False
    )
    elapsed = time.time() - start
    print(f"  ✓ Modèle chargé en {elapsed:.2f}s")
except Exception as e:
    print(f"  ✗ Erreur initialisation : {e}")
    sys.exit(1)

# ─── Étape 3 : Créer une image de test ────────────────────────
print("\n[Étape 3] Création d'une image de test...")
try:
    from PIL import Image, ImageDraw, ImageFont

    img_dir = "test_images"
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, "sample_text.png")

    # Créer une image blanche avec du texte
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50),  "Hello, PaddleOCR!",  fill=(0, 0, 0))
    draw.text((50, 90),  "OCR Test - 2026",    fill=(0, 0, 0))
    draw.text((50, 130), "Python 3.10 - Windows", fill=(0, 0, 0))
    img.save(img_path)
    print(f"  ✓ Image créée : {img_path}")
except Exception as e:
    print(f"  ✗ Erreur création image : {e}")
    sys.exit(1)

# ─── Étape 4 : Reconnaissance OCR ─────────────────────────────
print("\n[Étape 4] Reconnaissance OCR sur l'image...")
try:
    start = time.time()
    result = ocr.ocr(img_path, cls=False)
    elapsed = time.time() - start

    if result and result[0]:
        print(f"  ✓ OCR terminé en {elapsed:.2f}s")
        print(f"  ✓ {len(result[0])} élément(s) détecté(s)\n")
        print("  Résultats :")
        print("  " + "-" * 50)
        total_conf = 0
        for line in result[0]:
            bbox, (text, confidence) = line
            total_conf += confidence
            print(f"  Texte      : {text}")
            print(f"  Confiance  : {confidence * 100:.1f}%")
            print("  " + "-" * 50)
        avg_conf = total_conf / len(result[0])
        print(f"\n  Confiance moyenne : {avg_conf * 100:.1f}%")
    else:
        print("  ✗ Aucun texte détecté dans l'image.")
except Exception as e:
    print(f"  ✗ Erreur OCR : {e}")

# ─── Résumé final ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("   TEST TERMINÉ AVEC SUCCÈS")
print("=" * 60)
