from env_setup import *
from data_loader import load_data
from agent_setup import create_agents_and_tasks
import streamlit as st
import pandas as pd
import io

def main():
    teacher_df, room_df = load_data()

    if teacher_df is not None and room_df is not None:
        crew = create_agents_and_tasks(teacher_df, room_df)
        try:
             # Start the crew to get the final output
             result = crew.kickoff()
             # Parse the JSON timetable string back into a dataframe
             try:
                 timetable_df = pd.read_excel(io.BytesIO(result.encode()))
             except Exception as e:
                st.error(f"Could not parse the timetable into data frame, due to the following error: {e}")
                return

             st.subheader("Generated Timetable")
             st.dataframe(timetable_df)
             excel_buffer = io.BytesIO()
             with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                timetable_df.to_excel(writer, sheet_name='Timetable', index=False)
             excel_buffer.seek(0)
             st.download_button(
                label="Download Excel Timetable",
                data=excel_buffer,
                file_name="timetable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
             st.error(f"An error occurred during timetable generation: {e}")



if __name__ == "__main__":
    main()