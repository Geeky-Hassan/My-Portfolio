# conda activate "D:\Python_Projects\AI Timetable\aitimetable"
import os
import json
import random
import logging
import pandas as pd
import streamlit as st
from typing import List, Optional, Dict
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, Field

# CrewAI Imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai.llm import Gemini

# Google AI Imports
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration
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

# Enums and Models
class CourseType(str, Enum):
    THEORY = "Theory"
    HARDWARE_LAB = "Hardware Lab"
    COMPUTING_LAB = "Computing Lab"
    PHYSICS_LAB = "Physics Lab"

class Course(BaseModel):
    name: str
    code: str
    course_type: CourseType
    teachers: List[str]
    required_rooms: List[str] = []
    weekly_frequency: int = 2
    duration: int = 75

class ScheduledCourse(Course):
    assigned_teacher: Optional[str] = None
    assigned_room: Optional[str] = None
    assigned_day: Optional[str] = None
    assigned_time_slot: Optional[Dict] = None

# AI and Data Handling Utilities
class GeminiHandler:
    def __init__(self):
        genai.configure(api_key=Settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.llm = Gemini(api_key=Settings.GOOGLE_API_KEY)

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
      return Agent(
            role='Course Data Analyst',
            goal='Analyze and extract detailed insights from course and teacher data',
            backstory='An expert in academic course planning with deep understanding of curriculum design and resource allocation',
            verbose=True,
            allow_delegation=False,
            llm = self.gemini_handler.llm
        )

    def create_scheduling_agent(self):
        return Agent(
            role='University Scheduler',
            goal='Create an optimal and conflict-free course schedule',
            backstory='A strategic scheduler who ensures efficient use of resources, teacher availability, and student learning experience',
            verbose=True,
            allow_delegation=True,
            llm = self.gemini_handler.llm
        )

    def course_analysis_task(self, agent):
        return Task(
            description=f"""
            Analyze the course data and provide intelligent insights:
            {self.teachers_df.to_json(orient='records')}

            For each course, systematically determine:
            1. Precise course type
            2. Optimal teaching strategy
            3. Recommended weekly frequency
            4. Potential room requirements
            5. Suitable teachers for each course

            Ensure comprehensive and structured analysis.
            """,
            agent=agent,
            expected_output='Detailed JSON with course insights'
        )

    def scheduling_task(self, agent, analyzed_courses):
        return Task(
            description=f"""
            Create a comprehensive university course schedule based on analyzed courses.
            Constraints to consider:
            - Teacher availability
            - Room type suitability
            - Minimize scheduling conflicts
            - Ensure optimal distribution across days and time slots
            
            Analyzed Courses: {json.dumps(analyzed_courses, indent=2)}
            """,
            agent=agent,
            expected_output='Detailed course scheduling plan'
        )

    def generate_intelligent_schedule(self):
        course_analysis_agent = self.create_course_analysis_agent()
        scheduling_agent = self.create_scheduling_agent()

        course_analysis_task = self.course_analysis_task(course_analysis_agent)
        
        crew = Crew(
            agents=[course_analysis_agent, scheduling_agent],
            tasks=[course_analysis_task],
            process=Process.sequential
        )

        # Initial course analysis
        course_analysis_result = crew.kickoff()
        
        try:
            analyzed_courses = json.loads(course_analysis_result)
            
            # Scheduling task
            scheduling_task = self.scheduling_task(scheduling_agent, analyzed_courses)
            crew.tasks = [scheduling_task]
            
            scheduling_result = crew.kickoff()
            return scheduling_result
        except Exception as e:
            logger.error(f"Scheduling generation error: {e}")
            return None

# Scheduling Logic
class SchedulingAgent:
    def __init__(self, rooms_df, teachers_df):
        self.rooms_df = rooms_df
        self.teachers_df = teachers_df
        self.room_occupancy = {}
        self.teacher_occupancy = {}
        self.initialize_occupancy_tracking()

    def initialize_occupancy_tracking(self):
        for day in Settings.DAYS:
            self.room_occupancy[day] = {
                slot['start']: [] for slot in Settings.BASE_TIME_SLOTS
            }
            self.teacher_occupancy[day] = {
                slot['start']: [] for slot in Settings.BASE_TIME_SLOTS
            }

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
                    # Mark occupancy
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
        
        # Special Friday constraint can be added if needed
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
    
    # File uploaders
    teachers_file = st.file_uploader("Upload Teachers Excel", type=['xlsx'])
    rooms_file = st.file_uploader("Upload Rooms Excel", type=['xlsx'])

    if teachers_file and rooms_file:
        # Load data
        try:
            teachers_df = pd.read_excel(teachers_file)
            rooms_df = pd.read_excel(rooms_file)

            # Add Department column if not exists
            if 'Department' not in teachers_df.columns:
                teachers_df['Department'] = 'General'

            if st.button("Generate Intelligent Schedule"):
                # Initialize CrewAI Scheduler
                crew_scheduler = UniversitySchedulerCrew(teachers_df, rooms_df)
                
                # Generate intelligent schedule
                scheduling_result = crew_scheduler.generate_intelligent_schedule()
                
                # Process scheduling result
                scheduling_agent = SchedulingAgent(rooms_df, teachers_df)
                
                if scheduling_result:
                    # Parse results
                    analyzed_courses = json.loads(scheduling_result)
                    final_schedule = scheduling_agent.schedule_courses(analyzed_courses)
                    
                    # Display schedule
                    schedule_df = pd.DataFrame([
                        {
                            'Course': course['name'],
                            'Course Code': course['code'],
                            'Type': course['course_type'],
                            'Teacher Name': course['assigned_teacher'],
                            'Teacher Department': course.get('teacher_department', 'N/A'),
                            'Room': course['assigned_room'],
                            'Day': course['assigned_day'],
                            'Time Slot': f"{course['assigned_time_slot']['start']} - {course['assigned_time_slot']['end']}"
                        } for course in final_schedule
                    ])
                    
                    st.dataframe(schedule_df)
                    
                    # Download option
                    @st.cache_data
                    def convert_df(df):
                        return df.to_excel('intelligent_university_schedule.xlsx', index=False)
                    
                    st.download_button(
                        label="Download Schedule",
                        data=convert_df(schedule_df),
                        file_name='intelligent_university_schedule.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                else:
                    st.error("Unable to generate schedule. Please check input data.")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            logger.error(f"Scheduling Error: {e}")

if __name__ == "__main__":
    main()


# import pandas as pd

# # Expanded Sample Input Data Creation Function
# def create_expanded_sample_input_files():
#     # Teachers DataFrame - Expanded
#     teachers_data = {
#         'Name': [
#             'Dr. Smith', 'Prof. Johnson', 'Dr. Garcia', 'Prof. Kim', 'Ms. Rodriguez', 
#             'Dr. Lee', 'Prof. Brown', 'Dr. Wilson', 'Ms. Davis', 'Prof. Martinez', 
#             'Dr. Anderson', 'Ms. Taylor', 'Prof. Clark', 'Dr. White', 'Mr. Hall',
#              'Ms. Baker','Dr. Turner', 'Prof. King', 'Ms. Wright'
#         ],
#         'Course': [
#             'Digital Electronics', 'Programming Fundamentals', 'Linear Algebra', 'Physics Mechanics', 
#             'Web Development', 'Digital Signal Processing', 'Calculus', 'Data Structures', 
#             'Database Management', 'Thermodynamics', 'Artificial Intelligence', 'Operating Systems', 
#             'Probability and Statistics', 'Electromagnetism', 'Software Engineering', 
#             'Computer Networks', 'Quantum Mechanics', 'Differential Equations','Algorithm Analysis'
#         ],
#         'Course Code': [
#             'EE101', 'CS201', 'MATH101', 'PHY201', 'CS301', 'EE301', 'MATH201', 'CS202', 
#             'CS302', 'PHY301', 'CS401', 'CS303', 'MATH301', 'PHY302', 'CS402',
#             'CS403', 'PHY401', 'MATH302','CS404'
#         ],
#         'Course Type': [
#             'Hardware Lab', 'Computing Lab', 'Theory', 'Physics Lab', 'Computing Lab', 
#             'Hardware Lab', 'Theory', 'Computing Lab', 'Computing Lab', 'Physics Lab', 
#             'Computing Lab', 'Computing Lab', 'Theory', 'Physics Lab', 'Theory',
#              'Computing Lab', 'Physics Lab', 'Theory', 'Theory'
#         ],
#         'Department': [
#             'Electrical Engineering', 'Computer Science', 'Mathematics', 'Physics', 
#             'Computer Science', 'Electrical Engineering', 'Mathematics', 'Computer Science',
#             'Computer Science', 'Physics', 'Computer Science', 'Computer Science',
#             'Mathematics', 'Physics', 'Computer Science', 'Computer Science', 'Physics', 'Mathematics','Computer Science'
#         ]
#     }
#     teachers_df = pd.DataFrame(teachers_data)
#     teachers_df.to_excel('teachers_expanded.xlsx', index=False)

#     # Rooms DataFrame - Expanded
#     rooms_data = {
#         'Room Name': [
#             'Lab A', 'Lab B', 'Lab C', 'Lecture Hall 1', 'Lecture Hall 2', 
#             'Computing Room 1', 'Physics Workshop', 'Lecture Hall 3', 'Lab D',
#             'Computing Room 2', 'Physics Lab 2','Lecture Hall 4','Conference Room'
#         ],
#         'Room Type': [
#             'Hardware Lab', 'Computing Lab', 'Physics Lab', 'Lecture Hall', 'Lecture Hall', 
#             'Computing Lab', 'Physics Lab', 'Lecture Hall', 'Hardware Lab',
#             'Computing Lab', 'Physics Lab', 'Lecture Hall','Lecture Hall'
#         ],
#         'Capacity': [25, 30, 20, 50, 60, 35, 18, 70, 28, 40, 22, 55, 30]
#     }
#     rooms_df = pd.DataFrame(rooms_data)
#     rooms_df.to_excel('rooms_expanded.xlsx', index=False)
    
#     return teachers_df, rooms_df

# if __name__ == '__main__':
#     teachers_df, rooms_df = create_expanded_sample_input_files()
#     print("Expanded sample data files 'teachers_expanded.xlsx' and 'rooms_expanded.xlsx' created successfully.")

# Uncomment the following lines to generate sample input files
# teachers_df, rooms_df = create_sample_input_files()
# print("Sample input files 'teachers_sample.xlsx' and 'rooms_sample.xlsx' created.")