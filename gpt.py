import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing_extensions import Annotated

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

OPENAI_API_KEY = load_dotenv()

db = SQLDatabase.from_uri('postgresql+psycopg2://postgres:NeonWaterfallz8741@localhost/data')
llm = ChatOpenAI(model="gpt-4o")

