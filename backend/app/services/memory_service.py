import json
import uuid
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update
from app.models.case import Case, ChatMessage
from app.services.retrieval_service import ChromaDBManager

class MemoryService:
    def __init__(self, session_factory: async_sessionmaker, chroma: ChromaDBManager):
        self.session_factory = session_factory
        self.chroma = chroma
        print("MemoryService ready")

    async def save_case(self, case_data: Dict[str, Any]) -> str:
        case_id = str(uuid.uuid4())
        async with self.session_factory() as session:
            new_case = Case(
                id=case_id,
                user_id=case_data.get("user_id"),
                animal_type=case_data.get("animal_type"),
                symptoms_text=case_data.get("symptoms_text"),
                image_path=case_data.get("image_path"),
                primary_diagnosis=case_data.get("primary_diagnosis"),
                alternative_diagnoses=case_data.get("alternative_diagnoses", []),
                confidence_score=case_data.get("confidence_score", 0.0),
                severity=case_data.get("severity", "unknown"),
                vet_urgency=case_data.get("vet_urgency", "monitor"),
                immediate_precautions=case_data.get("immediate_precautions", []),
                llm_model_used=case_data.get("llm_model_used", "unknown"),
                retrieval_time_ms=case_data.get("retrieval_time_ms", 0.0)
            )
            session.add(new_case)
            await session.commit()
        return case_id

    async def save_chat_message(
        self,
        case_id: str,
        role: str,
        content: str
    ) -> None:
        async with self.session_factory() as session:
            new_msg = ChatMessage(
                id=str(uuid.uuid4()),
                case_id=case_id,
                role=role,
                content=content
            )
            session.add(new_msg)
            await session.commit()

    async def get_chat_history(
        self,
        case_id: str,
        last_n: int = 10
    ) -> List[Dict[str, str]]:
        async with self.session_factory() as session:
            stmt = select(ChatMessage).where(ChatMessage.case_id == case_id).order_by(ChatMessage.created_at.desc()).limit(last_n)
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            # Reverse to get chronological order
            return [{"role": m.role, "content": m.content} for m in reversed(messages)]

    async def get_case_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(Case).where(Case.user_id == user_id).order_by(Case.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            cases = result.scalars().all()
            
            return [{
                "case_id": c.id,
                "animal_type": c.animal_type,
                "primary_diagnosis": c.primary_diagnosis,
                "confidence_score": c.confidence_score,
                "feedback_correct": c.feedback_correct,
                "severity": c.severity or "unknown",
                "vet_urgency": c.vet_urgency or "monitor",
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in cases]

    async def save_feedback(
        self,
        case_id: str,
        feedback_correct: bool,
        farmer_note: str = ""
    ) -> None:
        async with self.session_factory() as session:
            stmt = update(Case).where(Case.id == case_id).values(
                feedback_correct=feedback_correct,
                farmer_note=farmer_note,
                feedback_at=datetime.now()
            )
            await session.execute(stmt)
            await session.commit()

    def store_case_vector(
        self,
        case_id: str,
        case_embedding: np.ndarray,
        case_metadata: Dict[str, Any]
    ) -> None:
        """
        Stores resolved case in ChromaDB cases_collection for future similarity-based recall.
        """
        emb_list = case_embedding.tolist() if isinstance(case_embedding, np.ndarray) else list(case_embedding)
        
        self.chroma.cases_collection.add(
            ids=[case_id],
            embeddings=[emb_list],
            metadatas=[case_metadata]
        )
        print(f"Case {case_id} vectorized and stored in memory.")

    async def get_case(self, case_id: str) -> Dict[str, Any]:
        async with self.session_factory() as session:
            stmt = select(Case).where(Case.id == case_id)
            result = await session.execute(stmt)
            case_obj = result.scalar_one_or_none()
            if not case_obj: return {}
            return {
                "id": case_obj.id,
                "user_id": case_obj.user_id,
                "animal_type": case_obj.animal_type,
                "primary_diagnosis": case_obj.primary_diagnosis,
                "feedback_correct": case_obj.feedback_correct
            }

    async def get_session_context(self, case_id: str) -> Dict[str, Any]:
        async with self.session_factory() as session:
            # 1. Get Case
            stmt = select(Case).where(Case.id == case_id)
            result = await session.execute(stmt)
            case_obj = result.scalar_one_or_none()
            
            if not case_obj:
                return {}
            
            # 2. Get Chat History
            chat_history = await self.get_chat_history(case_id, last_n=20)
            
            # 3. Extract answered questions from chat history
            # Simple heuristic: user answers to assistant questions
            answered = []
            for i in range(len(chat_history)-1):
                if chat_history[i]["role"] == "assistant" and chat_history[i+1]["role"] == "user":
                    answered.append((chat_history[i]["content"], chat_history[i+1]["content"]))
            
            case_dict = {
                "id": case_obj.id,
                "user_id": case_obj.user_id,
                "animal_type": case_obj.animal_type,
                "symptoms_text": case_obj.symptoms_text,
                "primary_diagnosis": case_obj.primary_diagnosis,
                "confidence_score": case_obj.confidence_score,
                "severity": case_obj.severity
            }
            
            return {
                "case": case_dict,
                "chat_history": chat_history,
                "answered_questions": answered,
                "current_diagnosis": case_obj.primary_diagnosis,
                "current_confidence": case_obj.confidence_score
            }
