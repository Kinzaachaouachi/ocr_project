"""
TEST 01: DOCLING AVEC IMAGE
Test de Docling sur l'image de démonstration existante
"""

from docling.document_converter import DocumentConverter
from pathlib import Path
import time

print("="*80)
print("TEST 01: DOCLING AVEC IMAGE")
print("="*80)

print("\n[ÉTAPE 1] Vérification de l'image existante...")
print("-" * 80)

demo_dir = Path("demo_images")
test_image_path = demo_dir / "demo_text.png"

if not test_image_path.exists():
    print(f"✗ Image non trouvée: {test_image_path}")
    exit(1)

print(f"✓ Image trouvée: {test_image_path}")
print(f"  Localisation: demo_images/demo_text.png")

print("\n[ÉTAPE 2] Initialisation de DocumentConverter...")
print("-" * 80)

try:
    init_start = time.time()
    converter = DocumentConverter()
    init_time = time.time() - init_start
    print(f"✓ DocumentConverter chargé avec succès")
    print(f"  Temps d'initialisation: {init_time:.2f}s")
except Exception as e:
    print(f"✗ Erreur: {e}")
    exit(1)

print("\n[ÉTAPE 3] Conversion de l'image avec Docling...")
print("-" * 80)

try:
    process_start = time.time()
    result = converter.convert(str(test_image_path))
    process_time = time.time() - process_start
    
    markdown_content = result.document.export_to_markdown()
    json_content = result.document.export_to_dict()
    
    num_chars = len(markdown_content)
    num_blocks = len(json_content.get('blocks', []))
    
    print(f"✓ Conversion réussie ({process_time:.2f}s)")
    print(f"  Blocs détectés: {num_blocks}")
    print(f"  Caractères extraits: {num_chars}")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    exit(1)

print("\n[ÉTAPE 4] Résultats de l'extraction...")
print("-" * 80)

print(f"\n✓ Contenu extrait (Markdown):")
print("-" * 80)
print(markdown_content)
print("-" * 80)

print(f"\nSTATISTIQUES:")
print(f"  - Blocs de contenu: {num_blocks}")
print(f"  - Caractères totaux: {num_chars}")
print(f"  - Temps de traitement: {process_time:.2f}s")
print(f"  - Temps total (init + traitement): {init_time + process_time:.2f}s")

print("\n" + "="*80)
print("✓ TEST 01 TERMINÉ AVEC SUCCÈS")
print("="*80)
