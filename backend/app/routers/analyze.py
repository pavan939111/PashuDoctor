from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
import anyio
import time
import uuid
import os
import shutil
import json
from typing import Optional

from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse, DiagnosisResult, 
    AnimalDetectionResult, ConfidenceResult, DiseaseCandidate
)
from app.dependencies import (
    get_image_service, get_retrieval, get_reranker, get_llm, get_memory, get_text_service
)
from app.utils.confidence import (
    compute_confidence, route_by_confidence, extract_scores_from_retrieval, 
    FollowUpQuestionGenerator
)
from app.utils.prompts import build_diagnosis_prompt, format_response_for_farmer, SYSTEM_PROMPT
from app.limiter import limiter

router = APIRouter()
question_generator = FollowUpQuestionGenerator()

# Constants
UPLOAD_DIR = "data/uploads"
MAX_IMAGE_SIZE = 10 * 1024 * 1024 # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_error_response(message: str, status_code: int = 500):
    return {
        "success": False,
        "error": message,
        "case_id": None
    }

@router.post("/image", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    user_id: str = Form(...),
    symptom_text: str = Form(...),
    animal_type: Optional[str] = Form(None),
    language: str = Form("english"),
    image_service=Depends(get_image_service),
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory)
):
    start_time = time.time()
    temp_path = None
    
    try:
        # 1. Image Validation (Size and Format)
        if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=415, detail="Unsupported image format. Use JPEG, PNG, or WebP.")
            
        # Check size by reading a small chunk or the whole thing
        contents = await image.read()
        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Image too large. Max size is 10MB.")
        
        # 2. Save Image
        filename = f"{uuid.uuid4()}_{image.filename}"
        temp_path = os.path.join(UPLOAD_DIR, filename)
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # 3. Quality Check
        quality = image_service.check_image_quality(temp_path)
        if not quality["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid image: {quality['reason']}")

        # 4. Animal Detection (to refine retrieval if animal_type not provided)
        detection = await anyio.to_thread.run_sync(image_service.detect_animal, temp_path)
        detected_animal = animal_type if animal_type else detection["animal"]
        
        # 5. Retrieval
        retrieval_start = time.time()
        results = await anyio.to_thread.run_sync(retrieval.retrieve_all, temp_path, symptom_text, detected_animal)
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        # 6. Reranking
        reranked_results = await anyio.to_thread.run_sync(reranker.rerank_all, symptom_text, results)
        
        # 7. Confidence & Routing
        if not reranked_results.get("disease_candidates"):
            return AnalyzeResponse(
                case_id=str(uuid.uuid4()),
                animal_detection=AnimalDetectionResult(
                    animal=detected_animal,
                    confidence=detection["confidence"],
                    method=detection["method"]
                ),
                confidence=ConfidenceResult(
                    score=0.0,
                    percentage=0,
                    action="ask_more",
                    message="Not enough information to identify a disease.",
                    show_prediction=False
                ),
                diagnosis=None,
                follow_up_questions=["Could you describe the symptoms in more detail?", "When did you first notice this?"],
                top_candidates=[],
                retrieval_time_ms=retrieval_time,
                llm_time_ms=0,
                model_used="none",
                success=True
            )

        top_candidate = reranked_results["disease_candidates"][0]
        scores = extract_scores_from_retrieval(
            top_candidate, 
            reranked_results, 
            provided_symptoms=[s.strip() for s in symptom_text.replace(",", " ").split()]
        )
        confidence = compute_confidence(**scores)
        routing = route_by_confidence(confidence)
        
        # 8. Follow-up or Diagnosis
        diagnosis = None
        follow_up = []
        model_used = "none"
        llm_time = 0
        
        if routing["action"] == "ask_more":
            follow_up = question_generator.get_questions(
                action="ask_more",
                disease_hint=top_candidate["metadata"].get("disease"),
                answered=[]
            )
        elif routing["show_prediction"]:
            llm_start = time.time()
            prompt = build_diagnosis_prompt(
                detected_animal, 
                symptom_text, 
                reranked_results["disease_candidates"][:3], 
                reranked_results["knowledge_chunks"][:3], 
                confidence
            )
            
            llm_res = await anyio.to_thread.run_sync(
                llm_router.generate,
                prompt,
                SYSTEM_PROMPT,
                {
                    "confidence_score": confidence["score"],
                    "needs_image_analysis": False
                }
            )

            llm_time = (time.time() - llm_start) * 1000
            model_used = llm_res.get("routed_to", "unknown")
            
            if llm_res["success"]:
                try:
                    # Parse JSON from LLM
                    text = llm_res["text"].strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    
                    diag_data = json.loads(text)
                    formatted = format_response_for_farmer(diag_data, language)
                    
                    diagnosis = DiagnosisResult(
                        primary_diagnosis=diag_data.get("primary_diagnosis", "Unknown"),
                        alternative_diagnoses=diag_data.get("alternative_diagnoses", []),
                        matching_symptoms=diag_data.get("matching_symptoms", []),
                        immediate_precautions=diag_data.get("immediate_precautions", []),
                        urgent_warning_signs=diag_data.get("urgent_warning_signs", []),
                        herd_prevention=diag_data.get("herd_prevention", []),
                        farmer_advice=diag_data.get("farmer_advice", ""),
                        vet_urgency=diag_data.get("vet_urgency", "monitor"),
                        severity="moderate", # Default or derived from diagnosis if available
                        formatted_response=formatted
                    )
                except Exception as e:
                    print(f"Error parsing LLM response: {e}")
                    # Fallback to simple diagnosis
                    diagnosis = None
        
        # 9. Save Case
        case_data = {
            "user_id": user_id,
            "animal_type": detected_animal,
            "symptoms_text": symptom_text,
            "image_path": temp_path,
            "primary_diagnosis": diagnosis.primary_diagnosis if diagnosis else "Pending",
            "confidence_score": confidence["score"],
            "llm_model_used": model_used,
            "retrieval_time_ms": retrieval_time
        }
        case_id = await memory.save_case(case_data)
        
        return AnalyzeResponse(
            case_id=case_id,
            animal_detection=AnimalDetectionResult(
                animal=detection["animal"],
                confidence=detection["confidence"],
                method=detection["method"]
            ),
            confidence=ConfidenceResult(
                score=confidence["score"],
                percentage=confidence["percentage"],
                action=routing["action"],
                message=routing["message"],
                show_prediction=routing["show_prediction"]
            ),
            diagnosis=diagnosis,
            follow_up_questions=follow_up,
            top_candidates=[
                DiseaseCandidate(
                    disease=c["metadata"].get("disease", "unknown"),
                    animal=c["metadata"].get("animal", "unknown"),
                    body_part=c["metadata"].get("body_part", "unknown"),
                    severity=c["metadata"].get("severity", "unknown"),
                    final_score=c.get("final_score", 0.0),
                    reranker_score=c.get("reranker_score", 0.0)
                ) for c in reranked_results["disease_candidates"][:5]
            ],
            retrieval_time_ms=retrieval_time,
            llm_time_ms=llm_time,
            model_used=model_used,
            success=True
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in analyze_image: {e}")
        return get_error_response(str(e))

@router.post("/text-only", response_model=AnalyzeResponse)
async def analyze_text(
    request: Request,
    request_body: AnalyzeRequest,
    text_service=Depends(get_text_service),
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory)
):
    start_time = time.time()
    
    try:
        # 1. Text-only Retrieval
        retrieval_start = time.time()
        # Use retrieve_all but pass None for image
        results = await anyio.to_thread.run_sync(retrieval.retrieve_all, None, request_body.symptom_text, request_body.animal_type)
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        # 2. Reranking
        reranked_results = await anyio.to_thread.run_sync(reranker.rerank_all, request_body.symptom_text, results)
        
        # 3. Confidence & Routing
        if not reranked_results.get("disease_candidates"):
            return AnalyzeResponse(
                case_id=str(uuid.uuid4()),
                animal_detection=AnimalDetectionResult(
                    animal=request_body.animal_type or "unknown",
                    confidence=0.0,
                    method="none"
                ),
                confidence=ConfidenceResult(
                    score=0.0,
                    percentage=0,
                    action="ask_more",
                    message="Not enough information to identify a disease.",
                    show_prediction=False
                ),
                diagnosis=None,
                follow_up_questions=["Could you describe the symptoms in more detail?", "When did you first notice this?"],
                top_candidates=[],
                retrieval_time_ms=retrieval_time,
                llm_time_ms=0,
                model_used="none",
                success=True
            )

        top_candidate = reranked_results["disease_candidates"][0]
        scores = extract_scores_from_retrieval(
            top_candidate, 
            reranked_results, 
            provided_symptoms=[s.strip() for s in request_body.symptom_text.replace(",", " ").split()]
        )
        # Weight image sim as 0 since it's text only
        scores["image_similarity"] = 0.0
        confidence = compute_confidence(**scores)
        routing = route_by_confidence(confidence)
        
        # 4. Follow-up or Diagnosis (Same as image logic)
        diagnosis = None
        follow_up = []
        model_used = "none"
        llm_time = 0
        
        if routing["action"] == "ask_more":
            follow_up = question_generator.get_questions(
                action="ask_more",
                disease_hint=top_candidate["metadata"].get("disease"),
                answered=[]
            )
        elif routing["show_prediction"]:
            llm_start = time.time()
            prompt = build_diagnosis_prompt(
                request_body.animal_type or "unknown", 
                request_body.symptom_text, 
                reranked_results["disease_candidates"][:3], 
                reranked_results["knowledge_chunks"][:3], 
                confidence
            )
            
            llm_res = await anyio.to_thread.run_sync(
                llm_router.generate,
                prompt,
                SYSTEM_PROMPT,
                {
                    "confidence_score": confidence["score"],
                    "needs_image_analysis": False
                }
            )
            llm_time = (time.time() - llm_start) * 1000
            model_used = llm_res.get("routed_to", "unknown")
            
            if llm_res["success"]:
                try:
                    text = llm_res["text"].strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    
                    diag_data = json.loads(text)
                    formatted = format_response_for_farmer(diag_data, request_body.language)
                    
                    diagnosis = DiagnosisResult(
                        primary_diagnosis=diag_data.get("primary_diagnosis", "Unknown"),
                        alternative_diagnoses=diag_data.get("alternative_diagnoses", []),
                        matching_symptoms=diag_data.get("matching_symptoms", []),
                        immediate_precautions=diag_data.get("immediate_precautions", []),
                        urgent_warning_signs=diag_data.get("urgent_warning_signs", []),
                        herd_prevention=diag_data.get("herd_prevention", []),
                        farmer_advice=diag_data.get("farmer_advice", ""),
                        vet_urgency=diag_data.get("vet_urgency", "monitor"),
                        severity="moderate",
                        formatted_response=formatted
                    )
                except:
                    diagnosis = None

        # 5. Save Case
        case_data = {
            "user_id": request_body.user_id,
            "animal_type": request_body.animal_type,
            "symptoms_text": request_body.symptom_text,
            "image_path": None,
            "primary_diagnosis": diagnosis.primary_diagnosis if diagnosis else "Pending",
            "confidence_score": confidence["score"],
            "llm_model_used": model_used,
            "retrieval_time_ms": retrieval_time
        }
        case_id = await memory.save_case(case_data)

        return AnalyzeResponse(
            case_id=case_id,
            animal_detection=AnimalDetectionResult(
                animal=request_body.animal_type or "unknown",
                confidence=0.0,
                method="none"
            ),
            confidence=ConfidenceResult(
                score=confidence["score"],
                percentage=confidence["percentage"],
                action=routing["action"],
                message=routing["message"],
                show_prediction=routing["show_prediction"]
            ),
            diagnosis=diagnosis,
            follow_up_questions=follow_up,
            top_candidates=[
                DiseaseCandidate(
                    disease=c["metadata"].get("disease", "unknown"),
                    animal=c["metadata"].get("animal", "unknown"),
                    body_part=c["metadata"].get("body_part", "unknown"),
                    severity=c["metadata"].get("severity", "unknown"),
                    final_score=c.get("final_score", 0.0),
                    reranker_score=c.get("reranker_score", 0.0)
                ) for c in reranked_results["disease_candidates"][:5]
            ],
            retrieval_time_ms=retrieval_time,
            llm_time_ms=llm_time,
            model_used=model_used,
            success=True
        )

    except Exception as e:
        print(f"Error in analyze_text: {e}")
        return get_error_response(str(e))

@router.get("/{case_id}")
async def get_case_details(
    case_id: str,
    memory=Depends(get_memory)
):
    try:
        context = await memory.get_session_context(case_id)
        if not context:
            raise HTTPException(status_code=404, detail="Case not found")
        return {
            "success": True,
            "case": context["case"],
            "chat_history": context["chat_history"],
            "diagnosis": context.get("current_diagnosis"),
            "confidence": context.get("current_confidence")
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching case: {e}")
        return get_error_response(str(e))
