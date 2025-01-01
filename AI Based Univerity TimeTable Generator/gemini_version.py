import os
import json
import random
import logging
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in .env file.")

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration class
class Settings:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    BASE_TIME_SLOTS = [
        {"start": "08:00", "end": "09:15"},
        {"start": "09:30", "end": "10:45"},
        {"start": "11:00", "end": "12:15"},
        {"start": "12:30", "end": "13:45"},
        {"start": "14:00", "end": "15:15"},
        {"start": "15:30", "end": "16:45"},
        {"start": "17:00", "end": "18:15"}
    ]

# AI and Data Handling Utilities
class GeminiHandler:
    def __init__(self):
        import google.generativeai as genai  # Ensure it's imported here
        genai.configure(api_key=Settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_intelligent_response(self, prompt, temperature=0.7):
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': 8192
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Generation Error: {e}")
            return None

# CrewAI Agents
class UniversitySchedulerCrew:
    def __init__(self, teachers_df, rooms_df):
        self.teachers_df = teachers_df
        self.rooms_df = rooms_df
        self.gemini_handler = GeminiHandler()

    def create_course_analysis_agent(self):
        from crewai import Agent  # Ensure it's imported here
        return Agent(
            role='Course Data Analyst',
            goal='Analyze and extract detailed insights from course and teacher data',
            backstory='An expert in academic course planning with deep understanding of curriculum design and resource allocation',
            verbose=True,
            allow_delegation=False,
            llm=self.gemini_handler.model,
        )

    def create_scheduling_agent(self):
        from crewai import Agent  # Ensure it's imported here
        return Agent(
            role='University Scheduler',
            goal='Create an optimal and conflict-free course schedule',
            backstory='A strategic scheduler who ensures efficient use of resources, teacher availability, and student learning experience',
            verbose=True,
            allow_delegation=True,
            llm=self.gemini_handler.model,
        )

    def generate_intelligent_schedule(self):
        course_analysis_agent = self.create_course_analysis_agent()
        scheduling_agent = self.create_scheduling_agent()

        # Implement your analysis and scheduling logic here...

# Scheduling Logic class (unchanged)
class SchedulingAgent:
    def __init__(self, rooms_df, teachers_df):
        self.rooms_df = rooms_df
        self.teachers_df = teachers_df
        self.room_occupancy = {}
        self.teacher_occupancy = {}
        self.initialize_occupancy_tracking()

    def initialize_occupancy_tracking(self):
        for day in Settings.DAYS:
            self.room_occupancy[day] = {slot['start']: [] for slot in Settings.BASE_TIME_SLOTS}
            self.teacher_occupancy[day] = {slot['start']: [] for slot in Settings.BASE_TIME_SLOTS}

    def schedule_courses(self, courses):
        scheduled_courses = []
        for course in courses:
            scheduled_course = self.schedule_course(course)
            if scheduled_course:
                scheduled_courses.append(scheduled_course)
        return scheduled_courses

    def schedule_course(self, course):
        possible_rooms = self._get_suitable_rooms(course['course_type'])
        
        for _ in range(course.get('weekly_frequency', 2)):
            scheduled = False
            attempts = 0
            
            while not scheduled and attempts < 20:
                day = random.choice(Settings.DAYS)
                time_slot = random.choice(Settings.BASE_TIME_SLOTS)
                room = random.choice(possible_rooms)
                teacher = random.choice(course['teachers'])

                if self._is_slot_available(day, time_slot, room, teacher):
                    # Mark occupancy...
                    self.room_occupancy[day][time_slot['start']].append(room)
                    self.teacher_occupancy[day][time_slot['start']].append(teacher)

                    # Get full teacher details
                    teacher_details = self.teachers_df[self.teachers_df['Name'] == teacher].iloc[0]
                    return {
                        **course,
                        'assigned_teacher': teacher,
                        'teacher_department': teacher_details['Department'] if 'Department' in self.teachers_df.columns else 'N/A',
                        'assigned_room': room,
                        'assigned_day': day,
                        'assigned_time_slot': time_slot
                    }
                attempts += 1
        
        return None

    def _is_slot_available(self, day: str, time_slot: dict, room: str, teacher: str) -> bool:
        # Check room availability
        if room in self.room_occupancy[day][time_slot['start']]:
            return False
        
        # Check teacher availability
        if teacher in self.teacher_occupancy[day][time_slot['start']]:
            return False
        
        return True

    def _get_suitable_rooms(self, course_type: str) -> List[str]:
        room_type_mapping = {
            'Theory': 'Lecture Hall',
            'Hardware Lab': 'Hardware Lab',
            'Computing Lab': 'Computing Lab',
            'Physics Lab': 'Physics Lab'
        }
        
        return self.rooms_df[
            self.rooms_df['Room Type'] == room_type_mapping.get(course_type, 'Lecture Hall')
        ]['Room Name'].tolist()

# Streamlit Application 
def main():
    st.title("🎓 CrewAI Intelligent University Scheduler")
    
    # File uploaders for teachers and rooms data
    teachers_file = st.file_uploader("Upload Teachers Excel (with columns: Teacher, Course, Type)", type=['xlsx'])
    rooms_file = st.file_uploader("Upload Rooms Excel (with columns: Room Name, Room Type)", type=['xlsx'])

    if teachers_file and rooms_file:
        try:
            teachers_df = pd.read_excel(teachers_file)
            rooms_df = pd.read_excel(rooms_file)

            if 'Department' not in teachers_df.columns:
                teachers_df['Department'] = 'General'

            st.write("### Uploaded Teachers File:")
            st.dataframe(teachers_df)

            st.write("### Uploaded Rooms File:")
            st.dataframe(rooms_df)

            if st.button("Generate Timetable"):
                crew_scheduler = UniversitySchedulerCrew(teachers_df, rooms_df)
                timetable_df = crew_scheduler.generate_intelligent_schedule()

                if timetable_df is not None:
                    st.write("### Generated Timetable:")
                    st.dataframe(timetable_df)

                    # Download timetable as Excel
                    st.download_button(
                        label="Download Timetable",
                        data=timetable_df.to_excel(index=False, engine="openpyxl"),
                        file_name="timetable.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("Unable to generate timetable. Please check input data.")
        
        except Exception as e:
            st.error(f"An error occurred while processing files: {e}")
            logger.error(f"File Processing Error: {e}")

if __name__ == "__main__":
    main()
