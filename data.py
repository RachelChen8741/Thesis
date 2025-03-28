import psycopg2
from datetime import datetime, date
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection
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

def format_value(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value) if value is not None else "N/A"

def fetch_table_data(conn, table_name, patient_id, columns):
    try:
        cur = conn.cursor()
        query = f"SELECT {', '.join(columns)} FROM {table_name} WHERE patient = %s" # takes all the columns from each table for that patienti
        cur.execute(query, (patient_id,))
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error fetching {table_name}:", e)
        return []
    finally:
        cur.close()

# Fetch all patient IDs
def get_all_patient_ids(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM patients")
        return [row[0] for row in cur.fetchall()]
    except psycopg2.Error as e:
        print("Error fetching patient IDs:", e)
        return []
    finally:
        cur.close()

# Generate a text report for a single patient
def generate_text_report(conn, patient_id):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first, last, birthdate, gender
            FROM patients
            WHERE id = %s
        """, (patient_id,))
        patient = cur.fetchone()

        if not patient:
            return f"Patient {patient_id} not found"

        tables = {
            "Encounters": ["start", "stop", "description"],
            "Conditions": ["description"],
            "Medications": ["description", "start", "stop"],
            "Procedures": ["description", "start", "stop"],
            "Observations": ["description", "value", "units"],
            "Allergies": ["description", "reaction1", "severity1"],
            "Immunizations": ["description", "date"],
            "Devices": ["description", "start", "stop"],
            "Careplans": ["description", "start", "stop"],
            "Imaging": ["bodysitedescription", "modalitydescription", "date"],
            "Supplies": ["description", "quantity", "date"]
        }

        report = []
        report.append(f"PATIENT RECORD\n{'='*40}")
        report.append(f"Name: {patient[1]} {patient[2]}")
        report.append(f"ID: {patient[0]}")
        report.append(f"Birthdate: {format_value(patient[3])}")
        report.append(f"Gender: {patient[4]}\n")

        for table_name, columns in tables.items():
            data = fetch_table_data(conn, table_name.lower(), patient_id, columns)
            if data:
                report.append(f"\n{table_name.upper()}\n{'-'*40}")
                for row in data:
                    items = [f"{col}: {format_value(val)}" for col, val in zip(columns, row)]
                    report.append(" • " + " | ".join(items))

        return "\n".join(report)

    except psycopg2.Error as e:
        return f"Database error for patient {patient_id}: {str(e)}"
    
def create_report_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS records (
                patient_id TEXT PRIMARY KEY,
                records TEXT
            );
        """)
        conn.commit()
    except psycopg2.Error as e:
        print("Error creating table:", e)

def save_patient_reports(conn, patient_id, records):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO records (patient_id, records)
            VALUES (%s, %s)
            ON CONFLICT (patient_id) DO UPDATE 
            SET records = EXCLUDED.records;
        """, (patient_id, records))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error for patient {patient_id}:", e)

# Generate reports for ALL patients
def generate_reports_for_all_patients():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return
    
    create_report_table(conn) 

    patient_ids = get_all_patient_ids(conn)

    if not patient_ids:
        print("No patients found.")
        return

    for patient_id in patient_ids:
        records = generate_text_report(conn, patient_id)
        save_patient_reports(conn, patient_id, records)

    conn.close()
    print("\nAll reports generated successfully.")

if __name__ == "__main__":
    generate_reports_for_all_patients()
