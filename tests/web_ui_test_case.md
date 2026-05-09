# 🧪 PashuDoctor Web UI Test Case

This file provides a standardized test case to verify the modern AI consultation interface.

## **Test Scenario: Lumpy Skin Disease (LSD) Detection**

### **1. Test Assets**
- **Image**: [Download/View Test Image](file:///C:/Users/mahip/.gemini/antigravity/brain/9ec16d18-5d46-4fb9-bff6-70a8632abe7d/test_cow_lumpy_skin_1778307905301.png)
- **Description**: "My cow has developed small, hard lumps and nodules all over its neck and back. It has a slight fever and is eating less than usual."

### **2. Expected Result**
- **Detected Animal**: Cow (Confidence > 90%)
- **Primary Diagnosis**: Lumpy Skin Disease
- **Severity**: High / Urgent
- **Confidence**: > 80%

---

## **📋 Step-by-Step Test Procedure**

1.  **Launch Interface**: Ensure Streamlit is running at `http://localhost:8501`.
2.  **Upload Image**: Click the attachment icon (📎) in the chat bar and select the generated test image.
3.  **Enter Description**: Type the description provided above into the chat input and press Enter.
4.  **Observe Indicators**:
    - Verify that "Analyzing image..." and "Searching similar cases..." status bars appear.
    - Verify that only ONE analysis request is sent (no loops).
5.  **Verify Results Panel**:
    - Check the **Right Column** for the "Identified Animal" card.
    - Confirm the "Disease Prediction" card shows **Lumpy Skin Disease**.
    - Expand "Clinical Explainability" to see matched symptoms (e.g., Skin Nodules).

---

## **🛠 Troubleshooting**
- **415 Error**: Ensure the image is a valid PNG/JPG (the generated image is PNG).
- **No Results**: Check the backend terminal for Gemini API errors or database connection issues.
- **Multiple Analysis**: Ensure you are using the latest version of `home.py` with the trigger-guard logic.

![Test Image](file:///C:/Users/mahip/.gemini/antigravity/brain/9ec16d18-5d46-4fb9-bff6-70a8632abe7d/test_cow_lumpy_skin_1778307905301.png)
