import os
import sys
import time
from PIL import Image

print("=" * 60)
print("   TEST TROCR (Hugging Face Transformers)")
print("=" * 60)


image_path = os.path.join("demo_images", "demo_text.png")
if not os.path.exists(image_path):
    image_path = "test_image.png"

print(f"\n[1/3] Utilisation de l'image : {image_path}")


print("\n[2/3] Initialisation de TrOCR (modèle: microsoft/trocr-small-printed)...")
print("    Remarque : Le premier chargement va télécharger le modèle (~246MB).")
debut_init = time.time()

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch

   
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"    Périphérique utilisé : {device.upper()}")

    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed").to(device)

    fin_init = time.time()
    print(f"    TrOCR prêt en {fin_init - debut_init:.2f}s")

    
    print("\n[3/3] Reconnaissance du texte en cours...")
    debut_ocr = time.time()

   
    image = Image.open(image_path).convert("RGB")
    
    
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
    
   
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    fin_ocr = time.time()
    duree = fin_ocr - debut_ocr
    print(f"    OCR terminé en {duree:.2f}s")

   
    print("\nRésultats :")
    print("-" * 60)
    print(f"  Texte reconnu : {generated_text}")
    print(f"  Durée OCR     : {duree:.2f}s")
    print("-" * 60)
    
    
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
