from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import time
import anyio

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
    build_followup_prompt, SYSTEM_PROMPT, CONVERSATIONAL_SYSTEM_PROMPT
)
from app.limiter import limiter

router = APIRouter()
question_generator = FollowUpQuestionGenerator()

@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory),
    input_sanitizer=Depends(get_input_sanitizer),
    audit_logger=Depends(get_audit_logger)
):
    """
    Streaming chat endpoint for multi-turn conversational AI.
    Maintains context of animal, images, and symptoms.
    """
    try:
        # 1. Load Session Context
        context = await memory.get_session_context(chat_request.case_id)
        if not context:
            # Fallback for new chats if no case_id provided
            animal_type = "unknown"
            image_path = None
            symptoms = ""
        else:
            animal_type = context["case"].get("animal_type", "unknown")
            image_path = context["case"].get("image_path")
            symptoms = context["case"].get("symptoms_text", "")

        # 2. Sanitize & Save User Message
        sanitized = input_sanitizer.sanitize_text(chat_request.message)
        clean_msg = sanitized["sanitized_text"]
        await memory.save_chat_message(chat_request.case_id, "user", clean_msg)

        # 3. Load Chat History
        history = await memory.get_chat_history(chat_request.case_id, last_n=10)
        
        # 4. Hybrid Retrieval (Augmenting context with technical data)
        # We re-run retrieval to ensure the LLM has the latest medical context for the discussed symptoms
        enriched_query = f"{symptoms} {clean_msg}"
        retrieval_results = await retrieval.retrieve_all(image_path, enriched_query, animal_type)
        reranked = await anyio.to_thread.run_sync(reranker.rerank_all, enriched_query, retrieval_results)
        
        # 5. Build Dynamic Knowledge Context
        knowledge_str = "\n".join([c["text"] for c in reranked["knowledge_chunks"][:2]])
        cases_str = "\n".join([f"- {c['metadata'].get('disease')}" for c in reranked["disease_candidates"][:3]])
        
        full_system_prompt = CONVERSATIONAL_SYSTEM_PROMPT + f"\n\nCURRENT CASE CONTEXT:\n- Animal: {animal_type}\n- Image Provided: {'Yes' if image_path else 'No'}\n- Knowledge Base:\n{knowledge_str}\n- Similar Cases Seen:\n{cases_str}"

        # 6. Stream Generator
        async def event_generator():
            full_response = ""
            async for chunk in llm_router.generate_streaming(
                messages=history,
                system_prompt=full_system_prompt,
                image_paths=[image_path] if image_path else None
            ):
                full_response += chunk
                # Standard SSE format
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            
            # Save Assistant Message at the end
            await memory.save_chat_message(chat_request.case_id, "assistant", full_response)
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        print(f"Error in chat_stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        results = await retrieval.retrieve_all(image_path, enriched_symptoms, context["case"].get("animal_type"))
        reranked = await anyio.to_thread.run_sync(reranker.rerank_all, enriched_symptoms, results)
        
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
        
        # 8. Generate Follow-up Questions
        follow_up = question_generator.get_questions(
            action=route_by_confidence(new_confidence)["action"],
            disease_hint=top_candidate["metadata"].get("disease"),
            answered=[] # Logic to track answered questions could be added here
        )

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
