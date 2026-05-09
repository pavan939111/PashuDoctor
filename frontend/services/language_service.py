import os
from deep_translator import GoogleTranslator
from langdetect import detect
from gtts import gTTS
import logging
from utils.connectivity import is_online

class LanguageService:
    SUPPORTED_LANGUAGES = {
        "English":    {"code": "en", "gtts": "en", "sr": "en-IN", "flag": "[EN]"},
        "Hindi":      {"code": "hi", "gtts": "hi", "sr": "hi-IN", "flag": "[HI]"},
        "Tamil":      {"code": "ta", "gtts": "ta", "sr": "ta-IN", "flag": "[TA]"},
        "Telugu":     {"code": "te", "gtts": "te", "sr": "te-IN", "flag": "[TE]"},
        "Kannada":    {"code": "kn", "gtts": "kn", "sr": "kn-IN", "flag": "[KN]"},
        "Malayalam":  {"code": "ml", "gtts": "ml", "sr": "ml-IN", "flag": "[ML]"},
        "Marathi":    {"code": "mr", "gtts": "mr", "sr": "mr-IN", "flag": "[MR]"},
        "Bengali":    {"code": "bn", "gtts": "bn", "sr": "bn-IN", "flag": "[BN]"},
        "Punjabi":    {"code": "pa", "gtts": "pa", "sr": "pa-IN", "flag": "[PA]"},
        "Gujarati":   {"code": "gu", "gtts": "gu", "sr": "gu-IN", "flag": "[GU]"}
    }

    def __init__(self):
        self.logger = logging.getLogger("pashudoctor.frontend.language_service")
        self._argos_installed = False # Lazy load argos

    def translate_to_english(self, text: str, source_lang: str) -> dict:
        """
        Translates text from source_lang to English.
        """
        try:
            if not text or text.strip() == "":
                return {"original": text, "translated": text, "source_lang": source_lang, "success": True}

            lang_code = source_lang
            if source_lang in self.SUPPORTED_LANGUAGES:
                lang_code = self.SUPPORTED_LANGUAGES[source_lang]["code"]

            if lang_code == "en":
                return {"original": text, "translated": text, "source_lang": "en", "success": True}

            if is_online():
                translator = GoogleTranslator(source=lang_code, target="en")
                translated = translator.translate(text)
            else:
                self.logger.info("Offline mode: Using ArgosTranslate fallback...")
                translated = self._argos_translate(text, lang_code, "en")

            return {
                "original": text,
                "translated": translated,
                "source_lang": source_lang,
                "success": True
            }
        except Exception as e:
            self.logger.error(f"Translation to English error: {e}")
            return {"original": text, "translated": text, "success": False, "error": str(e)}

    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translates English text to target_lang.
        """
        try:
            if not text or text.strip() == "":
                return text

            lang_code = target_lang
            if target_lang in self.SUPPORTED_LANGUAGES:
                lang_code = self.SUPPORTED_LANGUAGES[target_lang]["code"]

            if lang_code == "en":
                return text

            if is_online():
                translator = GoogleTranslator(source="en", target=lang_code)
                return translator.translate(text)
            else:
                self.logger.info("Offline mode: Using ArgosTranslate fallback...")
                return self._argos_translate(text, "en", lang_code)
        except Exception as e:
            self.logger.error(f"Translation from English error: {e}")
            return text

    def _argos_translate(self, text: str, from_code: str, to_code: str) -> str:
        """Helper for offline translation using Argos Translate"""
        try:
            import argostranslate.package
            import argostranslate.translate
            
            # Simple check/setup - in production, packages should be pre-installed
            return argostranslate.translate.translate(text, from_code, to_code)
        except Exception as e:
            self.logger.error(f"ArgosTranslate error: {e}")
            return f"[Offline Translation Error: {text}]"

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the provided text.
        Returns language code (e.g. 'hi').
        """
        try:
            if not text or text.strip() == "":
                return "en"
            return detect(text)
        except Exception as e:
            self.logger.error(f"Language detection error: {e}")
            return "en"

    def text_to_speech(self, text: str, lang: str, output_path: str) -> bool:
        """
        Converts text to speech and saves it to output_path.
        lang is the name (e.g. 'Hindi').
        """
        try:
            if not text or text.strip() == "":
                return False

            if not is_online():
                self.logger.warning("Offline mode: gTTS is disabled.")
                return False

            lang_code = "en"
            if lang in self.SUPPORTED_LANGUAGES:
                lang_code = self.SUPPORTED_LANGUAGES[lang]["gtts"]
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(output_path)
            return True
        except Exception as e:
            self.logger.error(f"Text to speech error: {e}")
            return False

    def get_disease_terms(self, lang: str) -> dict:
        """
        Returns translated disease names for UI display.
        """
        # Hardcoded translations for all 6 diseases in all 10 languages
        terms = {
            "mastitis": {
                "English": "Mastitis",
                "Hindi": "थनैला रोग",
                "Tamil": "மடி அழற்சி",
                "Telugu": "పొదుగు వ్యాధి",
                "Kannada": "ಮಾಸ್ಟೈಟಿಸ್",
                "Malayalam": "മാസ്റ്റൈറ്റിസ്",
                "Marathi": "थानेला रोग",
                "Bengali": "ম্যাস্টাইটিস",
                "Punjabi": "ਮਾਸਟਾਈਟਿਸ",
                "Gujarati": "મેસ્ટાઇટિસ"
            },
            "foot_and_mouth": {
                "English": "Foot and Mouth Disease",
                "Hindi": "खुरपका-मुँहपका रोग",
                "Tamil": "கோமாரி நோய்",
                "Telugu": "గాలికుంటు వ్యాధి",
                "Kannada": "ಕಾಲು ಮತ್ತು ಬಾಯಿ ರೋಗ",
                "Malayalam": "കുരലടപ്പൻ",
                "Marathi": "लाळ्या खुरकुत",
                "Bengali": "ক্ষুররোগ",
                "Punjabi": "ਮੂੰਹ ਖੁਰ",
                "Gujarati": "ખરવા મસા"
            },
            "lumpy_skin_disease": {
                "English": "Lumpy Skin Disease",
                "Hindi": "गाँठदार त्वचा रोग",
                "Tamil": "சரும கட்டி நோய்",
                "Telugu": "ముద్ద చర్మ వ్యాధి",
                "Kannada": "ಚರ್ಮ ಗಂಟು ರೋಗ",
                "Malayalam": "ലമ്പി സ്കിൻ ഡിസീസ്",
                "Marathi": "लम्पी त्वचा रोग",
                "Bengali": "লাম্পি স্কিন ডিজিজ",
                "Punjabi": "ਲੰਪੀ ਸਕਿਨ ਬਿਮਾਰੀ",
                "Gujarati": "લમ્પી સ્કિન રોગ"
            },
            "blackquarter": {
                "English": "Black Quarter",
                "Hindi": "लंगड़िया बुखार",
                "Tamil": "சப்பை நோய்",
                "Telugu": "జబ్బ వాపు",
                "Kannada": "ಚಪ್ಪೆ ರೋಗ",
                "Malayalam": "കരിങ്കാലൻ",
                "Marathi": "घटसर्प",
                "Bengali": "তড়কা",
                "Punjabi": "ਗਲਘੋਟੂ",
                "Gujarati": "ગલગોટો"
            },
            "hemorrhagic_septicemia": {
                "English": "Hemorrhagic Septicemia",
                "Hindi": "गलघोंटू",
                "Tamil": "தொண்டை அடைப்பான்",
                "Telugu": "గొంతు వాపు",
                "Kannada": "ಗಳಲೆ ರೋಗ",
                "Malayalam": "കരളടപ്പൻ",
                "Marathi": "फऱ्या",
                "Bengali": "গলাফুলা",
                "Punjabi": "ਫਰਿਆ",
                "Gujarati": "ફરિયો"
            },
            "ppr": {
                "English": "PPR (Goat Plague)",
                "Hindi": "पीपीआर (भेड़-बकरी प्लेग)",
                "Tamil": "ஆட்டு பிளேக் (PPR)",
                "Telugu": "పి.పి.ఆర్ వ్యాధి",
                "Kannada": "ಪಿ.ಪಿ.ಆರ್ ರೋಗ",
                "Malayalam": "ആട് വസന്ത",
                "Marathi": "पीपीआर",
                "Bengali": "পিপিআর",
                "Punjabi": "ਪੀਪੀਆਰ",
                "Gujarati": "પીપીઆર"
            }
        }
        
        result = {}
        for disease, trans in terms.items():
            result[disease] = trans.get(lang, trans["English"])
        return result

    def get_ui_strings(self, lang: str) -> dict:
        """
        Returns translated UI labels for the selected language.
        """
        # Hardcoding UI strings for 10 languages
        # Note: In a real app, this would be a JSON file.
        ui_data = {
            "English": {
                "upload_photo": "Upload Animal Photo",
                "describe_symptoms": "Describe Symptoms",
                "analyze_button": "Analyze Health",
                "chat_with_doctor": "Chat with PashuDoctor",
                "my_cases": "My Cases",
                "new_analysis": "New Analysis",
                "confidence": "Confidence",
                "diagnosis": "Diagnosis",
                "precautions": "Precautions",
                "consult_vet": "Consult a Veterinarian",
                "speak_now": "Speak Now",
                "listening": "Listening...",
                "processing": "Processing...",
                "no_speech_detected": "No speech detected. Try again.",
                "animal_detected": "Animal Detected",
                "follow_up_questions": "Follow-up Questions",
                "submit_answers": "Submit Answers",
                "feedback_correct": "Correct",
                "feedback_incorrect": "Incorrect",
                "thank_you": "Thank You"
            },
            "Hindi": {
                "upload_photo": "पशु का फोटो अपलोड करें",
                "describe_symptoms": "लक्षणों का वर्णन करें",
                "analyze_button": "स्वास्थ्य विश्लेषण करें",
                "chat_with_doctor": "पशु डॉक्टर से चैट करें",
                "my_cases": "मेरे मामले",
                "new_analysis": "नया विश्लेषण",
                "confidence": "आत्मविश्वास",
                "diagnosis": "रोग का निदान",
                "precautions": "सावधानियां",
                "consult_vet": "पशु चिकित्सक से सलाह लें",
                "speak_now": "अभी बोलें",
                "listening": "सुन रहा हूँ...",
                "processing": "प्रसंस्करण हो रहा है...",
                "no_speech_detected": "कोई आवाज नहीं मिली। फिर कोशिश करें।",
                "animal_detected": "पशु की पहचान हुई",
                "follow_up_questions": "अगले प्रश्न",
                "submit_answers": "जवाब भेजें",
                "feedback_correct": "सही",
                "feedback_incorrect": "गलत",
                "thank_you": "धन्यवाद"
            },
            "Tamil": {
                "upload_photo": "விலங்கு புகைப்படத்தைப் பதிவேற்றவும்",
                "describe_symptoms": "அறிகுறிகளை விவரிக்கவும்",
                "analyze_button": "ஆரோக்கியத்தை ஆராயுங்கள்",
                "chat_with_doctor": "பசுடாக்டருடன் அரட்டையடிக்கவும்",
                "my_cases": "எனது வழக்குகள்",
                "new_analysis": "புதிய பகுப்பாய்வு",
                "confidence": "நம்பிக்கை",
                "diagnosis": "நோய் கண்டறிதல்",
                "precautions": "தற்காப்பு நடவடிக்கைகள்",
                "consult_vet": "கால்நடை மருத்துவரை அணுகவும்",
                "speak_now": "இப்போது பேசுங்கள்",
                "listening": "கேட்கிறது...",
                "processing": "செயலாக்கம்...",
                "no_speech_detected": "பேச்சு கண்டறியப்படவில்லை. மீண்டும் முயற்சிக்கவும்.",
                "animal_detected": "விலங்கு கண்டறியப்பட்டது",
                "follow_up_questions": "பின்தொடர் கேள்விகள்",
                "submit_answers": "பதில்களைச் சமர்ப்பிக்கவும்",
                "feedback_correct": "சரி",
                "feedback_incorrect": "தவறு",
                "thank_you": "நன்றி"
            },
            "Telugu": {
                "upload_photo": "జంతువు ఫోటోను అప్‌లోడ్ చేయండి",
                "describe_symptoms": "లక్షణాలను వివరించండి",
                "analyze_button": "ఆరోగ్య విశ్లేషణ",
                "chat_with_doctor": "పశు డాక్టర్‌తో చాట్ చేయండి",
                "my_cases": "నా కేసులు",
                "new_analysis": "కొత్త విశ్లేషణ",
                "confidence": "నమ్మకం",
                "diagnosis": "వ్యాధి నిర్ధారణ",
                "precautions": "జాగ్రత్తలు",
                "consult_vet": "పశువైద్యుడిని సంప్రదించండి",
                "speak_now": "ఇప్పుడు మాట్లాడండి",
                "listening": "వింటున్నాను...",
                "processing": "ప్రాసెసింగ్...",
                "no_speech_detected": "మాట వినిపించలేదు. మళ్ళీ ప్రయత్నించండి.",
                "animal_detected": "జంతువును గుర్తించాము",
                "follow_up_questions": "తదుపరి ప్రశ్నలు",
                "submit_answers": "సమాధానాలు సమర్పించండి",
                "feedback_correct": "సరియైనది",
                "feedback_incorrect": "తప్పు",
                "thank_you": "ధన్యవాదాలు"
            },
            "Kannada": {
                "upload_photo": "ಪ್ರಾಣಿಗಳ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
                "describe_symptoms": "ಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ",
                "analyze_button": "ಆರೋಗ್ಯ ವಿಶ್ಲೇಷಣೆ",
                "chat_with_doctor": "ಪಶು ಡಾಕ್ಟರ್ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ",
                "my_cases": "ನನ್ನ ಪ್ರಕರಣಗಳು",
                "new_analysis": "ಹೊಸ ವಿಶ್ಲೇಷಣೆ",
                "confidence": "ಆತ್ಮವಿಶ್ವಾಸ",
                "diagnosis": "ರೋಗನಿರ್ಣಯ",
                "precautions": "ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು",
                "consult_vet": "ಪಶುವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ",
                "speak_now": "ಈಗ ಮಾತನಾಡಿ",
                "listening": "ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದೆ...",
                "processing": "ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ...",
                "no_speech_detected": "ಮಾತು ಪತ್ತೆಯಾಗಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
                "animal_detected": "ಪ್ರಾಣಿ ಪತ್ತೆಯಾಗಿದೆ",
                "follow_up_questions": "ಮುಂದಿನ ಪ್ರಶ್ನೆಗಳು",
                "submit_answers": "ಉತ್ತರಗಳನ್ನು ಸಲ್ಲಿಸಿ",
                "feedback_correct": "ಸರಿ",
                "feedback_incorrect": "ತಪ್ಪು",
                "thank_you": "ಧನ್ಯವಾದಗಳು"
            },
            "Malayalam": {
                "upload_photo": "മൃഗത്തിന്റെ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക",
                "describe_symptoms": "ലക്ഷണങ്ങൾ വിവരിക്കുക",
                "analyze_button": "ആരോഗ്യ വിശകലനം",
                "chat_with_doctor": "പശു ഡോക്ടറുമായി ചാറ്റ് ചെയ്യുക",
                "my_cases": "എന്റെ കേസുകൾ",
                "new_analysis": "പുതിയ വിശകലനം",
                "confidence": "വിശ്വാസ്യത",
                "diagnosis": "രോഗനിർണ്ണയം",
                "precautions": "മുൻകരുതലുകൾ",
                "consult_vet": "മൃഗഡോക്ടറെ കാണുക",
                "speak_now": "ഇപ്പോൾ സംസാരിക്കുക",
                "listening": "കേൾക്കുന്നു...",
                "processing": "നടന്നുകൊണ്ടിരിക്കുന്നു...",
                "no_speech_detected": "സംസാരം തിരിച്ചറിഞ്ഞില്ല. വീണ്ടും ശ്രമിക്കുക.",
                "animal_detected": "മൃഗത്തെ കണ്ടെത്തി",
                "follow_up_questions": "തുടർന്നുള്ള ചോദ്യങ്ങൾ",
                "submit_answers": "മറുപടികൾ സമർപ്പിക്കുക",
                "feedback_correct": "ശരി",
                "feedback_incorrect": "തെറ്റ്",
                "thank_you": "നന്ദി"
            },
            "Marathi": {
                "upload_photo": "प्राण्याचे छायाचित्र अपलोड करा",
                "describe_symptoms": "लक्षणांचे वर्णन करा",
                "analyze_button": "आरोग्य विश्लेषण",
                "chat_with_doctor": "पशु डॉक्टरशी संवाद साधा",
                "my_cases": "माझे केसेस",
                "new_analysis": "नवीन विश्लेषण",
                "confidence": "विश्वास",
                "diagnosis": "रोग निदान",
                "precautions": "सावधानता",
                "consult_vet": "पशुवैद्यकाचा सल्ला घ्या",
                "speak_now": "आता बोला",
                "listening": "ऐकत आहे...",
                "processing": "प्रक्रिया सुरू आहे...",
                "no_speech_detected": "आवाज ओळखला नाही. पुन्हा प्रयत्न करा.",
                "animal_detected": "प्राणी ओळखला",
                "follow_up_questions": "पुढील प्रश्न",
                "submit_answers": "उत्तरे सबमिट करा",
                "feedback_correct": "बरोबर",
                "feedback_incorrect": "चुकीचे",
                "thank_you": "धन्यवाद"
            },
            "Bengali": {
                "upload_photo": "প্রাণীর ছবি আপলোড করুন",
                "describe_symptoms": "লক্ষণগুলি বর্ণনা করুন",
                "analyze_button": "স্বাস্থ্য বিশ্লেষণ",
                "chat_with_doctor": "পশু ডাক্তারের সাথে কথা বলুন",
                "my_cases": "আমার কেস",
                "new_analysis": "নতুন বিশ্লেষণ",
                "confidence": "আত্মবিশ্বাস",
                "diagnosis": "রোগ নির্ণয়",
                "precautions": "সতর্কতা",
                "consult_vet": "পশুচিকিৎসকের পরামর্শ নিন",
                "speak_now": "এখন বলুন",
                "listening": "শুনছি...",
                "processing": "প্রক্রিয়াকরণ হচ্ছে...",
                "no_speech_detected": "কথা শনাক্ত করা যায়নি। আবার চেষ্টা করুন।",
                "animal_detected": "প্রাণী শনাক্ত হয়েছে",
                "follow_up_questions": "পরবর্তী প্রশ্ন",
                "submit_answers": "উত্তর জমা দিন",
                "feedback_correct": "সঠিক",
                "feedback_incorrect": "ভুল",
                "thank_you": "ধন্যবাদ"
            },
            "Punjabi": {
                "upload_photo": "ਪਸ਼ੂ ਦੀ ਫੋਟੋ ਅਪਲੋਡ ਕਰੋ",
                "describe_symptoms": "ਲੱਛਣ ਦੱਸੋ",
                "analyze_button": "ਸਿਹਤ ਵਿਸ਼ਲੇਸ਼ਣ",
                "chat_with_doctor": "ਪਸ਼ੂ ਡਾਕਟਰ ਨਾਲ ਗੱਲ ਕਰੋ",
                "my_cases": "ਮੇਰੇ ਕੇਸ",
                "new_analysis": "ਨਵਾਂ ਵਿਸ਼ਲੇਸ਼ਣ",
                "confidence": "ਭਰੋਸਾ",
                "diagnosis": "ਬਿਮਾਰੀ ਦੀ ਪਛਾਣ",
                "precautions": "ਸਾਵਧਾਨੀਆਂ",
                "consult_vet": "ਪਸ਼ੂ ਡਾਕਟਰ ਨਾਲ ਸਲਾਹ ਕਰੋ",
                "speak_now": "ਹੁਣ ਬੋਲੋ",
                "listening": "ਸੁਣ ਰਿਹਾ ਹਾਂ...",
                "processing": "ਪ੍ਰੋਸੈਸਿੰਗ...",
                "no_speech_detected": "ਕੋਈ ਆਵਾਜ਼ ਨਹੀਂ ਮਿਲੀ। ਫਿਰ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
                "animal_detected": "ਪਸ਼ੂ ਦੀ ਪਛਾਣ ਹੋਈ",
                "follow_up_questions": "ਅਗਲੇ ਸਵਾਲ",
                "submit_answers": "ਜਵਾਬ ਜਮ੍ਹਾਂ ਕਰੋ",
                "feedback_correct": "ਸਹੀ",
                "feedback_incorrect": "ਗਲਤ",
                "thank_you": "ਧੰਨਵਾਦ"
            },
            "Gujarati": {
                "upload_photo": "પ્રાણીનો ફોટો અપલોડ કરો",
                "describe_symptoms": "લક્ષણો જણાવો",
                "analyze_button": "સ્વાસ્થ્ય વિશ્લેષણ",
                "chat_with_doctor": "પશુ ડોક્ટર સાથે વાત કરો",
                "my_cases": "મારા કેસો",
                "new_analysis": "નવું વિશ્લેષણ",
                "confidence": "વિશ્વાસ",
                "diagnosis": "રોગ નિદાન",
                "precautions": "સાવચેતીઓ",
                "consult_vet": "પશુચિકિત્સકની સલાહ લો",
                "speak_now": "હવે બોલો",
                "listening": "સાંભળી રહ્યું છે...",
                "processing": "પ્રક્રિયા થઈ રહી છે...",
                "no_speech_detected": "અવાજ ઓળખાયો નથી. ફરી પ્રયાસ કરો.",
                "animal_detected": "પ્રાણી ઓળખાયું",
                "follow_up_questions": "પછીના પ્રશ્નો",
                "submit_answers": "જવાબો સબમિટ કરો",
                "feedback_correct": "સાચું",
                "feedback_incorrect": "ખોટું",
                "thank_you": "આભાર"
            }
        }
        
        return ui_data.get(lang, ui_data["English"])
