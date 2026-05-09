import os
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.dependencies import get_audit_logger, get_chroma, get_memory

router = APIRouter()

@router.get("/stats")
async def get_system_stats(
    chroma=Depends(get_chroma),
    audit=Depends(get_audit_logger),
    memory=Depends(get_memory)
):
    """
    Returns high-level observability stats for governance and monitoring.
    """
    try:
        audit_summary = audit.get_audit_summary()
        db_stats = chroma.get_collection_stats()
        
        return {
            "success": True,
            "governance": {
                "audit_summary": audit_summary,
                "safety_status": "Active",
            },
            "retrieval": {
                "collection_stats": db_stats,
                "engine": "Hybrid (Vector + BM25)",
                "reranker": "BGE-Reranker-v2"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    audit=Depends(get_audit_logger)
):
    """
    Returns raw audit logs for compliance review.
    """
    if not audit:
        return {"logs": []}
        
    logs = []
    if os.path.exists(audit.LOG_FILE):
        with open(audit.LOG_FILE, "r") as f:
            for line in f:
                logs.append(json.loads(line))
                if len(logs) >= limit:
                    break
    return {"logs": logs[::-1]} # Latest first
