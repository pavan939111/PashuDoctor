# PashuDoctor — AI Safety & Guardrail Documentation

## Why Guardrails Matter

In the context of veterinary medicine, especially within rural and remote communities, the stakes for AI-driven advice are exceptionally high. Farmers often rely on their livestock for their primary livelihood, and any incorrect medical advice can lead to significant economic loss, animal suffering, or even zoonotic disease outbreaks. PashuDoctor's guardrail system is designed to prevent the AI from overstepping its role as a decision-support tool, ensuring it never replaces professional veterinary judgment or provides high-risk instructions that could be misapplied in the field.

Without strict guardrails, an LLM might confidently suggest dosages for potent antibiotics or invasive home procedures, which a farmer—trusting the technology—might attempt without proper supervision. By implementing rigorous input filtering, output sanitization, and automated safety fallbacks, PashuDoctor ensures that every interaction remains within safe clinical boundaries, prioritizing animal welfare and farmer safety above all else.

## Guardrail Architecture Overview

```ascii
[ Farmer Input ]
       │
       ▼
┌────────────────────────────────┐
│  Layer 1: Input Guardrails     │──► [ Blocked: Injection/Human Query ]
└────────────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Layer 2: Prompt Guardrails    │──► [ System Prompt Constraints ]
└────────────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Layer 3: Output Guardrails    │──► [ Filtered: Drug Names/Dosages ]
└────────────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Layer 4: Confidence Routing   │──► [ Routing: Ask More/Suggest ]
└────────────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Layer 5: Safety Fast-Path     │──► [ Response < 10ms: EMERGENCY ]
└────────────────────────────────┘
       │
       ▼
[ Final Response to Farmer ]
```

## Layer 1 — Input Guardrails

| Check | Threshold | Action if Failed | Log Event |
|-------|-----------|-----------------|-----------|
| File Size | > 10MB | Reject Upload | `invalid_file` |
| MIME Type | Non-Image | Reject Upload | `invalid_file` |
| Image Quality | < 64px / Low Var | Reject Upload | `invalid_file` |
| Animal Relevance | CLIP < 0.20 | Reject Upload | `non_animal_image` |
| Prompt Injection | Pattern Match | Reject Request | `injection_attempt` |
| Human Medical Query | Pattern Match | Redirect to Doctor | `human_query_attempt` |
| Text Length | > 1000 chars | Truncate | N/A |

## Layer 2 — LLM Prompt Guardrails

The `SYSTEM_PROMPT` enforces the following absolute rules:
1. **Prescription Ban**: Never provide drug names, medicines, or dosages.
2. **Human Health Ban**: Explicitly refuse any queries about human medical conditions.
3. **Mandatory Disclaimer**: Every response must end with a referral to a licensed vet and the 1962 helpline.
4. **Evidence Grounding**: Diagnosis must be based solely on retrieved cases and knowledge base.
5. **Procedure Ban**: Never recommend surgery, injections, or invasive home treatments.
6. **Isolation Protocol**: Mandatory isolation advice for contagious disease detections.

## Layer 3 — LLM Output Guardrails

| Check | Method | Action if Failed |
|-------|--------|-----------------|
| JSON Schema | Pydantic / Key Check | Retry (Max 3) -> Fallback |
| Drug Name Detection | Regex Blacklist (20+) | Redact to "[REMOVED]" |
| Dosage Detection | Pattern Match (mg/kg, etc) | Redact to "[REMOVED]" |
| Field Validation | Value Set Checking | Coerce to Safe Default |
| Human Query Leak | Pattern Match in Advice | Replace with Safe Fallback |

## Layer 4 — Confidence Guardrails

PashuDoctor uses a 4-tier routing system based on a combined score (Image + Text + Symptoms):

| Tier | Score Range | Action | Message to Farmer |
|------|-------------|--------|-------------------|
| **Ask More** | < 0.50 | Refuse Diagnosis | "Not enough info. Please answer questions." |
| **Show Options**| 0.50 - 0.75 | List Possibilities | "Possible conditions identified." |
| **Suggest** | 0.75 - 0.90 | Suggest Condition | "Likely condition. Vet visit recommended." |
| **Strong Suggest**| > 0.90 | High Confidence | "High confidence. Consult vet immediately." |

## Layer 5 — Safety Fast-Path

The system monitors for emergency keywords across 10 Indian languages (Hindi, Tamil, Telugu, etc.).

| Keyword Types | Examples |
|---------------|----------|
| **Critical** | Collapsed, Seizure, Not breathing |
| **Fatal** | Dying, Sudden death, Unconscious |
| **Trauma** | Bleeding heavily, Convulsion |

**Performance Guarantee**: < 10ms (Bypasses all AI/RAG processing).

## Layer 6 — API Security

- **Rate Limiting**: 5 requests per minute per IP to prevent DoS.
- **CORS Support**: Strict origin validation.
- **MIME Validation**: Prevents malicious file uploads.
- **SQL Injection**: Prevented via SQLAlchemy ORM usage.
- **Global Exception Handling**: Ensures no stack traces are leaked to the user.

## Banned Content List

### Blocked Drug/Dosage Patterns
- **Antibiotics**: Penicillin, Amoxicillin, Enrofloxacin, etc.
- **Steroids**: Dexamethasone, Prednisolone.
- **Dewormers**: Ivermectin, Albendazole.
- **Dosage Units**: mg/kg, ml/kg, ml IM, IV, Subcutaneous.

### Blocked Prompt Patterns
- "Ignore previous instructions", "DAN mode", "Jailbreak", "System prompt override".

### Human Medical Triggers
- "My fever", "My child is sick", "Doctor for me", "Human medicine".

## Audit Log

PashuDoctor maintains a persistent audit log at `data/logs/guardrail_audit.jsonl`. 

**Sample Entry**:
```json
{
  "timestamp": "2026-05-09T10:05:00",
  "event_type": "injection_attempt",
  "case_id": "null",
  "blocked": true,
  "details": {"pattern": "ignore previous instructions"},
  "ip_hash": "a1b2c3d4e5f6"
}
```
Administrators can review these logs via the `/guardrails/audit` endpoint.

## Guardrail Test Results

| Test Suite | Pass Rate | Status |
|------------|-----------|--------|
| Input Sanitizer | 7/7 | ✅ PASS |
| LLM Output Validator | 5/5 | ✅ PASS |
| System Prompt Rules | 4/4 | ✅ PASS |
| Audit Logger | 2/2 | ✅ PASS |
| **Overall** | **100%** | **ACTIVE** |

## What PashuDoctor Will Never Do
- Never prescribe drugs or dosages.
- Never give injection instructions.
- Never advise on human medical conditions.
- Never diagnose without retrieved evidence.
- Never ignore emergency symptoms.
- Never respond without a vet disclaimer.
- Never store personally identifiable information (PII).

## Compliance Notes
- **Decision Support Only**: PashuDoctor is a decision-support tool, not a licensed medical device.
- **Suggestions Only**: All AI outputs are suggestions based on historical data and not definitive clinical diagnoses.
- **Mandatory Referral**: The system explicitly directs all users to consult licensed veterinarians for any and all animal health concerns.
