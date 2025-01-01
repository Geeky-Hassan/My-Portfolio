import streamlit as st
import os
import io
from PIL import Image

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
image_model = genai.GenerativeModel("gemini-pro-vision")


def get_caption(platform, max_length,image):
    min_length = 20
    if platform is None:
        text = f'Generate a caption for this image: {image} with a max length of {max_length} and min length of {min_length}.'
    else:
        text = f'generate me a caption for this image for {platform}: {image}. Which i can use on my {platform} and the caption should be max length of {max_length} and min length of {min_length}. Give me the tags as well for that {platform}.'
    response = image_model.generate_content([text,image])
    return response.text


st.title("Image Caption Generator")
st.write("This app generates a caption for an image.")

uploaded_file = st.file_uploader("choose an image...", type= ["png","jpg","jpeg"])
max_length = st.slider("Select the length of the caption,", 50,100,70)


platform = ""

if st.button("identify image"):
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image,caption="Uploaded Image. ", use_column_width= True)
        st.write("")
        st.write("generating Caption")
        caption = get_caption(platform,max_length,image)
        st.write(f"Caption: {caption}")
    else:
        st.write("Please uplaod an image first")

if st.button("Insta Caption"):
    if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image,caption="Uploaded Image. ", use_column_width= True)
            st.write("")
            st.write("Generating Caption for instagram")
            caption = get_caption("instagram",max_length,image)
            st.write(f"Caption: {caption}")
    else:
            st.write("Please uplaod an image first")



