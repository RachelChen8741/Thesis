import psycopg2
from datetime import datetime, date
from dotenv import load_dotenv
import os
from openai import OpenAI
import getpass
from readability import Readability

if "DEEPSEEK_API_KEY" not in os.environ:
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DEEPSEEK API key: ")

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

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
            CREATE TABLE IF NOT EXISTS gpt_summaries (
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

def fetch_patient_health_record(conn, patient_id):
    """Fetch health records for a specific patient from the database."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT records FROM records WHERE patient_id = %s;", (patient_id,))
        record = cur.fetchone()
        if record:
            return record[0]
        else:
            print("No health record found for this patient.")
            return None
    except psycopg2.Error as e:
        print("Error fetching patient record:", e)
        return None

def summarize_with_deepseek(data):
    prompt = f"""
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an eighth grader. 
    Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.

    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.

    Here is the patient's health record:
    {data}
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

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
        return { "flesch_kincaid_grade": r.flesch_kincaid().grade_level, "flesch_kincaid_score": r.flesch().score, "flesch_reading_ease": r.flesch().ease, "smog_score": None, "smog_grade": None }

def process_patient(patient_id):
    file_path = f"patient_reports/patient_{patient_id}.txt"
    
    print(f"Processing Patient {patient_id}...")

    text_data = load_text_report(file_path)
    if not text_data:
        print(f"No data found for Patient {patient_id}. Skipping.")
        return

    summary = summarize_with_gpt(text_data)
    readability_scores = compute_readability(summary)

    print(f"**Readability Scores:**\n{readability_scores}")

    print(f"Patient {patient_id} processed successfully!")

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        patient_id = input("Enter the patient ID: ").strip()
        health_record = fetch_patient_health_record(conn, patient_id)

        if health_record:
            print("\nGenerating summary...\n")
            summary = summarize_with_deepseek(health_record)
            print("\nPatient Summary:\n")
            print(summary)
            scores = compute_readability(summary)
            print(scores)
        
        conn.close()