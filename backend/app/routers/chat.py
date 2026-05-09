from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from typing import List, Dict, Any
import json
import time

from app.models.schemas import (
    ChatRequest, ChatResponse, AnalyzeResponse, 
    FollowUpRequest, ConfidenceResult, DiagnosisResult,
    AnimalDetectionResult, DiseaseCandidate
)
from app.dependencies import (
    get_retrieval, get_reranker, get_llm, get_memory, get_text_service,
    get_input_sanitizer, get_audit_logger
)
from app.utils.confidence import (
    compute_confidence, route_by_confidence, extract_scores_from_retrieval, 
    FollowUpQuestionGenerator
)
from app.utils.prompts import (
    build_diagnosis_prompt, format_response_for_farmer, 
    build_followup_prompt, SYSTEM_PROMPT
)
from app.limiter import limiter

router = APIRouter()
question_generator = FollowUpQuestionGenerator()

@router.post("/message", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_message(
    request: Request,
    chat_request: ChatRequest,
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory),
    input_sanitizer=Depends(get_input_sanitizer),
    audit_logger=Depends(get_audit_logger)
):
    try:
        # 1. Load Session Context
        context = await memory.get_session_context(chat_request.case_id)
        if not context:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # 1.5 Sanitize Message
        sanitized = input_sanitizer.sanitize_text(chat_request.message)
        if not sanitized["is_safe"]:
            if sanitized["injection_detected"]:
                audit_logger.log_event("injection_attempt", chat_request.case_id, sanitized, blocked=True)
                return ChatResponse(case_id=chat_request.case_id, response="Invalid characters detected in message.", success=False, diagnosis_updated=False, follow_up_questions=[])
            if sanitized["human_query_detected"]:
                audit_logger.log_event("human_query_attempt", chat_request.case_id, sanitized, blocked=True)
                return ChatResponse(case_id=chat_request.case_id, response="PashuDoctor can only help with livestock health. Please contact a doctor for human health issues.", success=False, diagnosis_updated=False, follow_up_questions=[])
        chat_request.message = sanitized["sanitized_text"]

        # 2. Save User Message
        await memory.save_chat_message(chat_request.case_id, "user", chat_request.message)
        
        # 3. Load History
        history = await memory.get_chat_history(chat_request.case_id, last_n=10)
        
        # 4. Check for New Symptom Info & Re-run Retrieval
        original_symptoms = context["case"].get("symptoms_text", "")
        enriched_symptoms = original_symptoms + " " + chat_request.message
        
        retrieval_start = time.time()
        image_path = context["case"].get("image_path")
        results = retrieval.retrieve_all(image_path, enriched_symptoms, context["case"].get("animal_type"))
        reranked = reranker.rerank_all(enriched_symptoms, results)
        
        # 5. Recompute Confidence
        top_candidate = reranked["disease_candidates"][0]
        scores = extract_scores_from_retrieval(
            top_candidate, 
            reranked, 
            provided_symptoms=[s.strip() for s in enriched_symptoms.replace(",", " ").split()]
        )
        new_confidence = compute_confidence(**scores)
        old_confidence_score = context["case"].get("confidence_score", 0.0)
        
        # 6. Generate LLM Response
        prompt = build_followup_prompt(
            animal_type=context["case"].get("animal_type", "unknown"),
            symptom_text=original_symptoms,
            previous_questions=[], 
            new_answers=[{"question": "previous", "answer": "previous"}] if history else [],
            disease_hint=top_candidate["metadata"].get("disease")
        )
        
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        llm_res = await anyio.to_thread.run_sync(
            llm_router.generate,
            prompt, 
            SYSTEM_PROMPT,
            messages,
            {"confidence_score": new_confidence["score"]}
        )
        
        assistant_text = llm_res.get("text", "I'm sorry, I couldn't process that.")
        
        # 7. Update Diagnosis if needed
        diagnosis = None
        diagnosis_updated = False
        
        if new_confidence["score"] >= 0.75 and (new_confidence["score"] - old_confidence_score > 0.05):
            diagnosis_updated = True
            # Re-run full diagnostic validation
            diag_prompt = build_diagnosis_prompt(
                context["case"].get("animal_type", "unknown"),
                enriched_symptoms,
                reranked["disease_candidates"][:3],
                reranked["knowledge_chunks"][:3],
                new_confidence
            )
            # (Note: In a real app we'd use llm_validator here, for demo we'll use generate)
            diag_res = llm_router.generate(diag_prompt, SYSTEM_PROMPT)
            if diag_res.get("success"):
                diag_data = json.loads(diag_res["text"])
                diagnosis = DiagnosisResult(**diag_data)
                # Update memory with new diagnosis
                await memory.update_case(chat_request.case_id, {"primary_diagnosis": diagnosis.primary_diagnosis, "confidence_score": new_confidence["score"]})

        await memory.save_chat_message(chat_request.case_id, "assistant", assistant_text)
        
        return ChatResponse(
            case_id=chat_request.case_id,
            response=assistant_text,
            updated_confidence=ConfidenceResult(
                score=new_confidence["score"],
                percentage=new_confidence["percentage"],
                action=route_by_confidence(new_confidence)["action"],
                message=route_by_confidence(new_confidence)["message"],
                show_prediction=route_by_confidence(new_confidence)["show_prediction"]
            ),
            follow_up_questions=follow_up,
            diagnosis_updated=diagnosis_updated,
            diagnosis=diagnosis,
            success=True
        )

    except Exception as e:
        print(f"Error in chat_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
