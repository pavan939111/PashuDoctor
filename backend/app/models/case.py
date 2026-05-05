from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    animal_type = Column(String)
    symptoms_text = Column(String)
    image_path = Column(String)
    prediction = Column(String)
    confidence_score = Column(Float)
    severity = Column(String)
    vet_referred = Column(Boolean, default=False)
    feedback_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
