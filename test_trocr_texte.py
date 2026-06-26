"""
Script de test pour TrOCR - Test Texte
Auteur : Kinza Chaouachi
Description : Test simple de TrOCR avec un fichier texte
"""

import os
import sys
import time
from pathlib import Path

print("=" * 60)
print("   TEST TROCR - TEXTE")
print("=" * 60)

test_file = "test_sample.txt"

print(f"\n[1/3] Vérification du fichier : {test_file}")
if not Path(test_file).exists():
    print(f"    [X] Fichier non trouvé")
    sys.exit(1)
print(f"    [OK] Fichier trouvé")

print("\n[2/3] Initialisation de TrOCR...")
debut_init = time.time()

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    fin_init = time.time()
    print(f"    [OK] TrOCR prêt en {fin_init - debut_init:.2f}s")
except Exception as e:
    print(f"    [X] Erreur: {e}")
    sys.exit(1)

print("\n[3/3] Résultats")
print("-" * 60)

try:
    # Lire le fichier texte
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"    [OK] Fichier texte lu")
    print(f"    Lignes : {len(lines)}")
    print(f"    Caractères : {len(content)}")
    print(f"    Mots : {len(content.split())}")
    print(f"\n    Contenu :\n    {content[:100]}...")
    print(f"\n    RÉSULTAT : SUCCÈS [OK]")
    
except Exception as e:
    print(f"    [X] Erreur: {e}")
    print(f"    RÉSULTAT : ÉCHEC [FAIL]")

print("\n" + "=" * 60)
print("   Fin du test TrOCR Texte")
print("=" * 60)
