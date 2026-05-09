import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean, JSON, text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Case(Base):
    __tablename__ = "cases"
    
    # Using String for UUID to ensure SQLite compatibility
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True) # farmer_id
    animal_type = Column(String)
    symptoms_text = Column(String)
    image_path = Column(String)
    
    primary_diagnosis = Column(String)
    alternative_diagnoses = Column(JSON) # List of alternative conditions
    confidence_score = Column(Float)
    severity = Column(String)
    vet_urgency = Column(String)
    immediate_precautions = Column(JSON)
    
    llm_model_used = Column(String)
    retrieval_time_ms = Column(Float)
    
    # Feedback
    feedback_correct = Column(Boolean, nullable=True)
    farmer_note = Column(String, nullable=True)
    feedback_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
