from openai import OpenAI
import os
import psycopg2
import getpass
from readability import Readability
import glob

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OPEN AI API key: ")

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

client = OpenAI()
    
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
                smog_grade FLOAT,
                gunning_fog_score FLOAT,
                gunning_fog_grade FLOAT
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

def summarize_with_gpt(data):
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
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()

def compute_readability(text):
    r = Readability(text)
    try:
        return {
            "flesch_kincaid_grade": r.flesch_kincaid().grade_level,
            "flesch_kincaid_score": r.flesch().score,
            "flesch_reading_ease": r.flesch().ease,
            "smog_score": r.smog().score,
            "smog_grade": r.smog().grade_level,
            "gunning_fog_score": r.gunning_fog().score,
            "gunning_fog_grade": r.gunning_fog().grade_level
        }
    except Exception as e:
        print("Readability error:", e)
        return { "flesch_kincaid_grade": r.flesch_kincaid().grade_level, "flesch_kincaid_score": r.flesch().score, "flesch_reading_ease": r.flesch().ease, "smog_score": None, "smog_grade": None, "gunning_fog_score": r.gunning_fog().score, "gunning_fog_grade": r.gunning_fog().grade_level}
    
def save_summary_to_db(conn, patient_id, summary, readability_scores):
    try:
        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gpt_summaries (
                patient_id, summary, flesch_kincaid_grade, 
                flesch_kincaid_score, flesch_reading_ease, 
                smog_score, smog_grade, gunning_fog_score, gunning_fog_grade
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id) DO UPDATE
            SET summary = EXCLUDED.summary,
                flesch_kincaid_grade = EXCLUDED.flesch_kincaid_grade,
                flesch_kincaid_score = EXCLUDED.flesch_kincaid_score,
                flesch_reading_ease = EXCLUDED.flesch_reading_ease,
                smog_score = EXCLUDED.smog_score,
                smog_grade = EXCLUDED.smog_grade,
                gunning_fog_score = EXCLUDED.gunning_fog_score,
                gunning_fog_grade = EXCLUDED.gunning_fog_grade;
        """, (
            patient_id, summary,
            safe_float(readability_scores["flesch_kincaid_grade"]),
            safe_float(readability_scores["flesch_kincaid_score"]),
            readability_scores["flesch_reading_ease"],
            safe_float(readability_scores["smog_score"]),
            safe_float(readability_scores["smog_grade"]),
            safe_float(readability_scores["gunning_fog_score"]),
            safe_float(readability_scores["gunning_fog_grade"])
        ))
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

        summary = summarize_with_gpt(text_data)
        readability_scores = compute_readability(summary)

        save_summary_to_db(conn, patient_id, summary, readability_scores)

        print(f"Summary saved for Patient {patient_id}\n")

    conn.close()
    print("\nAll patients processed successfully!")

if __name__ == "__main__":
    process_all_patients()