# import streamlit as st
# from dotenv import load_dotenv

# import os
# import google.generativeai as genai
# from youtube_transcript_api import YouTubeTranscriptApi

# load_dotenv()

# genai.configure(api_key = os.getenv("GOOGLE_API_KEY"))

# prompt = """You are Youtube video summarizer. You will be taking the transcript textand summarizing the entire video and providning the important summary in points within 300 words. Please Provide the summary of the text given here: """

# def extract_video_details(youtube_video_url):
#     try:
#         video_id = youtube_video_url.split("=")[1]
#         transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

#         transcript = ""
#         for i in transcript_text:
#             transcript += " " + i["text"]
#         return transcript
#     except Exception as e:
#         raise e

# def generate_gemini_content(transcript_text,prompt):
#     model = genai.GenerativeModel('gemini-pro')
#     response = model.generate_content(prompt+transcript_text)
#     return response.text


# st.title("Youtube AI Summerizer")
# youtube_link = st.text_input("Enter the youtube Link")

# if youtube_link:
#     video_id = youtube_link.split("=")[1]

#     print(video_id)
#     st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

# if st.button("Get the Summary"):
#      transcript_text = extract_video_details(youtube_link)

#      if transcript_text:
#          summary = generate_gemini_content(transcript_text,prompt)
#          st.markdown("Full Summary:")
#          st.write(summary)
    


import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

prompt = """You are a Youtube video summarizer. You will be taking the transcript text and summarizing the entire video and providing the important summary in points within 300 words. Please provide the summary of the text given here: """

def extract_video_details(youtube_video_url):
    try:
        # More robust video ID extraction
        if "v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1]
        else:
            raise ValueError("Invalid YouTube URL format")

        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]
        return transcript
    except TranscriptsDisabled:
        st.error("Subtitles are disabled for this video.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise e

def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt + transcript_text)
    return response.text

st.title("YouTube AI Summarizer")
youtube_link = st.text_input("Enter the YouTube Link")

if youtube_link:
    if "v=" in youtube_link:
        video_id = youtube_link.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_link:
        video_id = youtube_link.split("youtu.be/")[1]
    else:
        st.error("Invalid YouTube URL format")

    st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

if st.button("Get the Summary"):
    if youtube_link:
        transcript_text = extract_video_details(youtube_link)

        if transcript_text:
            summary = generate_gemini_content(transcript_text, prompt)
            st.markdown("Full Summary:")
            st.write(summary)
        else:
            st.error("Failed to retrieve transcript for the video.")





