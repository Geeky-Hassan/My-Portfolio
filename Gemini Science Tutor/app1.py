# step 1: create a virtual environment and then activate that environment
# step 2: create 3 files, 1) app.py 2) .env   3) requirements.txt
# step 3: add api key into .env file
# step 4: add libraries names in requirements.txt file
# step 5: after activating the environment, install libraries in the envirnment..how, just write, 
# pip install -r requirements.txt


import os
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.1,
    "response_mime_type": "text/plain",
    "max_output_tokens": 8192
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You are an expert at teaching science to kids. Your task is to engage in conversation about science and answer questions. Explain scientific concepts so that they are easily understandable. Use humor and make the conversation both educational and interesting. Ask questions so that you can better understand the user and improve the educational experience. Make sure to restrict yourself only to science-related topics as you are a science teacher."
)

# Initialize chat history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# Display or initialize the chat session
chat_session = model.start_chat(history=st.session_state.history)

# Display bot's initial message if history is empty
if not st.session_state.history:
    st.chat_message("assistant").write("Hello, How can I help you today?")
    st.session_state.history.append({"role": "model", "parts": ["Hello, How can I help you today?"]})

# Get user input
user_input = st.chat_input("You: ")

if user_input:
    # Append user message to history and display it
    st.session_state.history.append({"role": "user", "parts": [user_input]})
    st.chat_message("user").write(user_input)

    # Send user message to the model and get response
    response = chat_session.send_message(user_input)
    model_response = response.text

    # Append bot's response to history and display it
    st.session_state.history.append({"role": "model", "parts": [model_response]})
    st.chat_message("assistant").write(model_response)
