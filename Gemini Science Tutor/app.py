# conda activate "D:\Python_Projects\B3 AI\chatbot_history_gemini\chatbot1"

import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key = os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature" : 0,
    "top_p": 0.95,
    "top_k":64,
    "max_output_tokens":8192,
    "response_mime_type":"text/plain"

}

safety_settings = [
    {
        "category" : "HARM_CATEGORY_HARASSMENT",
        "threshold" : "BLOCK_NONE"
    },
    {
        "category" : "HARM_CATEGORY_HATE_SPEECH",
        "threshold" : "BLOCK_MEDIUM_AND_ABOVE"

    },
    {
        "category" : "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold" : "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(
    model_name = "gemini-1.5-flash",
    safety_settings = safety_settings,
    generation_config = generation_config,
    system_instruction = "You are an expert at teaching science to kids. Your task is to engage in conversation about science and answer questions. Explain scientific concepts so that they are easily understandable. Use Analogies and examples that are relatable. Use Humor and make the converstaion both educational and interesting. Ask Questions so that you can better understand the user and improve the eductaional experiences. Suggest way that these concepts can be related to the real world with observations and experiments.",
)

history = []

print("Bot: Hello, how can i help you?")
print()

while True:
    user_input = input("You: ")
    print()

    chat_session = model.start_chat(
        history = history
    )
    response = chat_session.send_message(user_input)

    model_response = response.text

    print(f'Bot: {model_response}')
    print()

    history.append({"role":"user","parts":[user_input]})
    history.append({"role":"model","parts":[model_response]})


