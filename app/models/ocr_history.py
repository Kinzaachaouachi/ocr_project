from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class OCRHistory(Base):
    __tablename__ = "ocr_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_path = Column(String(1000), nullable=True)

    model_id = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=False, index=True)
    extracted_text = Column(Text, nullable=True)
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

    ocr_time_s = Column("execution_time", Float, default=0.0)
    init_time_s = Column(Float, default=0.0)

    confidence = Column("confidence_score", Float, default=0.0)
    precision_score = Column(Float, nullable=True)
    robustness = Column(Float, nullable=True)
    global_score = Column(Float, nullable=True)

    language = Column("detected_language", String(10), default="auto")
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)

    client_ip = Column(String(50), nullable=True)
    processed_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("User", back_populates="ocr_history")

    @property
    def confidence_percentage(self) -> int:
        conf = self.confidence or 0

        return int(conf if conf > 1 else conf * 100)

    @property
    def text_preview(self) -> str:
        if not self.extracted_text:
            return ""
        text = self.extracted_text.strip()
        return text[:150] + "…" if len(text) > 150 else text

    @property
    def processing_time_formatted(self) -> str:
        return f"{self.ocr_time_s:.2f}s" if self.ocr_time_s else "0.00s"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_path": self.file_path,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "extracted_text": self.extracted_text,
            "text_preview": self.text_preview,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "ocr_time_s": self.ocr_time_s,
            "confidence": self.confidence,
            "confidence_percentage": self.confidence_percentage,
            "precision_score": self.precision_score,
            "robustness": self.robustness,
            "global_score": self.global_score,
            "language": self.language,
            "status": self.status,
            "error_message": self.error_message,
            "client_ip": self.client_ip,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "user_name": self.user.display_name if self.user else "Anonyme",
        }
