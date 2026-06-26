

import os
import sys
import time
from pathlib import Path

print("=" * 60)
print("   TEST DOCLING")
print("=" * 60)

# Chemins des fichiers de test
test_files = [
    ("demo_images/demo_text.png", "image"),
    ("test_image.png", "image"),
    ("test_sample.txt", "texte"),
]

print("\n[1/3] Initialisation de Docling...")
init_start = time.time()

try:
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    init_time = time.time() - init_start
    print(f"    [OK] Docling initialise en {init_time:.2f}s")
except Exception as e:
    print(f"    [X] Erreur: {e}")
    sys.exit(1)

print("\n[2/3] Tests sur fichiers...")
print("-" * 60)

success_count = 0

for file_path, file_type in test_files:
    if not Path(file_path).exists():
        print(f"    [?] {file_path} - non trouvé")
        continue
    
    print(f"    {file_path} ({file_type})")
    try:
        process_start = time.time()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown().strip()
        process_time = time.time() - process_start
        
        char_count = len(text)
        print(f"      [OK] {process_time:.2f}s - {char_count} caractères")
        success_count += 1
    except Exception as e:
        print(f"      [X] Erreur: {str(e)[:50]}")

print("\n[3/3] Résultats")
print("-" * 60)
print(f"    Fichiers traités : {success_count}")
if success_count > 0:
    print(f"    Statut : SUCCÈS [OK]")
else:
    print(f"    Statut : ÉCHEC [FAIL]")

print("\n" + "=" * 60)
print("   Fin du test Docling")
print("=" * 60)
