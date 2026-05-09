from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import os
import csv
from datetime import datetime, timedelta
from sqlalchemy import select, func, update

from app.models.schemas import HistoryResponse, CaseHistoryItem, FeedbackRequest, FollowUpUpdate
from app.dependencies import get_memory, get_llm, get_chroma, get_image_service, get_reranker, get_db, get_text_service, get_audit_logger
from app.models.case import Case

router = APIRouter()

@router.get("/health")
async def health_check(
    llm_router=Depends(get_llm),
    chroma=Depends(get_chroma),
    image_service=Depends(get_image_service),
    reranker=Depends(get_reranker),
    db=Depends(get_db)
):
    services = {
        "gemini": len(llm_router.gemini.api_keys) > 0,
        "chromadb": chroma.client.heartbeat() > 0,
        "sqlite": True,
        "clip": image_service.model is not None,
        "bge_reranker": reranker.model is not None
    }
    
    status = "healthy"
    if not all(services.values()):
        status = "degraded"
    if not services["chromadb"]:
        status = "down"
        
    return {
        "status": status,
        "services": services,
        "collections": {
            "disease_images": chroma.disease_collection.count(),
            "knowledge_chunks": chroma.knowledge_collection.count()
        },
        "version": "1.0.0",
        "uptime_seconds": 3600.0
    }

@router.get("/diseases")
async def get_disease_reference():
    return {
        "diseases": [
            {
                "name": "foot_and_mouth",
                "display_name": "Foot and Mouth Disease (Muhpaka-Khurpaka)",
                "animals_affected": ["cow", "buffalo", "sheep", "goat"],
                "body_parts": ["mouth", "hoof", "tongue"],
                "common_symptoms": ["blisters", "drooling", "lameness", "fever"],
                "severity_range": "moderate to severe",
                "india_prevalence": "high"
            },
            {
                "name": "mastitis",
                "display_name": "Mastitis (Thunela)",
                "animals_affected": ["cow", "buffalo"],
                "body_parts": ["udder", "teat"],
                "common_symptoms": ["swollen udder", "clots in milk", "painful udder"],
                "severity_range": "moderate",
                "india_prevalence": "high"
            },
            {
                "name": "lumpy_skin_disease",
                "display_name": "Lumpy Skin Disease",
                "animals_affected": ["cow", "buffalo"],
                "body_parts": ["skin", "lymph nodes"],
                "common_symptoms": ["nodules on skin", "fever", "weight loss"],
                "severity_range": "moderate to severe",
                "india_prevalence": "high"
            },
            {
                "name": "blackquarter",
                "display_name": "Blackquarter (Zeherbad)",
                "animals_affected": ["cow", "buffalo"],
                "body_parts": ["leg", "shoulder"],
                "common_symptoms": ["swelling", "crackling sound", "sudden death"],
                "severity_range": "severe to emergency",
                "india_prevalence": "medium"
            },
            {
                "name": "hemorrhagic_septicemia",
                "display_name": "Hemorrhagic Septicemia (Gal Ghotu)",
                "animals_affected": ["cow", "buffalo"],
                "body_parts": ["throat", "neck"],
                "common_symptoms": ["throat swelling", "difficulty breathing", "high fever"],
                "severity_range": "severe to emergency",
                "india_prevalence": "medium"
            },
            {
                "name": "ppr",
                "display_name": "PPR (Goat Plague)",
                "animals_affected": ["goat", "sheep"],
                "body_parts": ["mouth", "intestine", "lungs"],
                "common_symptoms": ["sores in mouth", "diarrhoea", "pneumonia"],
                "severity_range": "severe",
                "india_prevalence": "high"
            },
            {
                "name": "healthy",
                "display_name": "Healthy Animal",
                "animals_affected": ["cow", "buffalo", "sheep", "goat"],
                "body_parts": ["none"],
                "common_symptoms": ["none"],
                "severity_range": "none",
                "india_prevalence": "n/a"
            }
        ]
    }

@router.get("/user/{user_id}", response_model=HistoryResponse)
async def get_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    memory=Depends(get_memory)
):
    try:
        cases = await memory.get_case_history(user_id, limit=limit)
        return HistoryResponse(
            user_id=user_id,
            cases=[CaseHistoryItem(**c) for c in cases],
            total=len(cases)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/stats")
async def get_stats(
    user_id: str,
    memory=Depends(get_memory),
    db=Depends(get_db)
):
    try:
        stmt_total = select(func.count(Case.id)).where(Case.user_id == user_id, Case.deleted_at == None)
        total_cases = (await db.execute(stmt_total)).scalar() or 0
        
        stmt_animals = select(Case.animal_type, func.count(Case.id)).where(Case.user_id == user_id).group_by(Case.animal_type)
        animals_res = (await db.execute(stmt_animals)).all()
        animals_diagnosed = {row[0]: row[1] for row in animals_res if row[0]}
        
        stmt_diseases = select(Case.primary_diagnosis, func.count(Case.id)).where(Case.user_id == user_id).group_by(Case.primary_diagnosis)
        diseases_res = (await db.execute(stmt_diseases)).all()
        diseases_found = {row[0]: row[1] for row in diseases_res if row[0]}
        
        stmt_conf = select(func.avg(Case.confidence_score)).where(Case.user_id == user_id)
        avg_confidence = (await db.execute(stmt_conf)).scalar() or 0.0
        
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt_month = select(func.count(Case.id)).where(Case.user_id == user_id, Case.created_at >= first_of_month)
        cases_this_month = (await db.execute(stmt_month)).scalar() or 0
        
        stmt_vet = select(func.count(Case.id)).where(Case.user_id == user_id, Case.vet_urgency.in_(["immediate", "High"]))
        vet_referrals = (await db.execute(stmt_vet)).scalar() or 0
        
        most_common = max(diseases_found, key=diseases_found.get) if diseases_found else "None"

        return {
            "total_cases": total_cases,
            "animals_diagnosed": animals_diagnosed,
            "diseases_found": diseases_found,
            "avg_confidence": float(avg_confidence),
            "cases_this_month": cases_this_month,
            "most_common_disease": most_common,
            "vet_referrals": vet_referrals
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{case_id}")
async def delete_case(
    user_id: str,
    case_id: str,
    db=Depends(get_db)
):
    try:
        stmt = update(Case).where(Case.id == case_id, Case.user_id == user_id).values(deleted_at=datetime.now())
        await db.execute(stmt)
        await db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def save_feedback(
    request: FeedbackRequest,
    memory=Depends(get_memory),
    image_service=Depends(get_image_service),
    text_service=Depends(get_text_service)
):
    try:
        await memory.save_feedback(request.case_id, request.feedback_correct, request.farmer_note)
        
        if request.feedback_correct:
            # Rebuild case embedding from stored symptoms + image
            case = await memory.get_case(request.case_id)
            if case:
                # We use text embedding of symptoms as the primary vector for historical case matching
                symptom_emb = text_service.get_text_embedding(case.get("symptoms_text", ""))
                await memory.store_case_vector(
                    request.case_id,
                    symptom_emb,
                    {
                        "animal": case.get("animal_type"),
                        "disease": case.get("primary_diagnosis"),
                        "verified": "true",
                        "source": "farmer_feedback"
                    }
                )
        else:
            log_path = "data/processed/incorrect_predictions.csv"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            file_exists = os.path.isfile(log_path)
            with open(log_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "case_id", "farmer_note"])
                writer.writerow([datetime.now().isoformat(), request.case_id, request.farmer_note])
                
        return {"success": True, "message": "Thank you for feedback"}
    except Exception as e:
        import traceback
        print(f"Error saving feedback: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{str(e)}: {traceback.format_exc()[-200:]}")
@router.post("/follow-up")
async def update_follow_up(
    request: FollowUpUpdate,
    memory=Depends(get_memory)
):
    try:
        result = await memory.update_follow_up(request.case_id, request.status, request.note)
        return result
    except Exception as e:
        print(f"Error updating follow-up: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guardrails/audit")
async def get_guardrail_audit(
    audit_logger=Depends(get_audit_logger)
):
    try:
        summary = audit_logger.get_audit_summary()
        return {
            "success": True,
            "audit": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cases/store-vector")
async def store_case_vector(
    body: Dict[str, str],
    memory=Depends(get_memory),
    text_service=Depends(get_text_service),
    chroma=Depends(get_chroma),
    db=Depends(get_db)
):
    case_id = body.get("case_id")

    if not case_id:
        raise HTTPException(400, "case_id is required")
        
    try:
        # a. Load case from SQLite
        case = await memory.get_case(case_id)
        if not case:
            raise HTTPException(404, "Case not found")
            
        # b. Get symptoms and diagnosis
        symptoms = case.get("symptoms_text", "")
        disease = case.get("primary_diagnosis", "unknown")
        
        # c. Compute embedding
        embedding = text_service.get_text_embedding(symptoms)
        
        # d. Store in ChromaDB
        # Note: Based on our retrieval_service, it's chroma.cases_collection
        chroma.cases_collection.add(
            embeddings=[embedding.tolist()],
            metadatas=[{
                "animal": case.get("animal_type", "unknown"),
                "disease": disease,
                "confidence": str(case.get("confidence_score", 0.0)),
                "verified": "true",
                "source": "farmer_feedback",
                "verified_at": datetime.now().isoformat()
            }],
            ids=[f"verified_{case_id}"]
        )
        
        # e. Update cases table
        stmt = update(Case).where(Case.id == case_id).values(active_learning_stored=True)
        await db.execute(stmt)
        await db.commit()
        
        return {"success": True, "message": "Case added to learning base"}
    except Exception as e:
        print(f"Error storing vector: {e}")
        raise HTTPException(500, str(e))

from fpdf import FPDF
import io
from fastapi.responses import StreamingResponse
import json

@router.post("/generate-report")
async def generate_report(
    body: Dict[str, str],
    memory=Depends(get_memory)
):
    case_id = body.get("case_id")
    if not case_id:
        # Check query params for legacy compatibility
        raise HTTPException(400, "case_id is required")

    case = await memory.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PashuDoctor Clinical Report", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(5)

    fields = [
        ("Animal", str(case.get("animal_type", "unknown")).title()),
        ("Diagnosis", str(case.get("primary_diagnosis", "unknown")).replace("_"," ").title()),
        ("Confidence", f"{float(case.get('confidence_score', 0.0))*100:.0f}%"),
        ("Severity", str(case.get("severity","")).title()),
        ("Vet Urgency", str(case.get("vet_urgency","")).replace("_"," ")),
        ("Date", str(case.get("created_at", ""))[:10]),
        ("Case ID", str(case.get("id", ""))[:8]),
    ]
    for label, value in fields:
        pdf.set_font("Helvetica","B",11)
        pdf.cell(50, 8, f"{label}:", ln=False)
        pdf.set_font("Helvetica","",11)
        pdf.cell(0, 8, value, ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica","B",11)
    pdf.cell(0, 8, "Immediate Precautions:", ln=True)
    pdf.set_font("Helvetica","",10)
    
    precs_raw = case.get("immediate_precautions", "[]")
    if isinstance(precs_raw, str):
        try:
            precs = json.loads(precs_raw)
        except:
            precs = [precs_raw]
    else:
        precs = precs_raw

    for i, p in enumerate(precs[:5], 1):
        pdf.cell(0, 7, f"{i}. {p}", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica","I",9)
    pdf.cell(0,7, "This report is AI-generated. Always consult a licensed veterinarian.", ln=True)
    pdf.cell(0,7, "National Animal Helpline: 1962 (Free, 24/7)", ln=True)

    pdf_bytes = pdf.output()
    buf = io.BytesIO(bytes(pdf_bytes))
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=pashudoctor_{case_id[:8]}.pdf"}
    )
