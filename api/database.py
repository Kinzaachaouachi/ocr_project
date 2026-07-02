
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  
DB_NAME = os.getenv("DB_NAME", "ocr_database")

# Construction de l'URL de connexion
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuration du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    echo=False,          # Mettre True pour voir les requêtes SQL
    pool_size=10,        # Nombre de connexions dans le pool
    max_overflow=20      # Connexions supplémentaires autorisées
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class OCRHistory(Base):
    __tablename__ = "ocr_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500))
    file_type = Column(String(50))
    model_id = Column(String(50))
    model_name = Column(String(100))
    extracted_text = Column(Text)
    char_count = Column(Integer)
    word_count = Column(Integer)
    ocr_time_s = Column(Float)
    status = Column(String(50))
    error_message = Column(Text)
    processed_at = Column(DateTime, default=datetime.utcnow)
    client_ip = Column(String(50))

def init_db():
    """
    Initialise la base de données en créant toutes les tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print(f"✓ Base de données initialisée")
        print(f"  Host: {DB_HOST}:{DB_PORT}")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        return True
    except Exception as e:
        print(f"✗ Erreur d'initialisation de la base de données: {e}")
        return False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
