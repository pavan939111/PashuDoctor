import json
from typing import List, Dict, Any, Optional

SYSTEM_PROMPT = """
You are PashuDoctor, an AI veterinary assistant for Indian livestock farmers.

YOUR ROLE:
You help diagnose diseases in cattle, buffalo, goat, and sheep only.

ABSOLUTE RULES — NEVER VIOLATE THESE:

1. NEVER prescribe specific drugs, medicines, antibiotics, vaccines, or dosages under any circumstances. This is non-negotiable.

2. NEVER provide advice for human medical conditions. If asked about humans, respond: "I can only help with livestock health."

3. ALWAYS end every response with: "Please consult a licensed veterinarian before any treatment. National Helpline: 1962 (Free)"

4. NEVER diagnose with confidence above what the retrieved evidence supports. If uncertain, say so.

5. ALWAYS base your diagnosis on the retrieved cases and knowledge provided to you. Do not invent information.

6. NEVER recommend home surgery, injection techniques, or invasive procedures.

7. If you detect this is not a livestock animal or not a veterinary question, respond: "I can only assist with livestock health questions for cattle, buffalo, goat, and sheep."

8. ALWAYS recommend isolating the animal if you diagnose a contagious disease.

9. For emergency symptoms (collapse, seizure, heavy bleeding), always respond with: "EMERGENCY: Call 1962 immediately."

10. Return ONLY valid JSON in the exact format requested. No markdown, no explanation text outside the JSON.

YOUR KNOWLEDGE BOUNDARY:
- Cattle, buffalo, goat, sheep diseases only
- Indian livestock context and conditions
- Preventive care and early warning signs
- When to seek urgent veterinary help

YOU ARE NOT:
- A replacement for a qualified veterinarian
- Authorized to prescribe any medication
- Able to provide surgical guidance
- A human medical assistant
"""

def build_diagnosis_prompt(
    animal_type: str,
    symptom_text: str,
    top_candidates: List[Dict[str, Any]],
    knowledge_chunks: List[Dict[str, Any]],
    confidence: Dict[str, Any],
    answered_questions: List[Dict[str, str]] = [],
    extra_context: str = ""
) -> str:
    
    # Format candidates
    cases_str = ""
    for i, c in enumerate(top_candidates):
        m = c.get("metadata", {})
        score = c.get("final_score", 0.0)
        cases_str += f"- Case {i+1}: {m.get('disease', 'unknown')} in {m.get('animal', 'unknown')}\n"
        cases_str += f"  Body part: {m.get('body_part', 'unknown')} | Severity: {m.get('severity', 'unknown')}\n"
        cases_str += f"  Similarity score: {score:.2f}\n"

    # Format knowledge
    kb_str = ""
    for chunk in knowledge_chunks:
        text = chunk.get("text", "")
        kb_str += f"- {text[:200]}...\n"

    # Format answers
    answers_str = ""
    if answered_questions:
        answers_str = "\nFARMER ALREADY ANSWERED:\n"
        for qa in answered_questions:
            q = qa.get("question", "")
            a = qa.get("answer", "")
            answers_str += f"Q: {q}\nA: {a}\n"

    prompt = f"""
ANIMAL: {animal_type}
REPORTED SYMPTOMS: {symptom_text}
ADDITIONAL CONTEXT: {extra_context}

RETRIEVED SIMILAR CASES:
{cases_str}

VETERINARY KNOWLEDGE:
{kb_str}

CONFIDENCE LEVEL: {confidence.get('percentage', 0)}%
{answers_str}

YOUR TASKS:
1. Based on the evidence above, what is the most likely disease?
2. List the key matching symptoms that support this diagnosis.
3. Differential Diagnosis: Briefly explain why it is NOT the most likely alternative (e.g., "Why not FMD? Blisters on hooves not reported").
4. Breakdown the confidence score into:
   - Image Similarity (0.0 to 1.0)
   - Symptom Match (0.0 to 1.0)
   - Knowledge Grounding (0.0 to 1.0)
5. List immediate precautions, warning signs, and herd prevention.

Format your response as JSON:
{{
  "primary_diagnosis": "string",
  "alternative_diagnoses": ["string"],
  "matching_symptoms": ["string"],
  "differential_reasoning": "string",
  "image_confidence": float,
  "symptom_confidence": float,
  "knowledge_confidence": float,
  "immediate_precautions": ["string"],
  "urgent_warning_signs": ["string"],
  "herd_prevention": ["string"],
  "farmer_advice": "string",
  "vet_urgency": "immediate/within_24h/within_week/monitor"
}}
"""
    return prompt.strip()

def build_followup_prompt(
    animal_type: str,
    symptom_text: str,
    previous_questions: List[str],
    new_answers: List[Dict[str, str]],
    disease_hint: str = None
) -> str:
    history = ""
    for qa in new_answers:
        history += f"Q: {qa['question']}\nA: {qa['answer']}\n"
        
    prompt = f"""
You are refining a diagnosis for a {animal_type}.
Initial symptoms: {symptom_text}
{f'Suspected condition: {disease_hint}' if disease_hint else ''}

Conversation history:
{history}

Synthesise this information. What new details have been revealed? 
How do these change the likelihood of the suspected condition?
Provide a brief summary of the updated assessment.
"""
    return prompt.strip()

def build_explanation_prompt(
    diagnosis_result: Dict[str, Any],
    top_candidates: List[Dict[str, Any]],
    confidence: Dict[str, Any]
) -> str:
    prompt = f"""
Explain why PashuDoctor suggested the diagnosis: {diagnosis_result.get('primary_diagnosis', 'Unknown')}.

Evidence:
- Found {len(top_candidates)} similar cases in the database.
- Confidence score: {confidence.get('percentage', 0)}%.
- Key matched symptoms: {', '.join(diagnosis_result.get('matching_symptoms', []))}.

Provide a farmer-friendly explanation. Mention what would increase certainty (e.g., more photos, specific tests).
"""
    return prompt.strip()

def build_severity_prompt(
    animal_type: str,
    diagnosis: str,
    symptom_text: str,
    answered_questions: List[Dict[str, str]]
) -> str:
    prompt = f"""
Classify the severity of {diagnosis} in this {animal_type}.
Symptoms: {symptom_text}
Farmer answers: {json.dumps(answered_questions)}

Criteria:
- Mild: Animal is eating, fever is low, symptoms are localized.
- Moderate: Animal has reduced appetite, moderate fever, multiple lesions.
- Severe: Animal is not eating, high fever, difficulty breathing or walking.
- Emergency: Animal is recumbent (cannot stand), extremely high fever, sudden death in herd.

Return ONLY one word: mild / moderate / severe / emergency.
"""
    return prompt.strip()

def format_response_for_farmer(
    llm_response: Dict[str, Any],
    language: str = "english"
) -> str:
    primary = llm_response.get("primary_diagnosis", "Unknown Condition")
    percentage = llm_response.get("confidence_percentage", "N/A")
    
    symptoms = "\n".join([f"- {s}" for s in llm_response.get("matching_symptoms", [])])
    precautions = "\n".join([f"- {p}" for p in llm_response.get("immediate_precautions", [])])
    warnings = "\n".join([f"- {w}" for w in llm_response.get("urgent_warning_signs", [])])
    
    text = f"""
Diagnosis: {primary}
Confidence: {percentage}%

Matching symptoms:
{symptoms}

Immediate steps:
{precautions}

See vet immediately if:
{warnings}

{llm_response.get('farmer_advice', '')}

Please consult a licensed veterinarian.
"""
    return text.strip()
