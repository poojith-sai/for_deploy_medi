import os
import json
from dotenv import load_dotenv

# Load local environment variables (for development)
load_dotenv()

def setup_gcloud_credentials():
    """
    Configure Google Cloud credentials.
    
    For local development: expects GOOGLE_APPLICATION_CREDENTIALS to contain a file path.
    For deployments (like on Render): expects GOOGLE_CREDENTIALS_JSON with the JSON content.
    """
    # Check if a local file path is provided and exists
    google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds_path and os.path.isfile(google_creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
        print("Using local GOOGLE_APPLICATION_CREDENTIALS file.")
    else:
        # Otherwise, try to load credentials from a JSON string environment variable
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if credentials_json:
            file_path = "./gcloud_key.json"
            try:
                credentials = json.loads(credentials_json)
                with open(file_path, "w") as f:
                    json.dump(credentials, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = file_path
                print("Google credentials file created from GOOGLE_CREDENTIALS_JSON variable.")
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON provided in GOOGLE_CREDENTIALS_JSON") from e
        else:
            raise ValueError("Google Cloud credentials not found. Please set either GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CREDENTIALS_JSON.")

# Set up Google Cloud credentials on startup
setup_gcloud_credentials()

# Continue with the rest of your code
from google.cloud import vision
import google.generativeai as genai

# Configure Gemini API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("Missing GEMINI_API_KEY in environment variables")
genai.configure(api_key=gemini_api_key)

# --- STEP 2: Extract Text using Google Vision API ---
def extract_text_from_image(image_path):
    print("📷 Extracting text from image...")
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"Vision API error: {response.error.message}")
    
    texts = response.text_annotations
    return texts[0].description if texts else ""

# --- STEP 3: Generate Structured JSON using Gemini API ---
def generate_structured_json_from_text(raw_text):
    print("🤖 Sending to Gemini API...")
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")

    prompt = f"""
    You are a highly intelligent medical assistant trained to read prescriptions and infer medical information.
    Given an unstructured prescription text, convert it into a fully filled, detailed JSON object using your knowledge of medicine.

    If any detail (e.g., dosage, duration, side effects, summary) is missing, infer and fill it based on diagnosis, context, and standard practices.

    Prescription Text:
    \"\"\"{raw_text}\"\"\"

    Your task:
    - Fill in all fields in the JSON structure below.
    - Return only valid JSON.

    Expected JSON Format:
    {{
      "patient_name": "string",
      "age": number,
      "gender": "string",
      "prescription_date": "YYYY-MM-DD",
      "doctor_name": "string",
      "diagnosis": "string",
      "disease_info": {{
        "summary": "string",
        "precautions": ["string"]
      }},
      "medications": [
        {{
          "medicine_name": "string",
          "dosage": "string (e.g., 1-0-1)",
          "duration_days": number,
          "total_doses": number,
          "purpose": "string",
          "notes": "string",
          "side_effects": ["string"]
        }}
      ],
      "reminders": {{
        "enabled": true,
        "times": ["string (e.g., 08:00 AM, 02:00 PM, 08:00 PM)"]
      }},
      "additional_notes": "string"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("❌ Gemini API call failed:", e)
        return "{}"

# --- STEP 4: Clean and Save JSON to File ---
def clean_json_output(gemini_output):
    if "```json" in gemini_output:
        gemini_output = gemini_output.split("```json")[1]
    if "```" in gemini_output:
        gemini_output = gemini_output.split("```")[0]
    return gemini_output.strip()

def save_json_to_file(json_str, filename="output.json"):
    print("💾 Saving output...")
    json_str = clean_json_output(json_str)
    try:
        parsed = json.loads(json_str)
        with open(filename, "w") as f:
            json.dump(parsed, f, indent=2)
        print(f"✅ JSON saved to {filename}")
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON. Here's what Gemini returned:")
        print("```json")
        print(json_str)
        print("```")
        print("Error:", e)

# --- STEP 5: Pipeline Runner ---
def process_prescription(image_path):
    extracted_text = extract_text_from_image(image_path)
    generated_json = generate_structured_json_from_text(extracted_text)
    save_json_to_file(generated_json)

# --- Main Execution ---
if __name__ == "__main__":
    image_path = "image.png"  # Replace with your image file path
    process_prescription(image_path)
