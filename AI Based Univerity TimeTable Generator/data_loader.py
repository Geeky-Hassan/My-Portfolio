import streamlit as st
import pandas as pd

def load_data():
    st.title("AI-Powered Timetable Generator")

    uploaded_teacher_file = st.file_uploader("Upload Teacher Allocation Excel file", type=["xlsx", "xls"])
    if uploaded_teacher_file:
        try:
            teacher_df = pd.read_excel(uploaded_teacher_file)
            st.success("Teacher data loaded successfully.")
            st.dataframe(teacher_df)
        except Exception as e:
            st.error(f"Error loading teacher file: {e}")
            return None, None

    uploaded_room_file = st.file_uploader("Upload Room Availability Excel file", type=["xlsx", "xls"])
    if uploaded_room_file:
        try:
            room_df = pd.read_excel(uploaded_room_file)
            st.success("Room data loaded successfully.")
            st.dataframe(room_df)
        except Exception as e:
            st.error(f"Error loading room file: {e}")
            return None, None

    if uploaded_teacher_file and uploaded_room_file:
        return teacher_df, room_df
    else:
        return None, None