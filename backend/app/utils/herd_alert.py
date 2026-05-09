CONTAGIOUS_DISEASES = [
    "foot_and_mouth", "lumpy_skin_disease",
    "ppr", "hemorrhagic_septicemia", "blackquarter"
]

HERD_ALERT_MESSAGES = {
    "foot_and_mouth": {
        "english": "ISOLATE immediately. FMD spreads through air, contact, and contaminated water. Check ALL hooves and mouths in herd.",
        "hindi": "तुरंत अलग करें। FMD हवा, संपर्क और दूषित पानी से फैलता है। झुंड में सभी खुरों और मुंहों की जांच करें।",
        "tamil": "உடனடியாக தனிமைப்படுத்தவும். FMD காற்று, தொடர்பு மற்றும் அசுத்தமான நீர் மூலம் பரவுகிறது.",
        "telugu": "వెంటనే వేరు చేయండి. FMD గాలి, సంపర్కం మరియు కలుషిత నీటి ద్వారా వ్యాపిస్తుంది.",
        "kannada": "ತಕ್ಷಣ ಪ್ರತ್ಯೇಕಿಸಿ. FMD ಗಾಳಿ, ಸಂಪರ್ಕ ಮತ್ತು ಕಲುಷಿತ ನೀರಿನ ಮೂಲಕ ಹರಡುತ್ತದೆ.",
        "malayalam": "ഉടനടി മാറ്റി പാർപ്പിക്കുക. എഫ്.എം.ഡി വായുവിലൂടെയും സമ്പർക്കത്തിലൂടെയും പകരുന്നു.",
        "marathi": "त्वरीत वेगळे करा. FMD हवा, संपर्क आणि दूषित पाण्याद्वारे पसरतो.",
        "bengali": "অবিলম্বে আলাদা করুন। FMD বাতাস, সংস্পর্শ এবং দূষিত জলের মাধ্যমে ছড়ায়।",
        "punjabi": "ਤੁਰੰਤ ਵੱਖ ਕਰੋ। FMD ਹਵਾ, ਸੰਪਰਕ ਅਤੇ ਦੂਸ਼ਿਤ ਪਾਣੀ ਰਾਹੀਂ ਫੈਲਦਾ ਹੈ।",
        "gujarati": "તરત જ અલગ કરો. FMD હવા, સંપર્ક અને દૂષિત પાણી દ્વારા ફેલાય છે."
    },
    "lumpy_skin_disease": {
        "english": "ISOLATE immediately. LSD spreads via biting insects (flies, mosquitoes, ticks). Move animal to a vector-free area.",
        "hindi": "तुरंत अलग करें। LSD काटने वाले कीड़ों (मक्खियों, मच्छरों) के माध्यम से फैलता है।",
        "tamil": "உடனடியாக தனிமைப்படுத்தவும். LSD பூச்சிகள் மூலம் பரவுகிறது.",
        "telugu": "వెంటనే వేరు చేయండి. LSD దోమలు మరియు ఈగలు ద్వారా వ్యాపిస్తుంది.",
        "kannada": "ತಕ್ಷಣ ಪ್ರತ್ಯೇಕಿಸಿ. LSD ಕೀಟಗಳ ಮೂಲಕ ಹರಡುತ್ತದೆ.",
        "malayalam": "ഉടനടി മാറ്റി പാർപ്പിക്കുക. എൽഎസ്ഡി പ്രാണികൾ വഴി പകരുന്നു.",
        "marathi": "त्वरीत वेगळे करा. LSD कीटकांद्वारे पसरतो.",
        "bengali": "অবিলম্বে আলাদা করুন। LSD পতঙ্গবাহিত রোগ।",
        "punjabi": "ਤੁਰੰਤ ਵੱਖ ਕਰੋ। LSD ਕੀੜਿਆਂ ਰਾਹੀਂ ਫੈਲਦਾ ਹੈ।",
        "gujarati": "તરત જ અલગ કરો. LSD જીવજંતુઓ દ્વારા ફેલાય છે."
    },
    "ppr": {
        "english": "ISOLATE immediately. PPR affects only goats and sheep. Separate ALL small ruminants from infected animal.",
        "hindi": "तुरंत अलग करें। PPR केवल बकरियों और भेड़ों को प्रभावित करता है। सभी छोटे जानवरों को संक्रमित जानवर से अलग करें।",
        "tamil": "உடனடியாக தனிமைப்படுத்தவும். PPR ஆடுகள் மற்றும் செம்மறி ஆடுகளை மட்டுமே பாதிக்கிறது.",
        "telugu": "వెంటనే వేరు చేయండి. PPR కేవలం గొర్రెలు మరియు మేకలకు మాత్రమే వస్తుంది.",
        "kannada": "ತಕ್ಷಣ ಪ್ರತ್ಯೇಕಿಸಿ. PPR ಕೇವಲ ಕುರಿ ಮತ್ತು ಮೇಕೆಗಳಿಗೆ ಹರಡುತ್ತದೆ.",
        "malayalam": "ഉടനടി മാറ്റി പാർപ്പിക്കുക. പിപിആർ ആടുകളെയും ചെമ്മരിയാടുകളെയും മാത്രമേ ബാധിക്കൂ.",
        "marathi": "त्वरीत वेगळे करा. PPR फक्त शेळ्या आणि मेंढ्यांवर परिणाम करतो.",
        "bengali": "অবিলম্বে আলাদা করুন। PPR শুধুমাত্র ছাগল এবং ভেড়াকে আক্রান্ত করে।",
        "punjabi": "ਤੁਰੰਤ ਵੱਖ ਕਰੋ। PPR ਸਿਰਫ ਬੱਕਰੀਆਂ ਅਤੇ ਭੇਡਾਂ ਨੂੰ ਪ੍ਰਭਾਵਿਤ ਕਰਦਾ ਹੈ।",
        "gujarati": "તરત જ અલગ કરો. PPR ફક્ત બકરીઓ અને ઘેટાંને અસર કરે છે."
    },
    "hemorrhagic_septicemia": {
        "english": "ISOLATE immediately. Highly contagious bacterial disease. Can cause sudden death in the herd.",
        "hindi": "तुरंत अलग करें। अत्यधिक संक्रामक जीवाणु रोग। झुंड में अचानक मृत्यु का कारण बन सकता है।",
        "tamil": "உடனடியாக தனிமைப்படுத்தவும். மிகவும் தொற்றும் பாக்டீரியா நோய்.",
        "telugu": "వెంటనే వేరు చేయండి. ఇది అత్యంత వేగంగా వ్యాపించే వ్యాధి.",
        "kannada": "ತಕ್ಷಣ ಪ್ರತ್ಯೇಕಿಸಿ. ಇದು ಅತ್ಯಂತ ವೇಗವಾಗಿ ಹರಡುವ ಬ್ಯಾಕ್ಟೀರಿಯಾ ರೋಗ.",
        "malayalam": "ഉടനടി മാറ്റി പാർപ്പിക്കുക. വേഗത്തിൽ പകരുന്ന ബാക്ടീരിയ രോഗം.",
        "marathi": "त्वरीत वेगळे करा. अत्यंत संक्रामक जीवाणूजन्य रोग.",
        "bengali": "অবিলম্বে আলাদা করুন। অত্যন্ত সংক্রামক ব্যাকটেরিয়া ঘটিত রোগ।",
        "punjabi": "ਤੁਰੰਤ ਵੱਖ ਕਰੋ। ਬਹੁਤ ਜ਼ਿਆਦਾ ਛੂਤ ਵਾਲੀ ਬਿਮਾਰੀ।",
        "gujarati": "તરત જ અલગ કરો. અત્યંત ચેપી બેક્ટેરિયલ રોગ."
    },
    "blackquarter": {
        "english": "ISOLATE immediately. Soil-borne spores. Do NOT move the animal across shared grazing areas.",
        "hindi": "तुरंत अलग करें। मिट्टी से पैदा होने वाले बीजाणु। जानवर को साझा चराई क्षेत्रों में न ले जाएं।",
        "tamil": "உடனடியாக தனிமைப்படுத்தவும். மண்ணிலிருந்து பரவும் நோய்.",
        "telugu": "వెంటనే వేరు చేయండి. ఇది నేల ద్వారా వ్యాపించే వ్యాధి.",
        "kannada": "ತಕ್ಷಣ ಪ್ರತ್ಯೇಕಿಸಿ. ಮಣ್ಣಿನಿಂದ ಹರಡುವ ರೋಗ.",
        "malayalam": "ഉടനടി മാറ്റി പാർപ്പിക്കുക. മണ്ണിലൂടെ പകരുന്ന രോഗം.",
        "marathi": "त्वरीत वेगळे करा. मातीतून पसरणारे रोग.",
        "bengali": "অবিলম্বে আলাদা করুন। মাটিবাহিত রোগ।",
        "punjabi": "ਤੁਰੰਤ ਵੱਖ ਕਰੋ। ਮਿੱਟੀ ਰਾਹੀਂ ਫੈਲਣ ਵਾਲੀ ਬਿਮਾਰੀ।",
        "gujarati": "તરત જ અલગ કરો. માટીથી ફેલાતો રોગ."
    }
}

def check_herd_alert(disease_label: str, language: str) -> dict:
    # Normalize label
    disease = disease_label.lower().replace(" ", "_")
    lang = language.lower()
    
    if disease in CONTAGIOUS_DISEASES:
        return {
            "is_contagious": True,
            "alert_message": HERD_ALERT_MESSAGES.get(disease, {}).get(lang, HERD_ALERT_MESSAGES[disease]["english"]),
            "isolation_required": True,
            "report_to_authority": True,
            "authority_number": "1962"
        }
    return {"is_contagious": False}
