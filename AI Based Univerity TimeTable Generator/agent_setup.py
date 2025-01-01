def create_agents_and_tasks(teacher_df, room_df):
    llm = ChatGoogleGenerativeAI(model="gemini-pro")

    data_gatherer = Agent(
        role='Data Gathering Expert',
        goal='Gather and organize all required data from provided excel sheets',
        backstory='An expert in extracting information from datasets.',
        llm=llm
    )

    scheduler = Agent(
        role='Timetable Scheduler',
        goal='Create an initial timetable based on the data, applying all provided constraints.',
        backstory='A very skilled scheduler who takes constraints very seriously.',
        llm=llm
    )

    conflict_resolver = Agent(
        role='Conflict Resolver',
        goal='Identify and resolve scheduling conflicts, ensuring no violations.',
        backstory='An extremely detail-oriented conflict resolver with expertise in timetables.',
        llm=llm
    )

    output_generator = Agent(
        role="Output Generator",
        goal='Format the final timetable in a proper output file (Excel)',
        backstory="Expert at file formatting and data handling.",
        llm=llm
    )

    data_gathering_task = Task(
        description=f"Collect all data about the teachers, courses, allocated labs, and available rooms from the given data and write it as a JSON string. Teachers data: {teacher_df.to_json()}, room data: {room_df.to_json()}",
        agent=data_gatherer
    )

    scheduling_task = Task(
         description="""Generate a tentative timetable based on the data gathered from Data Gatherer while respecting all of the constraints provided below.
            Constraints to follow:
            1. Every Theory Lecture is of 1 hour and 15 minutes.
            2. University first lecture starts at 8 am and ends at 6:30 pm, including Saturday.
            3. There is a 15-minute break between every lecture.
            4. The first lecture is between 8 am to 9:15 am and then the second lecture will start from 9:30 to 10:45 am and so on.
            5. Every lab is a combination of 2 lectures (it will be 2 hours and 30 minutes long).
            6. Labs will only happen once a week.
            7. Theory lectures will happen twice a week.
            8. There is no lecture from 12:30 to 2 pm on Friday.
            9. There are 3 types of labs: Hardware, Computing, and Physics labs, and they must be allocated to their respective locations.
            Output: Output a json string of a timetable.
        """,
        agent=scheduler
    )


    conflict_resolution_task = Task(
        description="""Identify and resolve any conflicts in the tentative timetable. Make sure there is no teacher, room, or lab clash.
            Constraints to follow:
            1. Every Theory Lecture is of 1 hour and 15 minutes.
            2. University first lecture starts at 8 am and ends at 6:30 pm, including Saturday.
            3. There is a 15-minute break between every lecture.
            4. The first lecture is between 8 am to 9:15 am and then the second lecture will start from 9:30 to 10:45 am and so on.
            5. Every lab is a combination of 2 lectures (it will be 2 hours and 30 minutes long).
            6. Labs will only happen once a week.
            7. Theory lectures will happen twice a week.
            8. There is no lecture from 12:30 to 2 pm on Friday.
            9. There are 3 types of labs: Hardware, Computing, and Physics labs, and they must be allocated to their respective locations.
            Output: Output a JSON string of a conflict-free timetable.
        """,
        agent=conflict_resolver
    )

    output_generation_task = Task(
         description="""Format the given timetable data to generate a proper excel file with each column named correctly and a named sheet.
            Make sure the output is an Excel file that can be directly downloaded by the user.
            Input:{timetable}
            Output: The output will be a valid Excel file.
         """,
        agent=output_generator,
     )

    crew = Crew(
        agents=[data_gatherer, scheduler, conflict_resolver, output_generator],
        tasks=[data_gathering_task, scheduling_task, conflict_resolution_task, output_generation_task],
        process=Process.sequential,
    )
    return crew