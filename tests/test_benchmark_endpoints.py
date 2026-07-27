"""
Script de test pour vérifier les endpoints de benchmark
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Test login et récupération du token"""
    print("🔐 Test de connexion...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Connexion réussie - Token: {data['token'][:20]}...")
        return data['token']
    else:
        print(f"❌ Échec de connexion: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return None

def test_olm_data(token):
    """Test de l'endpoint de données OLM"""
    print("\n📊 Test de l'endpoint données OLM...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/olm-report/data?include_user_stats=true",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Données OLM récupérées")
        print(f"   Nombre de modèles dans la matrice: {len(data.get('benchmark_matrix', []))}")
        print(f"   Statistiques utilisateur incluses: {'user_stats' in data}")
        return True
    else:
        print(f"❌ Échec récupération données OLM: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_olm_pdf(token):
    """Test du téléchargement PDF OLM"""
    print("\n📄 Test téléchargement PDF OLM...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/olm-report/download/pdf?include_user_stats=false",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ PDF OLM généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération PDF OLM: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_olm_docx(token):
    """Test du téléchargement Word OLM"""
    print("\n📝 Test téléchargement Word OLM...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/olm-report/download/docx?include_user_stats=false",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Word OLM généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération Word OLM: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_local_benchmark_pdf(token):
    """Test du téléchargement PDF benchmark local"""
    print("\n📄 Test téléchargement PDF benchmark local...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/local-benchmark/download/pdf",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ PDF benchmark local généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération PDF local: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_local_benchmark_docx(token):
    """Test du téléchargement Word benchmark local"""
    print("\n📝 Test téléchargement Word benchmark local...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/local-benchmark/download/docx",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Word benchmark local généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération Word local: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_local_benchmark_excel(token):
    """Test du téléchargement Excel benchmark local"""
    print("\n📊 Test téléchargement Excel benchmark local...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/local-benchmark/download/excel",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Excel benchmark local généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération Excel local: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def test_local_benchmark_csv(token):
    """Test du téléchargement CSV benchmark local"""
    print("\n📋 Test téléchargement CSV benchmark local...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/local-benchmark/download/csv",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ CSV benchmark local généré avec succès")
        print(f"   Taille: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Échec génération CSV local: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def main():
    print("=" * 60)
    print("TEST DES ENDPOINTS DE BENCHMARK")
    print("=" * 60)
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Impossible de continuer sans token d'authentification")
        return
    
    # Test OLM endpoints
    results = []
    results.append(("Données OLM", test_olm_data(token)))
    results.append(("PDF OLM", test_olm_pdf(token)))
    results.append(("Word OLM", test_olm_docx(token)))
    
    # Test local benchmark endpoints
    results.append(("PDF Local", test_local_benchmark_pdf(token)))
    results.append(("Word Local", test_local_benchmark_docx(token)))
    results.append(("Excel Local", test_local_benchmark_excel(token)))
    results.append(("CSV Local", test_local_benchmark_csv(token)))
    
    # Summary
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés avec succès!")
    else:
        print(f"\n⚠️ {total - passed} test(s) ont échoué")

if __name__ == "__main__":
    main()
