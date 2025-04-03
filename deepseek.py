from openai import OpenAI
import os
import psycopg2
import getpass
from readability import Readability
import glob
from openai import OpenAI, APIError

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
            CREATE TABLE IF NOT EXISTS deepseek_summaries (
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
    
def order_by_size(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT *, pg_column_size(r.*) AS row_size FROM records r ORDER BY row_size ASC;")
        patient_ids = [row[0] for row in cur.fetchall()]
        return patient_ids
    except psycopg2.Error as e:
        print("Error fetching patient IDs:", e)
        return []

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
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an sixth grader. 
    Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.

    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.

    Here is the patient's health record:
    {data}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except APIError as e:
        if "maximum context length" in str(e) or "tokens exceeded" in str(e):
            print("Error: The input is too long for Deepseek. Try using a different model.")
        else:
            print(f"Unexpected API error: {e}")
        return None

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
        return { "flesch_kincaid_grade": r.flesch_kincaid().grade_level, "flesch_kincaid_score": r.flesch().score, "flesch_reading_ease": r.flesch().ease, "smog_score": None, "smog_grade": None }
    
def save_summary_to_db(conn, patient_id, summary, readability_scores):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO deepseek_summaries (patient_id, summary, flesch_kincaid_grade, flesch_kincaid_score, flesch_reading_ease, smog_score, smog_grade)
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
    
    patient_ids = order_by_size(conn)

    for patient_id in patient_ids:
        print(f"Processing Patient {patient_id}...")

        text_data = fetch_patient_health_record(conn, patient_id)
        if not text_data:
            print(f"Skipping Patient {patient_id} due to missing data.")
            continue

        summary = summarize_with_deepseek(text_data)
        readability_scores = compute_readability(summary)

        save_summary_to_db(conn, patient_id, summary, readability_scores)

        print(f"Summary saved for Patient {patient_id}\n")

    conn.close()
    print("\nAll patients processed successfully!")

if __name__ == "__main__":
    process_all_patients()