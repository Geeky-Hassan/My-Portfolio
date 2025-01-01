import os
import google.generativeai as genai
from dotenv import load_dotenv
import gradio as gr

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

def respond(message, chat_history):
    if message:
        chat_history = chat_history + [[message, None]]
        
        model_history = []
        for turn in chat_history:
            if turn[0] is not None:
                model_history.append({"role": "user", "parts": [turn[0]]})
            if turn[1] is not None:
                model_history.append({"role": "model", "parts": [turn[1]]})
        
        chat_session = model.start_chat(history=model_history)
        response = chat_session.send_message(message)
        model_response = response.text
        
        chat_history[-1][1] = model_response
    else:
        pass
    
    return "", chat_history

initial_chat = [[None, "Hello, How can I help you today?"]]

with gr.Blocks(css=""".gradio-container {text-align: center;}.chatbot {width: 60%; margin: 0 auto;}""") as demo:
    gr.Markdown("<h1 style='text-align: center;'>Science Chatbot</h1>")
    gr.Markdown("<h3 style='text-align: center;'>Ask me anything about science!</h3>")
    
    with gr.Row():
        chatbot = gr.Chatbot(value=initial_chat, height=500)
    
    with gr.Row():
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])
    
    msg.submit(respond, [msg, chatbot], [msg, chatbot], queue=False)
    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch()









