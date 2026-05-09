from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
import anyio
import time
import uuid
import os
import shutil
import json
from typing import Optional, List
from datetime import datetime

from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse, DiagnosisResult, 
    AnimalDetectionResult, ConfidenceResult, DiseaseCandidate
)
from app.dependencies import (
    get_image_service, get_retrieval, get_reranker, get_llm, get_memory, get_text_service,
    get_input_sanitizer, get_llm_validator, get_audit_logger
)
from app.utils.confidence import (
    compute_confidence, route_by_confidence, extract_scores_from_retrieval, 
    FollowUpQuestionGenerator
)
from app.utils.prompts import build_diagnosis_prompt, format_response_for_farmer, SYSTEM_PROMPT
from app.utils.herd_alert import check_herd_alert
from app.utils.breed_intelligence import get_breed_confidence_boost, get_breed_context
from app.utils.connectivity import is_online
from app.limiter import limiter

import logging
logger = logging.getLogger("pashudoctor")

router = APIRouter()
question_generator = FollowUpQuestionGenerator()

# Constants
UPLOAD_DIR = "data/uploads"
MAX_IMAGE_SIZE = 10 * 1024 * 1024 # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Offline Cache (Static for demo, could be persistent)
DIAGNOSIS_CACHE = {} 
CACHE_LIMIT = 50

EMERGENCY_KEYWORDS = [
    # English
    "collapsed", "not breathing", "seizure", "convulsion", "bleeding heavily", "sudden death", "unconscious", "dying",
    # Hindi
    "गिर गई", "बेहोश", "सांस नहीं", "खून बह रहा", "मर रहा", "दौरे",
    # Tamil
    "மயக்கம்", "மூச்சு இல்லை", "இரத்தம்", "வலிப்பு",
    # Telugu
    "పడిపోయింది", "శ్వాస లేదు", "రక్తం", "మూర్ఛ",
    # Kannada
    "ಬಿದ್ದಿದೆ", "ಉಸಿರಾಟವಿಲ್ಲ", "ರಕ್ತ", "ಸೆಳೆತ",
    # Marathi
    "कोलमडली", "श्वास नाही", "रक्तस्त्राव", "झटके",
    # Bengali
    "মাথা ঘুরে পড়ে", "নিশ্বাস বন্ধ", "রক্তপাত", "খিঁচুনি",
    # Punjabi
    "ਡਿੱਗ ਪਿਆ", "ਸਾਹ ਨਹੀਂ", "ਖੂਨ", "ਦੌਰੇ",
    # Gujarati
    "ઢળી પડી", "શ્વાસ નથી", "લોહી", "ખેંચ",
    # Malayalam
    "വീണു", "ശ്വാസമില്ല", "രക്തം", "അപസ്മാരം"
]

def check_emergency(text: str) -> bool:
    if not text: return False
    text = text.lower()
    return any(kw in text for kw in EMERGENCY_KEYWORDS)

def get_immediate_emergency_response(user_id: str, animal: str = "animal"):
    return AnalyzeResponse(
        case_id=str(uuid.uuid4()),
        animal_detection=AnimalDetectionResult(animal=animal, confidence=1.0, method="fast_path"),
        confidence=ConfidenceResult(
            score=1.0, percentage=100, action="suggest", 
            message="EMERGENCY DETECTED: Contact a veterinarian NOW.", 
            show_prediction=True
        ),
        diagnosis=DiagnosisResult(
            primary_diagnosis="CRITICAL EMERGENCY",
            alternative_diagnoses=[],
            matching_symptoms=["Emergency keywords detected"],
            differential_reasoning="Fast-path emergency trigger activated.",
            image_confidence=1.0,
            symptom_confidence=1.0,
            knowledge_confidence=1.0,
            immediate_precautions=["Do NOT attempt home treatment", "Call 1962 immediately", "Keep animal in shade"],
            urgent_warning_signs=["Life threatening condition"],
            herd_prevention=[],
            farmer_advice="EMERGENCY: Contact a veterinarian NOW. National Animal Helpline: 1962.",
            vet_urgency="immediate",
            severity="emergency",
            formatted_response="### 🚨 EMERGENCY: Contact a veterinarian NOW.\n\n**National Animal Helpline: 1962**\n\nDo NOT attempt home treatment. This is a life-threatening situation."
        ),
        follow_up_questions=[],
        top_candidates=[],
        retrieval_time_ms=0,
        llm_time_ms=0,
        model_used="fast_path",
        success=True
    )

def get_error_response(message: str):
    return AnalyzeResponse(
        case_id="error",
        animal_detection=AnimalDetectionResult(animal="unknown", confidence=0.0, method="error"),
        confidence=ConfidenceResult(
            score=0.0, percentage=0, action="error", 
            message=message, show_prediction=False
        ),
        diagnosis=None,
        follow_up_questions=[],
        top_candidates=[],
        retrieval_time_ms=0.0,
        llm_time_ms=0.0,
        model_used="error",
        success=False,
        error=message
    )

@router.post("/image", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    user_id: str = Form(...),
    images: List[UploadFile] = File(...),
    symptom_text: str = Form(...),
    animal_type: Optional[str] = Form(None),
    language: str = Form("english"),
    image_service=Depends(get_image_service),
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory),
    input_sanitizer=Depends(get_input_sanitizer),
    llm_validator=Depends(get_llm_validator),
    audit_logger=Depends(get_audit_logger)
):
    start_time = time.time()
    temp_paths = []
    
    try:
        # 0. Emergency Fast Path
        if check_emergency(symptom_text):
            return get_immediate_emergency_response(user_id, animal_type or "animal")

        # 0.5 Sanitize Text
        sanitized = input_sanitizer.sanitize_text(symptom_text)
        if not sanitized["is_safe"]:
            if sanitized["injection_detected"]:
                audit_logger.log_event("injection_attempt", None, sanitized, blocked=True)
                raise HTTPException(status_code=400, detail="Invalid characters in symptom description")
            if sanitized["human_query_detected"]:
                audit_logger.log_event("human_query_attempt", None, sanitized, blocked=True)
                return {
                    "success": False,
                    "error": "human_medical_query",
                    "message": "PashuDoctor can only help with livestock animal health. For human medical help please contact a doctor."
                }
        symptom_text = sanitized["sanitized_text"]

        # 1. Validation and Saving
        if len(images) > 3:
            images = images[:3]
            
        for image in images:
            if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
                raise HTTPException(status_code=415, detail=f"Unsupported format for {image.filename}")
            
            contents = await image.read()
            # 1.1 Image Validation
            validation = input_sanitizer.validate_image_file(
                file_size_bytes=len(contents),
                content_type=image.content_type,
                filename=image.filename
            )
            if not validation["is_valid"]:
                audit_logger.log_event("invalid_file", None, validation, blocked=True)
                raise HTTPException(status_code=400, detail=validation["errors"])
            
            filename = f"{uuid.uuid4()}_{image.filename}"
            path = os.path.join(UPLOAD_DIR, filename)
            with open(path, "wb") as f:
                f.write(contents)
            temp_paths.append(path)

            # Quality Check
            quality = image_service.check_image_quality(path)
            if not quality["valid"]:
                raise HTTPException(status_code=400, detail=f"Invalid image {image.filename}: {quality['reason']}")

            # 1.2 Animal Relevance Check
            animal_check = input_sanitizer.check_animal_relevance(path, image_service)
            if not animal_check["is_animal"]:
                audit_logger.log_event("non_animal_image", None, animal_check, blocked=True)
                raise HTTPException(status_code=400, detail={
                    "error": "non_animal_image",
                    "message": animal_check["reason"],
                    "suggestion": "Please upload a clear photo of your livestock animal"
                })

        if not temp_paths:
            raise HTTPException(status_code=400, detail="No valid images uploaded.")

        # 2. Animal Detection (using the first image as representative)
        detection = await anyio.to_thread.run_sync(image_service.detect_animal, temp_paths[0])
        detected_animal = animal_type if animal_type else detection["animal"]
        
        # 3. Retrieval with Combined Embedding
        retrieval_start = time.time()
        # We need a new retrieval method or hack it by passing the combined embedding
        # For now, let's assume retrieval.retrieve_all can handle a list of paths
        results = await retrieval.retrieve_all(temp_paths, symptom_text, detected_animal)
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
        
        # LOGGING FOR DEBUGGING
        logger.info(f"Retrieval Scores: {scores}")
        logger.info(f"Final Confidence: {confidence['score']} (Action: {route_by_confidence(confidence)['action']})")
        
        routing = route_by_confidence(confidence)
        
        # 8. Follow-up or Diagnosis
        # 8. Follow-up and Diagnosis
        follow_up = question_generator.get_questions(
            action=routing["action"],
            disease_hint=top_candidate["metadata"].get("disease"),
            answered=[]
        )

        diagnosis = None
        model_used = "none"
        llm_time = 0
        
        # We attempt a diagnosis if we have minimal evidence (10%) or an image
        if confidence["score"] > 0.10 or temp_paths:
            llm_start = time.time()
            breed_context = "" # No breed for image detection yet, unless passed in query
            prompt = build_diagnosis_prompt(
                detected_animal, 
                symptom_text, 
                reranked_results["disease_candidates"][:3], 
                reranked_results["knowledge_chunks"][:3], 
                confidence,
                extra_context=breed_context
            )
            
            if is_online():
                diag_data = await anyio.to_thread.run_sync(
                    llm_validator.validate_with_retry,
                    prompt,
                    llm_router,
                    SYSTEM_PROMPT,
                    temp_paths,
                    3
                )
                model_used = "gemini-1.5-flash"
                
                # Cache the validated data
                cache_key = f"{detected_animal}_{symptom_text[:50]}"
                DIAGNOSIS_CACHE[cache_key] = {"success": True, "text": json.dumps(diag_data), "routed_to": model_used}
            else:
                # Offline Cache Lookup
                cache_key = f"{detected_animal}_{symptom_text[:50]}"
                if cache_key in DIAGNOSIS_CACHE:
                    llm_res = DIAGNOSIS_CACHE[cache_key]
                    diag_data = json.loads(llm_res["text"])
                    model_used = llm_res.get("routed_to", "unknown")
                else:
                    # In low confidence ask_more path, we can afford to skip if offline
                    diag_data = None
                    if confidence["score"] > 0.35:
                        return get_error_response("Offline mode: No cached diagnosis for these symptoms. Please connect to internet.")

            llm_time = (time.time() - llm_start) * 1000
            
            if diag_data:
                try:
                    formatted = format_response_for_farmer(diag_data, language)
                    
                    # Similar cases info
                    sim_count = len(reranked_results.get("disease_candidates", []))
                    primary_name = diag_data.get("primary_diagnosis", "Unknown")
                    sim_type = f"{primary_name} cases in {detected_animal}s"
                    
                    diagnosis = DiagnosisResult(
                        primary_diagnosis=primary_name,
                        alternative_diagnoses=diag_data.get("alternative_diagnoses", []),
                        matching_symptoms=diag_data.get("matching_symptoms", []),
                        differential_reasoning=diag_data.get("differential_reasoning", ""),
                        image_confidence=diag_data.get("image_confidence", confidence.get("image_sim", 0.0)),
                        symptom_confidence=diag_data.get("symptom_confidence", confidence.get("symptom_match", 0.0)),
                        knowledge_confidence=diag_data.get("knowledge_confidence", confidence.get("text_sim", 0.0)),
                        similar_cases_count=sim_count,
                        similar_cases_type=sim_type,
                        immediate_precautions=diag_data.get("immediate_precautions", []),
                        urgent_warning_signs=diag_data.get("urgent_warning_signs", []),
                        herd_prevention=diag_data.get("herd_prevention", []),
                        farmer_advice=diag_data.get("farmer_advice", ""),
                        vet_urgency=diag_data.get("vet_urgency", "monitor"),
                        severity={
                            "immediate": "emergency",
                            "within_24h": "severe",
                            "within_week": "moderate",
                            "monitor": "mild"
                        }.get(diag_data.get("vet_urgency", "monitor"), "moderate"),
                        herd_alert=check_herd_alert(primary_name, language),
                        breed=animal_type or "Unknown",
                        timeline=[{
                            "day": 1,
                            "event": "Initial Diagnosis",
                            "note": f"{primary_name} suspected ({int(confidence.get('score', 0)*100)}%)",
                            "timestamp": datetime.now().isoformat()
                        }],
                        formatted_response=formatted
                    )
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}", exc_info=True)
                    # Fallback to simple diagnosis
                    diagnosis = None
        
        # 9. Save Case
        case_data = {
            "user_id": user_id,
            "animal_type": detected_animal,
            "symptoms_text": symptom_text,
            "image_path": temp_paths[0], # Primary image for history
            "all_images": temp_paths,
            "primary_diagnosis": diagnosis.primary_diagnosis if diagnosis else "Pending",
            "alternative_diagnoses": diagnosis.alternative_diagnoses if diagnosis else [],
            "matching_symptoms": diagnosis.matching_symptoms if diagnosis else [],
            "differential_reasoning": diagnosis.differential_reasoning if diagnosis else "",
            "image_confidence": diagnosis.image_confidence if diagnosis else 0.0,
            "symptom_confidence": diagnosis.symptom_confidence if diagnosis else 0.0,
            "knowledge_confidence": diagnosis.knowledge_confidence if diagnosis else 0.0,
            "similar_cases_count": diagnosis.similar_cases_count if diagnosis else 0,
            "similar_cases_type": diagnosis.similar_cases_type if diagnosis else "",
            "confidence_score": confidence["score"],
            "severity": diagnosis.severity if diagnosis else "unknown",
            "vet_urgency": diagnosis.vet_urgency if diagnosis else "monitor",
            "immediate_precautions": diagnosis.immediate_precautions if diagnosis else [],
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
@limiter.limit("10/minute")
async def analyze_text(
    request: Request,
    request_body: AnalyzeRequest,
    text_service=Depends(get_text_service),
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory),
    input_sanitizer=Depends(get_input_sanitizer),
    llm_validator=Depends(get_llm_validator),
    audit_logger=Depends(get_audit_logger)
):
    start_time = time.time()
    
    try:
        # 0. Emergency Fast Path
        if check_emergency(request_body.symptom_text):
            return get_immediate_emergency_response(request_body.user_id, request_body.animal_type or "animal")

        # 0.5 Sanitize Text
        sanitized = input_sanitizer.sanitize_text(request_body.symptom_text)
        if not sanitized["is_safe"]:
            if sanitized["injection_detected"]:
                audit_logger.log_event("injection_attempt", None, sanitized, blocked=True)
                raise HTTPException(status_code=400, detail="Invalid characters in symptom description")
            if sanitized["human_query_detected"]:
                audit_logger.log_event("human_query_attempt", None, sanitized, blocked=True)
                return {
                    "success": False,
                    "error": "human_medical_query",
                    "message": "PashuDoctor can only help with livestock animal health. For human medical help please contact a doctor."
                }
        request_body.symptom_text = sanitized["sanitized_text"]

        # 1. Text-only Retrieval
        retrieval_start = time.time()
        # Use retrieve_all but pass None for image
        results = await retrieval.retrieve_all(None, request_body.symptom_text, request_body.animal_type)
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
            breed_context = get_breed_context(request_body.breed)
            prompt = build_diagnosis_prompt(
                request_body.animal_type or "unknown", 
                request_body.symptom_text, 
                reranked_results["disease_candidates"][:3], 
                reranked_results["knowledge_chunks"][:3], 
                confidence,
                extra_context=breed_context
            )
            
            if is_online():
                diag_data = await anyio.to_thread.run_sync(
                    llm_validator.validate_with_retry,
                    prompt,
                    llm_router,
                    SYSTEM_PROMPT,
                    None,
                    3
                )
                model_used = "gemini-1.5-flash"
                
                # Caching
                cache_key = f"{request_body.animal_type}_{request_body.symptom_text[:50]}"
                DIAGNOSIS_CACHE[cache_key] = {"success": True, "text": json.dumps(diag_data), "routed_to": model_used}
            else:
                # Offline Cache Lookup
                cache_key = f"{request_body.animal_type}_{request_body.symptom_text[:50]}"
                if cache_key in DIAGNOSIS_CACHE:
                    llm_res = DIAGNOSIS_CACHE[cache_key]
                    diag_data = json.loads(llm_res["text"])
                    model_used = llm_res.get("routed_to", "unknown")
                else:
                    return get_error_response("Offline mode: No cached diagnosis for these symptoms. Please connect to internet.")
            llm_time = (time.time() - llm_start) * 1000
            
            if diag_data:
                try:
                    formatted = format_response_for_farmer(diag_data, request_body.language)
                    
                    # Similar cases info
                    sim_count = len(reranked_results.get("disease_candidates", []))
                    primary_name = diag_data.get("primary_diagnosis", "Unknown")
                    sim_type = f"{primary_name} cases in {request_body.animal_type or 'animal'}s"

                    diagnosis = DiagnosisResult(
                        primary_diagnosis=primary_name,
                        alternative_diagnoses=diag_data.get("alternative_diagnoses", []),
                        matching_symptoms=diag_data.get("matching_symptoms", []),
                        differential_reasoning=diag_data.get("differential_reasoning", ""),
                        image_confidence=diag_data.get("image_confidence", 0.0),
                        symptom_confidence=diag_data.get("symptom_confidence", confidence.get("symptom_match", 0.0)),
                        knowledge_confidence=diag_data.get("knowledge_confidence", confidence.get("text_sim", 0.0)),
                        similar_cases_count=sim_count,
                        similar_cases_type=sim_type,
                        immediate_precautions=diag_data.get("immediate_precautions", []),
                        urgent_warning_signs=diag_data.get("urgent_warning_signs", []),
                        herd_prevention=diag_data.get("herd_prevention", []),
                        farmer_advice=diag_data.get("farmer_advice", ""),
                        vet_urgency=diag_data.get("vet_urgency", "monitor"),
                        severity={
                            "immediate": "emergency",
                            "within_24h": "severe",
                            "within_week": "moderate",
                            "monitor": "mild"
                        }.get(diag_data.get("vet_urgency", "monitor"), "moderate"),
                        herd_alert=check_herd_alert(primary_name, language if 'language' in locals() else request_body.language),
                        breed=request_body.breed if 'request_body' in locals() else "Unknown",
                        timeline=[{
                            "day": 1,
                            "event": "Initial Diagnosis",
                            "note": f"{primary_name} suspected ({int(confidence.get('score', 0)*100)}%)",
                            "timestamp": datetime.now().isoformat()
                        }],
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
            "alternative_diagnoses": diagnosis.alternative_diagnoses if diagnosis else [],
            "matching_symptoms": diagnosis.matching_symptoms if diagnosis else [],
            "differential_reasoning": diagnosis.differential_reasoning if diagnosis else "",
            "image_confidence": diagnosis.image_confidence if diagnosis else 0.0,
            "symptom_confidence": diagnosis.symptom_confidence if diagnosis else 0.0,
            "knowledge_confidence": diagnosis.knowledge_confidence if diagnosis else 0.0,
            "similar_cases_count": diagnosis.similar_cases_count if diagnosis else 0,
            "similar_cases_type": diagnosis.similar_cases_type if diagnosis else "",
            "confidence_score": confidence["score"],
            "severity": diagnosis.severity if diagnosis else "unknown",
            "vet_urgency": diagnosis.vet_urgency if diagnosis else "monitor",
            "immediate_precautions": diagnosis.immediate_precautions if diagnosis else [],
            "llm_model_used": model_used,
            "retrieval_time_ms": retrieval_time
        }
        
        # Apply Breed Confidence Boost
        if request_body.breed and diagnosis:
            boost = get_breed_confidence_boost(request_body.breed, diagnosis.primary_diagnosis)
            confidence["score"] = min(1.0, confidence["score"] + boost)
            confidence["percentage"] = int(confidence["score"] * 100)
            case_data["confidence_score"] = confidence["score"]

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
        logger.error(f"Error in analyze_image: {e}", exc_info=True)
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

import io
from gtts import gTTS
from fastapi.responses import StreamingResponse

@router.post("/tts")
async def text_to_speech(body: dict):
    text = body.get("text","")[:300]
    lang = body.get("lang","en")
    
    # Simple lang code mapping if needed (e.g. English -> en)
    # Most of our internal lang names are capitalized, gTTS needs 2-char codes
    lang_map = {
        "english": "en", "hindi": "hi", "tamil": "ta", "telugu": "te",
        "kannada": "kn", "malayalam": "ml", "marathi": "mr", "bengali": "bn",
        "punjabi": "pa", "gujarati": "gu"
    }
    gtts_lang = lang_map.get(lang.lower(), "en")
    
    buf = io.BytesIO()
    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=tts.mp3"}
        )
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")
