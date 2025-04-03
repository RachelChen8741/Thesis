import google.generativeai as genai
import os
import getpass
import sys
from readability import Readability
import nltk
import requests
import argparse
from openai import OpenAI, APIError
import anthropic


def load_text_report(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None


def summarize_with_gemini(model, data):
    prompt = f"""
    Summarize and explain this patient's health record to them in simple language to help them better understand their own health as if they were an eighth grader. Avoid using abbreviations if possible. There is no need to include non-relevant medical information such as their age, birthday, or sex.
    
    {data}
    
    Provide an explanation that includes:
    - Their medical conditions.
    - Their current medications and what they do.
    - Any notable observations (e.g., lab results, vitals) and what it means.
    """
    
    response = model.generate_content(prompt)
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
            temperature=0.3,
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
            temperature=0.3,
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

def process_patient(patient_id, model_choice):
    file_path = f"patient_reports/patient_{patient_id}.txt"
    
    print(f"Processing Patient {patient_id}...")

    text_data = load_text_report(file_path)
    if not text_data:
        print(f"No data found for Patient {patient_id}. Skipping.")
        return

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

    readability_scores = compute_readability(summary)

    print(f"**Summary for {patient_id}:**\n{summary}")
    print(f"**Readability Scores:**\n{readability_scores}")
    print(f"Patient {patient_id} processed successfully!")

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Please select Gemini or MiniMax.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", action="store_true", help="put -g in command line to use Gemini")
    group.add_argument("-m", action="store_true", help="put -m in command line to use MiniMax")
    group.add_argument("-c", action="store_true", help="put -c in command line to use ChatGPT")
    group.add_argument("-a", action="store_true", help="put -a in command line to use Claude")
    group.add_argument("-d", action="store_true", help="put -d in command line to use Deepseek")


    args = parser.parse_args()

    patient_id = input("Please enter the Patient ID: ").strip()

    model_choice = "gemini" if args.g else "minimax" if args.m else "chatgpt" if args.c else "claude" if args.a else "deepseek" if args.d else None
    
    process_patient(patient_id, model_choice)
