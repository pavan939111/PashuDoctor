import httpx
import os
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def api_post(endpoint, data=None, json_payload=None, files=None):
    """Generic helper for POST requests"""
    try:
        with httpx.Client(timeout=60.0) as client:
            if files:
                # For multipart/form-data
                resp = client.post(f"{API_BASE}{endpoint}", data=data, files=files)
            else:
                # For JSON
                resp = client.post(f"{API_BASE}{endpoint}", json=json_payload)
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": False, "error": f"API Error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Cannot connect to PashuDoctor API: {str(e)}"}

def api_get(endpoint):
    """Generic helper for GET requests"""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(f"{API_BASE}{endpoint}")
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": False, "error": f"API Error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Cannot connect to PashuDoctor API: {str(e)}"}

def api_delete(endpoint):
    """Generic helper for DELETE requests"""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.delete(f"{API_BASE}{endpoint}")
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": False, "error": f"API Error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Cannot connect to PashuDoctor API: {str(e)}"}
