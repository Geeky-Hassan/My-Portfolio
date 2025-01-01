import streamlit as st
import os
import io
from PIL import Image

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

text_model = genai.GenerativeModel("gemini-1.5-flash")
image_model = genai.GenerativeModel("gemini-1.5-flash")

def get_combinations(query,clothes_desc):
    if query == "":
        text = f"You are an amazing stylist who knows best color combinations for outfits. So Build me some good outfits with great color combinations from the clothes which i have uploaded, these are the descriptions of each item {clothes_desc}. Using the description of each item, I want you to generate some good outfits for me using the items which i have given you"
    elif clothes_desc == []:
        text = f"You are an amazing stylist who knows best color combinations for outfits. So Build me some good outfits with great color combinations using the description of each item, I want you to generate some good outfits for me along with the need like {query}."
    else:
        text = f"You are an amazing stylist who knows best color combinations for outfits. So Build me some good outfits with great color combinations from the clothes which i have uploaded, these are the descriptions of each item {clothes_desc}. Using the description of each item, I want you to generate some good outfits for me along with the need like {query}."
    response = text_model.generate_content(text)
    response.resolve()
    return response.text

def get_img_desc(image):
    text = f"Describe the image in detail like what the piece is and what color it is."
    response = image_model.generate_content([text,image],stream=True)
    response.resolve()
    return response.text 



st.set_page_config(page_title="Dress Finder", page_icon="👕👔🎀")

# Image Upload Sections

st.title("Dress Finder🥼")

st.text("Upload pictures of your clothes and we'll suggest some great outfits!")
st.text("You can also add some other descriptions for the outfit you want to add on.")
st.text("Please Upload at least one image to generate outfit suggestions.")

uploaded_clothes = st.file_uploader("Upload Clothes", accept_multiple_files= True, type=["png","jpg","jpeg"])

clothes_desc = []
query = ""

query = st.text_input("Enter some othetr description for the outfit you want to add on", key = "other_desc")

if st.button("Generate Outfits"):
    if not uploaded_clothes and query == "":
        st.error("Please upload at least ome image or describe your needs in textbox to generate outfit suggestions.")
        exit()
    for clothes in uploaded_clothes:
        clothes_image = Image.open(clothes)
        st.image(clothes_image,caption="Uploaded Image. ", use_column_width= True)
        clothes_desc.append(get_img_desc(clothes_image))

    st.text("Almost there, Please wait...")

    print(clothes_desc)

    final_combo = (get_combinations(query,clothes_desc))
    st.success("Here are some outfits suggestions for you!")
    st.subheader("👔👕🧥")
    st.success(final_combo)
    print(final_combo)

st.markdown("***While uploading images it might take some more time to process the images. So please wait for some time.***")


