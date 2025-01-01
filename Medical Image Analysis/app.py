# conda activate "D:\Python_Projects\B5 AI\Medical_Image_Analysis\medicalenv"

import google.generativeai as genai
from pathlib import Path
import os
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def read_image_data(file_path):
    image_path = Path(file_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Could not find the image: {image_path}")
    return {"mime_type":"image/jpeg", "data":image_path.read_bytes()}

def generate_gemini_reply(prompt,image_path):
    image_data = read_image_data(image_path)
    response = model.generate_content([prompt,image_data])
    return response.text

# input_prompt = """Analyze the provided chest X-ray image in detail. Generate a comprehensive report outlining potential abnormalities, diagnoses, and recommended actions. Structure the report as follows:

# 1. Image Analysis:

# Describe the overall appearance of the chest, including lung fields, heart, mediastinum, diaphragm, and bony structures.
# Identify any abnormal findings, such as opacities, infiltrates, masses, nodules, pleural effusions, pneumothorax, or bone abnormalities.
# Provide detailed descriptions of the location, size, shape, and density of any identified abnormalities.
# 2. Potential Diagnoses:

# Based on the identified abnormalities, list potential diagnoses in order of likelihood.
# Provide a brief explanation for each potential diagnosis, including relevant clinical features.
# 3. Recommendations:

# Outline necessary follow-up investigations, such as additional imaging studies or laboratory tests.
# Suggest potential treatment options based on the likely diagnosis.
# Emphasize the importance of clinical correlation and further evaluation by a qualified healthcare professional.

# 4- Medication:
# Based on the potential diagnoses, suggest possible medications that could be considered.
# Clearly indicate that these are potential medications based on limited information and should not replace professional medical advice.

# 5. Limitations:

# Clearly state that this report is based solely on the provided chest X-ray image and does not replace a clinical evaluation by a healthcare provider.
# Highlight the importance of considering patient history, symptoms, and other diagnostic tests for an accurate diagnosis and treatment plan.

# Remember that you are an X ray Analyzer and you cannot analyze or describe any other image except chest X rays, You don't know anythung beyond that...On irrelevent images, Just say, I cannot describe this image as it's not an X ray.
# Note: The report should be written in clear and concise language, avoiding medical jargon. Use bullet points or numbered lists to enhance readability.

# """
input_prompt = """Analyze the provided image of a room or space. Generate a comprehensive report outlining potential design improvements, style suggestions, and furniture recommendations. Structure the report as follows:

1. Space Analysis:

Describe the overall layout, size, and natural light conditions of the space.
Identify the existing furniture, decor, and color palette.
Assess the functionality and flow of the space.
2. Style Analysis:

Determine the current design style of the space.
Identify any style inconsistencies or clashes.
Suggest potential design styles that would complement the space and meet the desired aesthetic.
3. Recommendations:

Propose specific design improvements, such as rearranging furniture, adding or removing elements, or modifying wall treatments.
Recommend furniture pieces and decor items that would enhance the space and align with the chosen style.
Suggest color palettes and material choices to create a cohesive and visually appealing environment.
4. Potential Challenges:

Identify any potential challenges or limitations of the space, such as awkward layouts, small dimensions, or low ceilings.
Suggest creative solutions to overcome these challenges.
5. Disclaimer:

Clearly state that this report is based solely on the provided image and does not account for personal preferences, budget, or practical considerations.
Emphasize the importance of consulting with an interior designer for personalized and tailored recommendations.
Note: The report should be written in clear and concise language, avoiding design jargon. Use visuals or diagrams to support the recommendations when possible.




"""

def process_upload_file(files):
    file_path = files[0].name if files else None
    response = generate_gemini_reply(input_prompt,file_path) if file_path else None

    return file_path, response


with gr.Blocks() as demo:
    file_output = gr.Textbox()
    image_output = gr.Image()
    combined_output = [image_output,file_output]

    upload_button = gr.UploadButton(
        "Click to upload an image..",
        file_types=['image'],
        file_count='multiple'
    )
    upload_button.upload(process_upload_file,upload_button,combined_output)

demo.launch(debug= True)    




