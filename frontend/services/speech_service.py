import speech_recognition as sr
import os
import tempfile
import logging
from typing import Optional
from streamlit_mic_recorder import mic_recorder
from services.language_service import LanguageService

class SpeechService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.logger = logging.getLogger("pashudoctor.frontend.speech_service")

    def record_from_microphone(
        self,
        duration: int = 10,
        language_code: str = "en-IN"
    ) -> dict:
        """
        Records audio from the local system microphone and transcribes it.
        """
        try:
            with sr.Microphone() as source:
                self.logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info(f"Listening for up to {duration} seconds...")
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=duration
                )

            self.logger.info("Transcribing audio...")
            text = self.recognizer.recognize_google(
                audio,
                language=language_code
            )
            
            return {
                "text": text,
                "language": language_code,
                "success": True,
                "method": "google_sr"
            }

        except sr.UnknownValueError:
            return {"text": "", "success": False, "error": "no_speech_detected"}
        except sr.RequestError as e:
            return {"text": "", "success": False, "error": f"sr_api_error: {e}"}
        except (OSError, Exception) as e:
            self.logger.error(f"Microphone error: {e}")
            return {"text": "", "success": False, "error": "no_microphone"}

    def transcribe_audio_file(
        self,
        audio_file_path: str,
        language_code: str = "en-IN"
    ) -> dict:
        """
        Transcribes an existing audio file.
        """
        try:
            if not os.path.exists(audio_file_path):
                return {"text": "", "success": False, "error": "file_not_found"}

            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(
                audio,
                language=language_code
            )
            
            return {
                "text": text,
                "language": language_code,
                "success": True,
                "method": "google_sr_file"
            }

        except sr.UnknownValueError:
            return {"text": "", "success": False, "error": "no_speech_detected"}
        except sr.RequestError as e:
            return {"text": "", "success": False, "error": f"sr_api_error: {e}"}
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return {"text": "", "success": False, "error": str(e)}

    def record_and_translate(
        self,
        duration: int = 10,
        ui_language: str = "Hindi",
        language_service: LanguageService = None
    ) -> dict:
        """
        Records audio and automatically translates it to English if needed.
        """
        if not language_service:
            language_service = LanguageService()

        # a. Get language code from SUPPORTED_LANGUAGES
        sr_code = "en-IN"
        if ui_language in language_service.SUPPORTED_LANGUAGES:
            sr_code = language_service.SUPPORTED_LANGUAGES[ui_language]["sr"]

        # b. Record audio with record_from_microphone
        record_res = self.record_from_microphone(duration=duration, language_code=sr_code)

        if record_res["success"]:
            text = record_res["text"]
            translated_text = text
            
            # c. If success and ui_language != "English", translate
            if ui_language != "English":
                trans_res = language_service.translate_to_english(text, ui_language)
                translated_text = trans_res.get("translated", text)
            
            return {
                "original_text": text,
                "translated_text": translated_text,
                "language": ui_language,
                "success": True,
                "error": None
            }
        
        return {
            "original_text": "",
            "translated_text": "",
            "language": ui_language,
            "success": False,
            "error": record_res.get("error")
        }

    def check_microphone_available(self) -> bool:
        """
        Checks if a local microphone is available.
        """
        try:
            with sr.Microphone() as source:
                return True
        except:
            return False

    def streamlit_record(
        self, 
        language: str, 
        language_service: LanguageService = None
    ) -> Optional[dict]:
        """
        Browser-compatible recording using streamlit-mic-recorder.
        """
        if not language_service:
            language_service = LanguageService()

        sr_code = "en-IN"
        if language in language_service.SUPPORTED_LANGUAGES:
            sr_code = language_service.SUPPORTED_LANGUAGES[language]["sr"]

        audio_data = mic_recorder(
            start_prompt=f"🎤 Click to speak ({language})",
            stop_prompt="🛑 Click to stop",
            key=f"mic_{language}"
        )

        if audio_data and "bytes" in audio_data:
            # Save bytes to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data["bytes"])
                tmp_path = tmp.name

            try:
                # Transcribe with transcribe_audio_file
                res = self.transcribe_audio_file(tmp_path, language_code=sr_code)
                
                if res["success"]:
                    text = res["text"]
                    translated_text = text
                    if language != "English":
                        trans_res = language_service.translate_to_english(text, language)
                        translated_text = trans_res.get("translated", text)
                    
                    return {
                        "original_text": text,
                        "translated_text": translated_text,
                        "language": language,
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "original_text": "",
                        "translated_text": "",
                        "language": language,
                        "success": False,
                        "error": res.get("error")
                    }
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        return None
