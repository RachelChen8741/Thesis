import os
import getpass
import requests
from readability import Readability

def load_text_report(file_path):
    with open(file_path, 'r') as f:
        return f.read()

if "MINIMAX_API_KEY" not in os.environ:
    os.environ["MINIMAX_API_KEY"] = getpass.getpass("Enter your Minimax AI API key: ")

MINIMAX_API_KEY = os.environ["MINIMAX_API_KEY"]
MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"

def summarize_with_minimax(data):
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an eighth grader. Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.
    
    {data}
    
    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.
    """
    
    payload = {
        "model": "MiniMax-Text-01",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    response = requests.post(MINIMAX_API_URL, headers=headers, json=payload)
    
    try:
        response_json = response.json()
        print(f"API Response: {response.status_code} - {response_json}")
        
        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0].get("message", {}).get("content", "")
        else:
            print("Unexpected API response structure:", response_json)
            return "Error: Unexpected API response format."
    
    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON response:", response.text)
        return "Error: API returned non-JSON response."


def compute_readability(text):
    try:
        r = Readability(text)
        return {
            "flesch_kincaid_grade": r.flesch_kincaid().grade_level,
            "flesch_kincaid_score": r.flesch().score,
            "flesch_reading_ease": r.flesch().ease,
            "smog_score": r.smog().score,
            "smog_grade": r.smog().grade_level
        }
    except Exception as e:
        print(f"Readability error: {e}")
        return { "flesch_kincaid_grade": None, "flesch_kincaid_score": None, "flesch_reading_ease": None, "smog_score": None, "smog_grade": None }

def process_patient(patient_id):
    file_path = f"patient_reports/patient_{patient_id}.txt"
    
    print(f"Processing Patient {patient_id}...")

    text_data = load_text_report(file_path)
    if not text_data:
        print(f"No data found for Patient {patient_id}. Skipping.")
        return

    summary = summarize_with_minimax(text_data)
    readability_scores = compute_readability(summary)

    print(f"**Summary for {patient_id}:**\n{summary}")
    print(f"**Readability Scores:**\n{readability_scores}")

    print(f"Patient {patient_id} processed successfully!")

if __name__ == "__main__":
    patient_id = input("Please enter the Patient ID: ").strip()
    process_patient(patient_id)
