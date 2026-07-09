import requests
import time
from pathlib import Path

API_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_test(number, total, name):
    print(f"\n[{number}/{total}] {name}")
    print("-"*70)


def test_health():
    print_test(1, 11, "GET /health - Status API")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data['status']}")
            print(f" Version: {data['version']}")
            print(f" Models: {data['models_available']}")
            return True
        else:
            print(f" Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False


def test_models():
    print_test(2, 11, "GET /models - Liste des Modèles")
    
    try:
        response = requests.get(f"{API_URL}/models", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total models: {data['total']}")
            for model_id, info in data['models'].items():
                print(f" {info['name']}: {', '.join(info['supported_formats'])}")
            return True
        else:
            print(f" Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False


def test_extract(model, file_path, description):
   
    
    if not Path(file_path).exists():
        print(f" File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            data = {'model': model}
            
            t0 = time.time()
            response = requests.post(f"{API_URL}/extract", files=files, data=data, timeout=60)
            wall_time = round(time.time() - t0, 2)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f" Model: {result['model']}")
            print(f" File type: {result['file_type']}")
            print(f"Characters: {result['char_count']}")
            print(f"Words: {result['word_count']}")
            print(f"Time: {wall_time}s")
            print(f"Text preview: {result['text'][:60]}...")
            return True
        else:
            error = response.json()
            print(f" Error: {error.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f" Exception: {str(e)}")
        return False


def test_translate():
  
    print_test(10, 11, "POST /translate - Traduction Texte")
    
    try:
        data = {
            'text': 'Bonjour, ceci est un test de traduction.',
            'target_lang': 'en',
            'model': 'paddleocr'
        }
        
        response = requests.post(f"{API_URL}/translate", data=data, timeout=20)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f" Original: {result['original_text'][:50]}...")
            print(f" Translated: {result['translated_text']}")
            print(f" Language: {result['source_lang']} → {result['target_lang']}")
            return True
        else:
            error = response.json()
            print(f"Error: {error.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f" Exception: {str(e)}")
        return False


def test_translate_file():
    
    print_test(11, 11, "POST /translate - Traduction Fichier")
    
    file_path = "demo_images/demo_text.png"
    
    if not Path(file_path).exists():
        print(f" File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            data = {
                'target_lang': 'es',
                'model': 'paddleocr'
            }
            
            response = requests.post(f"{API_URL}/translate", files=files, data=data, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f" File: {result.get('file_name', 'N/A')}")
            print(f"Original preview: {result['original_text'][:50]}...")
            print(f"Translated preview: {result['translated_text'][:50]}...")
            print(f"Language: {result['source_lang']} → {result['target_lang']}")
            return True
        else:
            error = response.json()
            print(f" Error: {error.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f" Exception: {str(e)}")
        return False



def main():
    print_header("TEST COMPLET API OCR - TOUS LES ENDPOINTS")
    print(f"API URL: {API_URL}")
    print("Assurez-vous que le serveur tourne:")
    print("  uvicorn api.main:app --host 127.0.0.1 --port 8000")
    
    results = []
    
    results.append(("GET /health", test_health()))
    results.append(("GET /models", test_models()))

    print_test(3, 11, "POST /extract - PaddleOCR + Image")
    results.append(("PaddleOCR + Image", 
        test_extract("paddleocr", "demo_images/demo_text.png", "PaddleOCR sur image")))
    
    print_test(4, 11, "POST /extract - EasyOCR + Image")
    results.append(("EasyOCR + Image", 
        test_extract("easyocr", "demo_images/demo_text.png", "EasyOCR sur image")))
    
    print_test(5, 11, "POST /extract - Docling + Image")
    results.append(("Docling + Image", 
        test_extract("docling", "demo_images/demo_text.png", "Docling sur image")))
    
    print_test(6, 11, "POST /extract - TrOCR + Image")
    results.append(("TrOCR + Image", 
        test_extract("trocr", "demo_images/demo_text.png", "TrOCR sur image")))
    
    print_test(7, 11, "POST /extract - PaddleOCR + PDF")
    results.append(("PaddleOCR + PDF", 
        test_extract("paddleocr", "test_files/sample_document.pdf", "PaddleOCR sur PDF")))
    
    print_test(8, 11, "POST /extract - Docling + PDF")
    results.append(("Docling + PDF", 
        test_extract("docling", "test_files/sample_document.pdf", "Docling sur PDF")))
    
    print_test(9, 11, "POST /extract - Docling + TXT")
    results.append(("Docling + TXT", 
        test_extract("docling", "test_files/sample_text.txt", "Docling sur texte")))
   
    results.append(("POST /translate (text)", test_translate()))
    results.append(("POST /translate (file)", test_translate_file()))
    
    print_header("RÉSUMÉ DES TESTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}  {test_name}")
    
    print("\n" + "="*70)
    print(f"  Résultat: {passed}/{total} tests réussis ({int(passed/total*100)}%)")
    print("="*70)
    
    if passed == total:
        print("\n  TOUS LES TESTS PASSENT - API 100% FONCTIONNELLE!")
    else:
        print(f"\n  {total - passed} test(s) échoué(s)")
        print("  Vérifiez que le serveur est démarré et que les fichiers de test existent.")


if __name__ == "__main__":
    main()
