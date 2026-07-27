#!/usr/bin/env python3
"""
Script de test pour créer un compte et envoyer la vérification.
"""
import sys
import os
from pathlib import Path

# Ajouter le chemin de l'application
sys.path.insert(0, str(Path(__file__).parent))

def test_account_creation():
    """Tester la création de compte avec envoi de vérification."""
    try:
        # Importer le service email modifié
        from app.services.email_service_working import send_email_verification_direct, send_otp_email_direct
        
        # Test email de vérification
        print("🧪 Test d'email de vérification...")
        test_email = "kinza.chaouachi04@gmail.com"
        test_link = "http://localhost:8000/verify-email?token=TEST_DIRECT_123"
        
        success = send_email_verification_direct(test_email, test_link, "Kinza Chaouachi")
        
        if success:
            print("✅ Email de vérification simulé avec succès")
        
        # Test code OTP
        print("\n🧪 Test de code OTP...")
        success_otp = send_otp_email_direct(test_email, "123456", "Kinza Chaouachi")
        
        if success_otp:
            print("✅ Code OTP simulé avec succès")
        
        print("\n🎉 Tests terminés !")
        print("💡 Les liens/codes s'affichent dans la console")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_account_creation()
