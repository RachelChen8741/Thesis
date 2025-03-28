import google.generativeai as genai
import os
import getpass
import psycopg2
from readability import Readability
import glob

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
            CREATE TABLE IF NOT EXISTS summaries (
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
            INSERT INTO summaries (patient_id, summary, flesch_kincaid_grade, flesch_kincaid_score, flesch_reading_ease, smog_score, smog_grade)
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
        summary = summarize_with_gemini(text_data)
        readability_scores = compute_readability(summary)

        save_summary_to_db(conn, patient_id, summary, readability_scores)

        print(f"Summary saved for Patient {patient_id}\n")

    conn.close()
    print("\nAll patients processed successfully!")

# Run the script
if __name__ == "__main__":
    process_all_patients()