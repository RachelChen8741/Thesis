import google.generativeai as genai
import os
import getpass
import sys
from readability import Readability
import nltk

def load_text_report(file_path):
    with open(file_path, 'r') as f:
        return f.read()

if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

def summarize_with_gemini(data):
    prompt = f"""
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an eighth grader. Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.:
      
       {data}
      
       Provide an explanation that includes:
       - Their medical conditions.
       - Their current medications and what they do.
       - Any notable observations (e.g., lab results, vitals) and what it means.
    """
    response = model.generate_content(prompt)
    return response.text

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

    summary = summarize_with_gemini(text_data)
    readability_scores = compute_readability(summary)

    print(f"**Summary for {patient_id}:**\n{summary}")
    print(f"**Readability Scores:**\n{readability_scores}")

    print(f"Patient {patient_id} processed successfully!")

if __name__ == "__main__":
    patient_id = input("Please enter the Patient ID: ").strip()
    process_patient(patient_id)