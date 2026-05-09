from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import time

from app.models.schemas import (
    ChatRequest, ChatResponse, AnalyzeResponse, 
    FollowUpRequest, ConfidenceResult, DiagnosisResult,
    AnimalDetectionResult, DiseaseCandidate
)
from app.dependencies import (
    get_retrieval, get_reranker, get_llm, get_memory, get_text_service
)
from app.utils.confidence import (
    compute_confidence, route_by_confidence, extract_scores_from_retrieval, 
    FollowUpQuestionGenerator
)
from app.utils.prompts import (
    build_diagnosis_prompt, format_response_for_farmer, 
    build_followup_prompt, SYSTEM_PROMPT
)

router = APIRouter()
question_generator = FollowUpQuestionGenerator()

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory)
):
    try:
        # 1. Load Session Context
        context = await memory.get_session_context(request.case_id)
        if not context:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # 2. Save User Message
        await memory.save_chat_message(request.case_id, "user", request.message)
        
        # 3. Load History
        history = await memory.get_chat_history(request.case_id, last_n=10)
        
        # 4. Check for New Symptom Info & Re-run Retrieval
        # (Simple heuristic: if message is long enough or contains key symptom words)
        original_symptoms = context["case"].get("symptoms_text", "")
        enriched_symptoms = original_symptoms + " " + request.message
        
        retrieval_start = time.time()
        # For chat, we might not have the image anymore, use text-only retrieval or cached image path
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
        # We use follow-up prompt style
        prompt = build_followup_prompt(
            animal_type=context["case"].get("animal_type", "unknown"),
            symptom_text=original_symptoms,
            previous_questions=[], # Can extract from history if needed
            new_answers=[{"question": "previous", "answer": "previous"}] if history else [],
            disease_hint=top_candidate["metadata"].get("disease")
        )
        
        # In chat mode, we pass the history to the LLM
        # Converting history to format expected by LLM
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        llm_res = llm_router.generate(
            prompt="", # generate uses messages if provided
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            routing_context={"confidence_score": new_confidence["score"]}
        )
        
        # 7. Check if Diagnosis Updated
        diagnosis_updated = False
        if new_confidence["score"] - old_confidence_score > 0.10:
            diagnosis_updated = True
            # Could trigger full diagnosis generation here if needed
            
        # 8. Follow-up Questions
        follow_up = []
        if new_confidence["score"] < 0.75:
            follow_up = question_generator.get_questions(
                action="ask_more",
                disease_hint=top_candidate["metadata"].get("disease"),
                answered=[msg["content"] for msg in history if msg["role"] == "assistant"]
            )
            
        # 9. Save Assistant Response
        assistant_text = llm_res.get("text", "I'm sorry, I couldn't process that.")
        await memory.save_chat_message(request.case_id, "assistant", assistant_text)
        
        return ChatResponse(
            case_id=request.case_id,
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
            success=True
        )

    except Exception as e:
        print(f"Error in chat_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/answer-questions", response_model=AnalyzeResponse)
async def answer_questions(
    request: FollowUpRequest,
    retrieval=Depends(get_retrieval),
    reranker=Depends(get_reranker),
    llm_router=Depends(get_llm),
    memory=Depends(get_memory)
):
    try:
        # 1. Load Session
        context = await memory.get_session_context(request.case_id)
        if not context:
            raise HTTPException(status_code=404, detail="Case not found")
            
        # 2. Build Enriched Symptoms
        original = context["case"].get("symptoms_text", "")
        answers_text = " ".join([qa["answer"] for qa in request.question_answers])
        enriched = original + " " + answers_text
        
        # 3. Retrieval & Reranking
        image_path = context["case"].get("image_path")
        results = retrieval.retrieve_all(image_path, enriched, context["case"].get("animal_type"))
        reranked = reranker.rerank_all(enriched, results)
        
        # 4. Confidence
        top_candidate = reranked["disease_candidates"][0]
        scores = extract_scores_from_retrieval(
            top_candidate, 
            reranked, 
            provided_symptoms=[s.strip() for s in enriched.replace(",", " ").split()]
        )
        new_confidence = compute_confidence(**scores)
        routing = route_by_confidence(new_confidence)
        
        # 5. Diagnosis Generation if confidence improved
        diagnosis = None
        model_used = "none"
        llm_time = 0
        
        if new_confidence["score"] >= 0.50:
            llm_start = time.time()
            prompt = build_diagnosis_prompt(
                context["case"].get("animal_type", "unknown"),
                enriched,
                reranked["disease_candidates"][:3],
                reranked["knowledge_chunks"][:3],
                new_confidence,
                answered_questions=request.question_answers
            )
            llm_res = llm_router.generate(prompt, system_prompt=SYSTEM_PROMPT)
            llm_time = (time.time() - llm_start) * 1000
            model_used = llm_res.get("routed_to", "unknown")
            
            if llm_res["success"]:
                try:
                    text = llm_res["text"].strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    diag_data = json.loads(text)
                    formatted = format_response_for_farmer(diag_data)
                    
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

        # 6. Save Q&A pairs to History
        for qa in request.question_answers:
            await memory.save_chat_message(request.case_id, "assistant", qa["question"])
            await memory.save_chat_message(request.case_id, "user", qa["answer"])
            
        if diagnosis:
            await memory.save_chat_message(request.case_id, "assistant", diagnosis.formatted_response)

        return AnalyzeResponse(
            case_id=request.case_id,
            animal_detection=AnimalDetectionResult(
                animal=context["case"].get("animal_type", "unknown"),
                confidence=0.0,
                method="cached"
            ),
            confidence=ConfidenceResult(
                score=new_confidence["score"],
                percentage=new_confidence["percentage"],
                action=routing["action"],
                message=routing["message"],
                show_prediction=routing["show_prediction"]
            ),
            diagnosis=diagnosis,
            follow_up_questions=[],
            top_candidates=[
                DiseaseCandidate(
                    disease=c["metadata"].get("disease", "unknown"),
                    animal=c["metadata"].get("animal", "unknown"),
                    body_part=c["metadata"].get("body_part", "unknown"),
                    severity=c["metadata"].get("severity", "unknown"),
                    final_score=c.get("final_score", 0.0),
                    reranker_score=c.get("reranker_score", 0.0)
                ) for c in reranked["disease_candidates"][:5]
            ],
            retrieval_time_ms=0.0, # Approximate or skip
            llm_time_ms=llm_time,
            model_used=model_used,
            success=True
        )

    except Exception as e:
        print(f"Error in answer_questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{case_id}")
async def get_chat_history(
    case_id: str,
    memory=Depends(get_memory)
):
    try:
        history = await memory.get_chat_history(case_id, last_n=50)
        if history is None:
            raise HTTPException(status_code=404, detail="Case not found")
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/stream/{case_id}")
async def chat_stream(
    websocket: WebSocket,
    case_id: str,
    llm_router=Depends(get_llm),
    memory=Depends(get_memory)
):
    await websocket.accept()
    try:
        # 1. Receive initial data
        data = await websocket.receive_text()
        msg_data = json.loads(data)
        user_message = msg_data.get("message", "")
        
        # 2. Save user message
        await memory.save_chat_message(case_id, "user", user_message)
        
        # 3. Load Context
        context = await memory.get_session_context(case_id)
        
        # 4. Start Streaming
        # For simplicity, we just stream a general response based on message
        # In production, we'd build a full prompt here
        full_response = ""
        for chunk in llm_router.generate_streaming(user_message, routing_context={"confidence_score": 0.8}):
            await websocket.send_text(json.dumps({"token": chunk, "done": False}))
            full_response += chunk
            
        # 5. Save assistant message
        await memory.save_chat_message(case_id, "assistant", full_response)
        
        # 6. Send Done
        await websocket.send_text(json.dumps({"token": "", "done": True}))
        
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for case {case_id}")
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e), "done": True}))
    finally:
        await websocket.close()
