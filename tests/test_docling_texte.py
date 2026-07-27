import os
import sys
import time
from pathlib import Path

print("=" * 60)
print("   TEST DOCLING - TEXTE")
print("=" * 60)

test_file = "test_sample.txt"

print(f"\n[1/3] Vérification du fichier : {test_file}")
if not Path(test_file).exists():
    print(f"    [X] Fichier non trouvé")
    sys.exit(1)
print(f"    [OK] Fichier trouvé")

print("\n[2/3] Initialisation de Docling...")
debut_init = time.time()

try:
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    fin_init = time.time()
    print(f"   Docling prêt en {fin_init - debut_init:.2f}s")
except Exception as e:
    print(f"   Erreur: {e}")
    sys.exit(1)

print("\n[3/3] Résultats")
print("-" * 60)

try:
    debut_ocr = time.time()
    result = converter.convert(test_file)
    text = result.document.export_to_markdown().strip()
    fin_ocr = time.time()
    
    duree = fin_ocr - debut_ocr
    print(f"    Fichier texte converti en {duree:.2f}s")
    print(f"    Caractères : {len(text)}")
    print(f"    Lignes : {len(text.split(chr(10)))}")
    print(f"\n    Contenu :\n    {text[:150]}...")
    print(f"\n    RÉSULTAT : SUCCÈS [OK]")
    
except Exception as e:
    print(f"    Erreur: {e}")
    print(f"    RÉSULTAT : ÉCHEC [FAIL]")

print("\n" + "=" * 60)
print("   Fin du test Docling Texte")
print("=" * 60)
