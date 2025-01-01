# --- Section 1: Environment Setup (env_setup.py) ---
import streamlit as st
import pandas as pd
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import io
import json

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")