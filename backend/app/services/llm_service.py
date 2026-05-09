import json
import time
import os
import google.generativeai as genai
from PIL import Image
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

class GeminiService:
    def __init__(self):
        # 1. Load keys and initialize
        self.api_keys = settings.get_gemini_keys()
        self.current_key_idx = 0
        self._configure_gemini()
        
        # 2. Config
        self.generation_config = {
            "temperature": 0.1, # Lower temperature for JSON
            "top_p": 0.9,
            "max_output_tokens": 2048,
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        print(f"GeminiService ready: gemini-1.5-flash ({len(self.api_keys)} keys available)")

    def _configure_gemini(self):
        if not self.api_keys:
            print("WARNING: No Gemini API keys found.")
            return
        key = self.api_keys[self.current_key_idx]
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-flash-latest")

    def rotate_key(self):
        if not self.api_keys: return
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        self._configure_gemini()
        print(f"GeminiService rotated to Key #{self.current_key_idx + 1}")

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        image_paths: List[str] = None,
        retries: int = None
    ) -> Dict[str, Any]:
        if retries is None:
            retries = len(self.api_keys)
        try:
            content = []
            if system_prompt:
                content.append(system_prompt)
            
            if image_paths:
                for path in image_paths:
                    if os.path.exists(path):
                        img = Image.open(path)
                        content.append(img)
            
            content.append(prompt)
            
            start_time = time.time()
            response = self.model.generate_content(
                content,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            if not response.text:
                reason = "unknown"
                if response.candidates:
                    reason = response.candidates[0].finish_reason.name
                raise ValueError(f"Gemini returned empty text (Reason: {reason})")
                
            return {
                "text": response.text,
                "model": "gemini-1.5-flash",
                "total_duration_ms": duration_ms,
                "success": True
            }
        except Exception as e:
            err_msg = str(e)
            # 429: Quota, 401: Unauthorized, 403: Forbidden/PermissionDenied
            retry_worthy = ["429", "ResourceExhausted", "401", "Unauthorized", "403", "PermissionDenied", "invalid api key"]
            
            if any(term.lower() in err_msg.lower() for term in retry_worthy) and retries > 0:
                print(f"Gemini error ({err_msg}). Rotating key and retrying...")
                self.rotate_key()
                return self.generate(prompt, system_prompt, image_paths, retries - 1)
            
            print(f"Gemini generation error: {e}")
            return {
                "text": "",
                "model": "gemini-1.5-flash",
                "success": False,
                "error": err_msg
            }

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        retries: int = None
    ) -> Dict[str, Any]:
        if retries is None:
            retries = len(self.api_keys)
        try:
            # Convert messages to Gemini format
            history = []
            for msg in messages[:-1]: # All but last
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
            chat = self.model.start_chat(history=history)
            
            last_msg = messages[-1]["content"]
            
            start_time = time.time()
            response = chat.send_message(
                last_msg, 
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            return {
                "text": response.text,
                "model": "gemini-1.5-flash",
                "total_duration_ms": duration_ms,
                "success": True
            }
        except Exception as e:
            err_msg = str(e)
            retry_worthy = ["429", "ResourceExhausted", "401", "Unauthorized", "403", "PermissionDenied", "invalid api key"]
            
            if any(term.lower() in err_msg.lower() for term in retry_worthy) and retries > 0:
                print(f"Gemini Chat error ({err_msg}). Rotating key and retrying...")
                self.rotate_key()
                return self.generate_with_history(messages, system_prompt, retries - 1)
                
            return {
                "text": "",
                "model": "gemini-1.5-flash",
                "success": False,
                "error": err_msg
            }

    def analyze_image_disease(
        self,
        image_paths: List[str],
        symptom_text: str,
        animal_type: str
    ) -> Dict[str, Any]:
        prompt = (
            f"You are a veterinary AI assistant.\n"
            f"Animal type: {animal_type}\n"
            f"Reported symptoms: {symptom_text}\n\n"
            f"Analyze this image and provide ONLY valid JSON:\n"
            "{\n"
            "  \"disease\": \"string\",\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"visible_symptoms\": [\"list\"],\n"
            "  \"severity\": \"mild/moderate/severe\",\n"
            "  \"body_parts_affected\": [\"list\"],\n"
            "  \"reasoning\": \"string\"\n"
            "}"
        )
        
        result = self.generate(prompt=prompt, image_paths=image_paths)
        if result["success"]:
            try:
                text = result["text"].strip()
                if text.startswith("```json"):
                    text = text[7:-3].strip()
                elif text.startswith("```"):
                    text = text[3:-3].strip()
                
                return json.loads(text)
            except Exception as e:
                return {
                    "error": f"Failed to parse Gemini JSON: {e}",
                    "raw_text": result["text"]
                }
        return result

class LLMRouter:
    def __init__(self):
        self.gemini = GeminiService()
        self.stats = {
            "total_calls": 0,
            "gemini_calls": 0,
            "fallback_triggers": 0
        }
        print("LLMRouter ready (Gemini-only mode)")

    def route(self, routing_context: Dict[str, Any]) -> str:
        return "gemini"

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        routing_context: Dict[str, Any] = {},
        image_paths: List[str] = None,
        messages: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        self.stats["total_calls"] += 1
        self.stats["gemini_calls"] += 1
        
        if messages:
            response = self.gemini.generate_with_history(messages, system_prompt)
        else:
            response = self.gemini.generate(prompt, system_prompt, image_paths)
            
        response["routed_to"] = "gemini"
        return response

    def generate_streaming(
        self,
        prompt: str,
        routing_context: Dict[str, Any] = {}
    ):
        try:
            self.stats["total_calls"] += 1
            self.stats["gemini_calls"] += 1
            response = self.gemini.model.generate_content(prompt, stream=True)
            for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"\n[Gemini Stream Error: {e}]\n"

    def get_routing_stats(self) -> Dict[str, int]:
        return self.stats
