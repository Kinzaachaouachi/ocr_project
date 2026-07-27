#!/usr/bin/env python3
"""
Test de connexion à la base MySQL ocr_intelligence.
"""
import pymysql

def test_mysql_connection():
    """Tester la connexion à MySQL et vérifier la structure."""
    try:
        print("🔍 Test de connexion à MySQL...")
        
        # Connexion à la base
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='ocr_intelligence',
            charset='utf8mb4'
        )
        
        print("✅ Connexion MySQL réussie !")
        
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f"📊 Tables trouvées: {[table[0] for table in tables]}")
        
        # Vérifier la structure de la table users
        cursor.execute('DESCRIBE users')
        columns = cursor.fetchall()
        print(f"🔍 Colonnes de la table users:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) {'NOT NULL' if col[2] == 'NO' else 'NULL'}")
        
        # Vérifier si is_email_verified existe
        user_columns = [col[0] for col in columns]
        if 'is_email_verified' in user_columns:
            print("✅ Colonne 'is_email_verified' trouvée - Compatible avec l'application")
        else:
            print("❌ Colonne 'is_email_verified' manquante")
        
        # Compter les enregistrements
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f"👥 Nombre d'utilisateurs: {user_count}")
        
        cursor.execute('SELECT COUNT(*) FROM ocr_history')
        history_count = cursor.fetchone()[0]
        print(f"📄 Nombre d'historiques OCR: {history_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        print("💡 Vérifiez que:")
        print("  - XAMPP/MySQL est démarré")
        print("  - La base 'ocr_intelligence' existe")
        print("  - Les paramètres de connexion sont corrects")
        return False

if __name__ == "__main__":
    test_mysql_connection()