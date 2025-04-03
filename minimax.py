import google.generativeai as genai
import os
import getpass
import psycopg2
from readability import Readability
import glob
import requests

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="data",
            user="postgres",
            password="NeonWaterfallz8741",
            host="127.0.0.1",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print("Database connection error:", e)
        return None


def create_summary_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS minimax_summaries (
                patient_id TEXT PRIMARY KEY,
                summary TEXT,
                flesch_kincaid_grade FLOAT,
                flesch_kincaid_score FlOAT,
                flesch_reading_ease TEXT,
                smog_score FLOAT,
                smog_grade FLOAT
            );
        """)
        conn.commit()
    except psycopg2.Error as e:
        print("Error creating table:", e)

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
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were a sixth grader. Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.
    
    {data}
    
    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.
    """
    
    payload = {
        "model": "MiniMax-Text-01",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    response = requests.post(MINIMAX_API_URL, headers=headers, json=payload)
    
    try:
        response_json = response.json()
        # print(f"API Response: {response.status_code} - {response_json}")
        
        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0].get("message", {}).get("content", "")
        else:
            print("Unexpected API response structure:", response_json)
            return "Error: Unexpected API response format."
    
    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON response:", response.text)
        return "Error: API returned non-JSON response."


def compute_readability(text):
    r = Readability(text)
    try:
        return {
            "flesch_kincaid_grade": r.flesch_kincaid().grade_level,
            "flesch_kincaid_score": r.flesch().score,
            "flesch_reading_ease": r.flesch().ease,
            "smog_score": r.smog().score,
            "smog_grade": r.smog().grade_level
        }
    except Exception as e:
        print("Readability error:", e)
        return {"flesch_kincaid_grade": None, "flesch_kincaid_score": None, "flesch_reading_ease": None, "smog_score": None, "smog_grade": None}
    
def save_summary_to_db(conn, patient_id, summary, readability_scores):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO minimax_summaries (patient_id, summary, flesch_kincaid_grade, flesch_kincaid_score, flesch_reading_ease, smog_score, smog_grade)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id) DO UPDATE 
            SET summary = EXCLUDED.summary,
                flesch_kincaid_grade = EXCLUDED.flesch_kincaid_grade,
                flesch_kincaid_score = EXCLUDED.flesch_kincaid_score,
                flesch_reading_ease = EXCLUDED.flesch_reading_ease,
                smog_score = EXCLUDED.smog_score,
                smog_grade = EXCLUDED.smog_grade;
        """, (patient_id, summary, readability_scores["flesch_kincaid_grade"], readability_scores["flesch_kincaid_score"],
              readability_scores["flesch_reading_ease"], readability_scores["smog_score"], 
              readability_scores["smog_grade"]))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error for patient {patient_id}:", e)

def process_all_patients():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    create_summary_table(conn)  

    report_files = glob.glob("patient_reports/patient_*.txt")  

    for file_path in report_files:
        patient_id = os.path.basename(file_path).split("_")[1].split(".")[0]  # Extract patient ID from filename
        
        print(f"Processing Patient {patient_id}...")

        text_data = load_text_report(file_path)
        summary = summarize_with_minimax(text_data)
        readability_scores = compute_readability(summary)

        save_summary_to_db(conn, patient_id, summary, readability_scores)

        print(f"Summary saved for Patient {patient_id}\n")

    conn.close()
    print("\nAll patients processed successfully!")

# Run the script
if __name__ == "__main__":
    process_all_patients()