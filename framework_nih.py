import google.generativeai as genai
import os
import getpass
import sys
from readability import Readability
import nltk
import requests
import psycopg2
import argparse
from openai import OpenAI, APIError
import anthropic

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="1k_data",
            user="postgres",
            password="NeonWaterfallz8741",
            host="127.0.0.1",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print("Database connection error:", e)
        return None
    
def load_text_report(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    
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
        conn.rollback()
        return None


def create_summary_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                patient_id TEXT,
                model TEXT,
                summary TEXT,
                flesch_kincaid_grade FLOAT,
                flesch_kincaid_score FLOAT,
                flesch_reading_ease TEXT,
                smog_score FLOAT,
                smog_grade FLOAT,
                gunning_fog_score FLOAT,
                gunning_fog_grade FLOAT,
                PRIMARY KEY (patient_id, model)
            );
        """)
        conn.commit()
    except psycopg2.Error as e:
        print("Error creating table:", e)

def summary_exists(conn, patient_id, model):
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM summaries WHERE patient_id = %s AND model = %s LIMIT 1;", (patient_id, model))
        return cur.fetchone() is not None
    except psycopg2.Error as e:
        print(f"Error checking summary existence for {patient_id} ({model}):", e)
        return False


def summarize_with_gemini(model, data):
    prompt = f"""
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an eighth grader. Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.
    
    {data}
    
    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.
    """
    
    response = model.generate_content(prompt, generation_config={"temperature": 0.1})
    return response.text


MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"

def summarize_with_minimax(MINIMAX_API_KEY, data):
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
        "temperature": 0.1
    }
    
    response = requests.post(MINIMAX_API_URL, headers=headers, json=payload)
    
    try:
        response_json = response.json()
        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0].get("message", {}).get("content", "")
        else:
            print("Unexpected API response structure:", response_json)
            return "Error: Unexpected API response format."
    
    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON response:", response.text)
        return "Error: API returned non-JSON response."

def summarize_with_gpt(client, data):
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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()

    except APIError as e:
        if "maximum context length" in str(e) or "tokens exceeded" in str(e):
            print("Error: The input is too long for GPT. Try using a different model.")
        else:
            print(f"Unexpected API error: {e}")
        return None

def summarize_with_claude(client, data):
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
    try: 
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=64000, 
            stream=True  
        )
        
        summary = ""  
        for event in response:
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                summary += event.delta.text  
        return summary.strip()
    except APIError as e:
        if "maximum context length" in str(e) or "tokens exceeded" in str(e):
            print("Error: The input is too long for Claude. Try using a different model.")
        else:
            print(f"Unexpected API error: {e}")
        return None
    
def summarize_with_deepseek(client,data):
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
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except APIError as e:
        if "maximum context length" in str(e) or "tokens exceeded" in str(e):
            print("Error: The input is too long for Deepseek. Try using a different model.")
        else:
            print(f"Unexpected API error: {e}")
        return None


def compute_readability(text):
    try:
        r = Readability(text)
        return {
            "flesch_kincaid_grade": r.flesch_kincaid().grade_level,
            "flesch_kincaid_score": r.flesch().score,
            "flesch_reading_ease": r.flesch().ease,
            "smog_score": r.smog(all_sentences=True).score,
            "smog_grade": r.smog(all_sentences=True).grade_level,
            "gunning_fog_score": r.gunning_fog().score,
            "gunning_fog_grade": r.gunning_fog().grade_level
        }
    except Exception as e:
        print(f"Readability error: {e}")
        return { "flesch_kincaid_grade": r.flesch_kincaid().grade_level, "flesch_kincaid_score": r.flesch().score, "flesch_reading_ease": r.flesch().ease, "smog_score": None, "smog_grade": None, "gunning_fog_score": r.gunning_fog().score, "gunning_fog_grade": r.gunning_fog().grade_level}

    
def save_summary_to_db(conn, patient_id, model, summary, readability_scores):
    try:
        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO summaries (
                patient_id, model, summary, flesch_kincaid_grade, 
                flesch_kincaid_score, flesch_reading_ease, 
                smog_score, smog_grade, gunning_fog_score, gunning_fog_grade
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id, model) DO UPDATE
            SET summary = EXCLUDED.summary,
                flesch_kincaid_grade = EXCLUDED.flesch_kincaid_grade,
                flesch_kincaid_score = EXCLUDED.flesch_kincaid_score,
                flesch_reading_ease = EXCLUDED.flesch_reading_ease,
                smog_score = EXCLUDED.smog_score,
                smog_grade = EXCLUDED.smog_grade,
                gunning_fog_score = EXCLUDED.gunning_fog_score,
                gunning_fog_grade = EXCLUDED.gunning_fog_grade;
        """, (
            patient_id, model, summary,
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
        print(f"Database error for patient {patient_id} (model={model}):", e)


def process_all_patients(model_choice):
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    create_summary_table(conn)  
    
    patient_ids = order_by_size(conn)

    for patient_id in patient_ids:
        if summary_exists(conn, patient_id, model_choice):
            print(f"Skipping Patient {patient_id} — summary already exists for model '{model_choice}'.")
            continue
        text_data = fetch_patient_health_record(conn, patient_id)
        if not text_data:
            print(f"Skipping Patient {patient_id} due to missing data.")
            continue
        if model_choice == "gemini":
            if "GEMINI_API_KEY" not in os.environ:
                os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-2.0-flash')
            summary = summarize_with_gemini(model, text_data)
        elif model_choice == "minimax":
            if "MINIMAX_API_KEY" not in os.environ:
                os.environ["MINIMAX_API_KEY"] = getpass.getpass("Enter your Minimax AI API key: ")
                MINIMAX_API_KEY = os.environ["MINIMAX_API_KEY"]
            summary = summarize_with_minimax(MINIMAX_API_KEY, text_data)
        elif model_choice == "chatgpt":
            if "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OPEN AI API key: ")
            client = OpenAI()
            summary = summarize_with_gpt(client, text_data)
        elif model_choice == "claude":
            if "CLAUDE_API_KEY" not in os.environ:
                os.environ["CLAUDE_API_KEY"] = getpass.getpass("Enter your CLAUDE API key: ")
            CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            summary = summarize_with_claude(client, text_data)
        elif model_choice == "deepseek":
            if "DEEPSEEK_API_KEY" not in os.environ:
                os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DEEPSEEK API key: ")
            DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            summary = summarize_with_deepseek(client, text_data)

        else:
            print("Error: Invalid model choice.")
            return
        print(f"Processing Patient {patient_id}...")

        readability_scores = compute_readability(summary)

        save_summary_to_db(conn, patient_id, model_choice, summary, readability_scores)

        print(f"Summary saved for Patient {patient_id}\n")

    conn.close()
    print("\nAll patients processed successfully!")

    

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Please input which LLM you would like to use.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", action="store_true", help="put -g in command line to use Gemini")
    group.add_argument("-m", action="store_true", help="put -m in command line to use MiniMax")
    group.add_argument("-c", action="store_true", help="put -c in command line to use ChatGPT")
    group.add_argument("-a", action="store_true", help="put -a in command line to use Claude")
    group.add_argument("-d", action="store_true", help="put -d in command line to use Deepseek")


    args = parser.parse_args()

    model_choice = "gemini" if args.g else "minimax" if args.m else "chatgpt" if args.c else "claude" if args.a else "deepseek" if args.d else None
    
    process_all_patients(model_choice)
