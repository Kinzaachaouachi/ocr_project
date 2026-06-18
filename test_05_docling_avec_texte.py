"""
TEST 05: DOCLING AVEC FICHIER TEXTE
Test de Docling sur un fichier texte unique
"""

from docling.document_converter import DocumentConverter
from pathlib import Path
import time

print("="*80)
print("TEST 05: DOCLING AVEC FICHIER TEXTE")
print("="*80)

print("\n[ÉTAPE 1] Création d'un fichier texte de test...")
print("-" * 80)

# Créer un dossier pour les fichiers texte
test_dir = Path("test_files")
test_dir.mkdir(exist_ok=True)

# Créer un fichier texte simple
test_file_path = test_dir / "test_document.txt"

test_content = """DOCUMENT DE TEST POUR DOCLING

Titre Principal
===============

Ceci est un document texte de test pour évaluer les capacités de Docling.

Sections:
---------
1. Introduction
2. Contenu principal
3. Conclusion

Paragraphe 1:
Le texte structuré permet à Docling d'extraire et de formater le contenu correctement.

Paragraphe 2:
Les fichiers texte sont une bonne base pour tester les fonctionnalités d'extraction.

Listes:
- Premier élément
- Deuxième élément
- Troisième élément

Conclusion:
Ce test démontre l'utilisation de Docling avec des fichiers texte simples.

Fin du document.
"""

with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write(test_content)

print(f"✓ Fichier texte créé: {test_file_path}")
print(f"  Contenu: {len(test_content)} caractères")
print(f"  Aperçu des 100 premiers caractères:")
print(f"  '{test_content[:100]}...'")

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

print("\n[ÉTAPE 3] Conversion du fichier texte avec Docling...")
print("-" * 80)

try:
    process_start = time.time()
    result = converter.convert(str(test_file_path))
    process_time = time.time() - process_start
    
    print(f"✓ Conversion réussie ({process_time:.2f}s)")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    exit(1)

print("\n[ÉTAPE 4] Résultats de l'extraction...")
print("-" * 80)

try:
    markdown_content = result.document.export_to_markdown()
    json_content = result.document.export_to_dict()
    
    num_chars = len(markdown_content)
    num_blocks = len(json_content.get('blocks', []))
    
    print(f"\n✓ Contenu extrait (Markdown):")
    print("-" * 80)
    print(markdown_content)
    print("-" * 80)
    
    print(f"\nSTATISTIQUES:")
    print(f"  - Blocs de contenu détectés: {num_blocks}")
    print(f"  - Caractères extraits: {num_chars}")
    print(f"  - Temps de traitement: {process_time:.2f}s")
    print(f"  - Temps total (init + traitement): {init_time + process_time:.2f}s")
    
except Exception as e:
    print(f"✗ Erreur lors de l'extraction: {e}")
    exit(1)

print("\n" + "="*80)
print("✓ TEST 05 TERMINÉ AVEC SUCCÈS")
print("="*80)
