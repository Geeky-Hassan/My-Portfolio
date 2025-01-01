import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# System constraints
TIMETABLE_CONSTRAINTS = """
Generate a timetable following these constraints:

1. Time Constraints:
   - Classes run Monday through Saturday
   - Theory class slots: 8:00-9:15, 9:30-10:45, 11:00-12:15, 2:00-3:15, 3:30-4:45, 5:00-6:15
   - Friday slots: 8:00-9:15, 9:30-10:45, 11:00-12:15, 2:00-3:15, 3:30-4:45, 5:00-6:15 (no 12:30-1:45 slot)
   - Theory classes: 1 hour 15 minutes
   - Lab slots: 2 hour 30 minutes (start at 8:00, 11:00, 2:00, 5:00)
   - 30 minutes break between labs
   - No overlap between labs and theory classes
   - There must be no overlap between same courses but different sections if the teacher is same in both classes.

2. Room Constraints:
   - Labs only in lab rooms
   - Theory classes in lecture rooms
   - Room capacity must match/exceed class size

3. Teacher Constraints:
   - No overlapping classes
   - Maximum 3 classes per day per teacher
   - 30 minutes minimum break between classes
   - One day break between same course for same teacher

4. Course Constraints:
   - 3 credit courses: 2 sessions per week
   - Lab courses: 1 session (2.5 hours) per week
   - No core course clashes within same semester
   - Controlled overlaps for electives
"""

class TimetableGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.5,
            google_api_key=GOOGLE_API_KEY
        )
        
    def validate_data(self, df, required_columns, file_type):
        """Validate input data files"""
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{file_type} file missing columns: {', '.join(missing_cols)}")
        
        empty_cols = df.columns[df.isna().any()].tolist()
        if empty_cols:
            raise ValueError(f"{file_type} file has empty values in columns: {', '.join(empty_cols)}")
    
    def load_data(self, teachers_file, rooms_file):
        """Load and validate input data"""
        try:
            teachers_df = pd.read_excel(teachers_file)
            rooms_df = pd.read_excel(rooms_file)
            
            self.validate_data(
                teachers_df,
                ['Name', 'Course', 'Course Code', 'Course Type', 'Department'],
                'Teachers'
            )
            self.validate_data(
                rooms_df,
                ['Room Name', 'Room Type', 'Capacity'],
                'Rooms'
            )
            
            return teachers_df, rooms_df
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")

    def validate_timetable_entry(self, entry):
        """Validate a single timetable entry"""
        required_fields = ['Day', 'StartTime', 'EndTime', 'CourseCode', 'CourseType', 'Room', 'Teacher']
        
        # Check all required fields exist
        for field in required_fields:
            if field not in entry:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate Day
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        if entry['Day'] not in valid_days:
            raise ValueError(f"Invalid day: {entry['Day']}")
            
        # Validate Time format
        try:
            datetime.strptime(entry['StartTime'], '%H:%M')
            datetime.strptime(entry['EndTime'], '%H:%M')
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM")
            
        return entry

    def parse_json_response(self, response_text):
        """Parse and validate JSON response"""
        try:
            # Find the first occurrence of '[' and the last occurrence of ']'
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in response")
                
            # Extract and parse JSON
            json_str = response_text[start:end]
            data = json.loads(json_str)
            
            if not isinstance(data, list):
                raise ValueError("Response is not a JSON array")
                
            # Validate each entry
            validated_data = [self.validate_timetable_entry(entry) for entry in data]
            return validated_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
            
    def generate_timetable(self, teachers_df, rooms_df):
        """Generate timetable using LangChain and Gemini"""
        try:
            # Format data for prompt
            teachers_info = "\n".join([
                f"Teacher: {row['Name']}, Course: {row['Course']}, Code: {row['Course Code']}, "
                f"Type: {row['Course Type']}, Department: {row['Department']}"
                for _, row in teachers_df.iterrows()
            ])
            
            rooms_info = "\n".join([
                f"Room: {row['Room Name']}, Type: {row['Room Type']}, Capacity: {row['Capacity']}"
                for _, row in rooms_df.iterrows()
            ])
            
            prompt = PromptTemplate(
                template="""
{constraints}

Using this data, generate a complete weekly timetable:

TEACHERS INFORMATION:
{teachers}

ROOMS INFORMATION:
{rooms}

Return ONLY a JSON array where each entry has this exact format:
{{
    "Day": "Monday",
    "StartTime": "08:00",
    "EndTime": "09:15",
    "CourseCode": "CS101",
    "Course": "Programming Fundamentals"
    "CourseType": "Theory",
    "Room": "Room Name",
    "Teacher": "Teacher Name"
}}

Return only the JSON array with no additional text or explanations.""",
                input_variables=["constraints", "teachers", "rooms"]
            )

            # Create and run chain
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(
                constraints=TIMETABLE_CONSTRAINTS,
                teachers=teachers_info,
                rooms=rooms_info
            )
            
            # Parse and validate response
            timetable_data = self.parse_json_response(response)
            
            # Convert to DataFrame
            timetable_df = pd.DataFrame(timetable_data)
            
            # Sort by day and time
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            timetable_df['DayOrder'] = pd.Categorical(timetable_df['Day'], categories=day_order, ordered=True)
            timetable_df = timetable_df.sort_values(['DayOrder', 'StartTime'])
            timetable_df = timetable_df.drop('DayOrder', axis=1)
            
            return timetable_df
            
        except Exception as e:
            raise Exception(f"Error generating timetable: {str(e)}")

    def export_to_excel(self, df, filename):
        """Export timetable to formatted Excel file"""
        try:
            writer = pd.ExcelWriter(filename, engine='openpyxl')
            df.to_excel(writer, index=False, sheet_name='Timetable')
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Timetable']
            
            # Format columns
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            writer.close()
            return filename
        except Exception as e:
            raise Exception(f"Error exporting to Excel: {str(e)}")

def main():
    st.set_page_config(page_title="UMT Timetable Generator", layout="wide")
    
    st.title("UMT Timetable Generator")
    st.write("Upload teachers and rooms data to generate a timetable")
    
    # File uploaders
    col1, col2 = st.columns(2)
    with col1:
        teachers_file = st.file_uploader("Upload Teachers Data (Excel)", type=['xlsx'])
        if teachers_file:
            st.success("Teachers file uploaded successfully!")
    with col2:
        rooms_file = st.file_uploader("Upload Rooms Data (Excel)", type=['xlsx'])
        if rooms_file:
            st.success("Rooms file uploaded successfully!")
    
    if teachers_file and rooms_file:
        try:
            generator = TimetableGenerator()
            
            # Load data
            with st.spinner("Loading data..."):
                teachers_df, rooms_df = generator.load_data(teachers_file, rooms_file)
            
            # Show data previews
            st.subheader("Data Preview")
            tab1, tab2 = st.tabs(["Teachers Data", "Rooms Data"])
            with tab1:
                st.dataframe(teachers_df, use_container_width=True)
            with tab2:
                st.dataframe(rooms_df, use_container_width=True)
            
            # Generate button
            if st.button("Generate Timetable", type="primary"):
                with st.spinner("Generating timetable... This may take a few minutes."):
                    try:
                        timetable_df = generator.generate_timetable(teachers_df, rooms_df)
                        
                        # Display timetable
                        st.subheader("Generated Timetable")
                        st.dataframe(
                            timetable_df,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Export to Excel
                        if not os.path.exists('temp'):
                            os.makedirs('temp')
                        filename = f"temp/timetable_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        generator.export_to_excel(timetable_df, filename)
                        
                        # Download button
                        with open(filename, 'rb') as f:
                            st.download_button(
                                label="📥 Download Timetable",
                                data=f,
                                file_name=os.path.basename(filename),
                                mime="application/vnd.ms-excel"
                            )
                        
                        # Cleanup temp file
                        try:
                            os.remove(filename)
                        except:
                            pass
                            
                    except Exception as e:
                        st.error("Failed to generate timetable. Please try again.")
                        st.error(f"Error details: {str(e)}")
                    
        except Exception as e:
            st.error("Error loading data. Please check your input files.")
            st.error(f"Error details: {str(e)}")

if __name__ == "__main__":
    main()