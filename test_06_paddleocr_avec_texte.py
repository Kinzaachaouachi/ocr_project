"""
TEST 06: PADDLEOCR AVEC FICHIER TEXTE (CONVERTIR EN IMAGE)
Test de PaddleOCR sur un fichier texte converti en image
"""

import os
os.environ['PADDLE_MKL_OPS'] = 'off'
os.environ['USE_MKLDNN'] = '0'

from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import time

print("="*80)
print("TEST 06: PADDLEOCR AVEC FICHIER TEXTE")
print("="*80)

print("\n[ÉTAPE 1] Création d'un fichier image depuis du texte...")
print("-" * 80)

# Créer un dossier pour les fichiers
test_dir = Path("test_files")
test_dir.mkdir(exist_ok=True)

# Texte à tester
test_text_content = """DOCUMENT DE TEST POUR PADDLEOCR

Titre Principal

Ceci est un document texte convertit en image
pour tester les capacités de reconnaissance de PaddleOCR.

Le texte structuré permet à PaddleOCR de reconnaître
et d'extraire le contenu correctement.

Sections principales:
- Introduction
- Contenu principal
- Conclusion

Conclusion: Test réussi!"""

# Créer l'image
try:
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_normal = ImageFont.truetype("arial.ttf", 20)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Écrire le texte sur l'image
    y_pos = 30
    lines = test_text_content.split('\n')
    
    for line in lines:
        if not line.strip():
            y_pos += 15
        elif line.isupper() and len(line) < 30:
            draw.text((30, y_pos), line, fill='black', font=font_title)
            y_pos += 40
        else:
            draw.text((30, y_pos), line, fill='black', font=font_normal)
            y_pos += 25
    
    test_image_path = test_dir / "test_text_image.png"
    img.save(test_image_path)
    
    print(f"✓ Image créée à partir du texte: {test_image_path}")
    print(f"  Dimensions: 800x600 pixels")
    print(f"  Contenu: {len(lines)} lignes de texte")
    
except Exception as e:
    print(f"✗ Erreur lors de la création de l'image: {e}")
    exit(1)

print("\n[ÉTAPE 2] Initialisation du modèle PaddleOCR...")
print("-" * 80)

try:
    init_start = time.time()
    ocr = PaddleOCR(lang='en')
    init_time = time.time() - init_start
    print(f"✓ Modèle PaddleOCR chargé avec succès")
    print(f"  Temps d'initialisation: {init_time:.2f}s")
except Exception as e:
    print(f"✗ Erreur: {e}")
    exit(1)

print("\n[ÉTAPE 3] Reconnaissance OCR de l'image contenant du texte...")
print("-" * 80)

try:
    process_start = time.time()
    result = ocr.ocr(str(test_image_path))
    process_time = time.time() - process_start
    
    print(f"✓ Reconnaissance réussie ({process_time:.2f}s)")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    exit(1)

print("\n[ÉTAPE 4] Résultats de la reconnaissance...")
print("-" * 80)

if result and result[0]:
    print(f"\n✓ Texte détecté: {len(result[0])} éléments reconnus\n")
    
    print("Résultats détaillés:")
    print("-" * 80)
    
    all_text = []
    for idx, line in enumerate(result[0], 1):
        text = line[1][0]
        confidence = line[1][1]
        all_text.append(text)
        print(f"  [{idx}] '{text}' (Confiance: {confidence:.2%})")
    
    confidences = [line[1][1] for line in result[0]]
    avg_confidence = sum(confidences) / len(confidences)
    
    print("-" * 80)
    print(f"\nTEXTE COMPLET RECONNU:")
    print("-" * 80)
    print(" ".join(all_text))
    print("-" * 80)
    
    print(f"\nSTATISTIQUES:")
    print(f"  - Nombre d'éléments: {len(result[0])}")
    print(f"  - Confiance moyenne: {avg_confidence:.2%}")
    print(f"  - Confiance min: {min(confidences):.2%}")
    print(f"  - Confiance max: {max(confidences):.2%}")
    print(f"  - Temps de traitement: {process_time:.2f}s")
    print(f"  - Temps total (init + traitement): {init_time + process_time:.2f}s")
    
else:
    print("⚠ Aucun texte détecté dans l'image")

print("\n" + "="*80)
print("✓ TEST 06 TERMINÉ AVEC SUCCÈS")
print("="*80)
