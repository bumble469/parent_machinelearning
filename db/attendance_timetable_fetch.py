import pandas as pd
from db.connection import get_db_engine
import json
from db.utils.flask_security import call_flask_decrypt_api
from datetime import datetime

def convert_to_am_pm(time_str):
    try:
        # Assuming the input time format is "HH:MM:SS"
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.strftime('%I:%M:%S %p')  # Convert to 12-hour format with AM/PM
    except Exception as e:
        print(f"Error converting time: {e}")
        return time_str  # In case of error, return the original time string

# Function to fetch and format the latest timetable
async def fetch_latest_timetable(prn):
    # Define your SQL query to fetch the timetable for the latest week
    query = """
    SELECT 
        [time_table_id],
        [subject_id],
        [subject_name],
        [teacher_fullname],
        [lecture_type],
        [day_name],
        [lecture_timing],
        [week_number]
    FROM [psat_final].[dbo].[vw_latest_timetable]
    WHERE [week_number] = (SELECT MAX([week_number]) FROM [psat_final].[dbo].[vw_latest_timetable])
    """
    
    # Fetch the data into a pandas DataFrame using your DB engine
    engine = get_db_engine()  # Assuming this function sets up the engine correctly
    df = pd.read_sql(query, engine)
    
    # Decrypt teacher names
    decrypted_teacher_names = []
    for index, row in df.iterrows():
        encrypted_data = row['teacher_fullname']
        encrypted_data_json = json.loads(encrypted_data)  # Assuming the data is in JSON format
        final_data = encrypted_data_json['final_data']
        encrypted_aes_key = encrypted_data_json['encrypted_aes_key']
        
        # Decrypt the teacher name
        decrypted_name = await call_flask_decrypt_api(final_data, encrypted_aes_key)
        decrypted_teacher_names.append(decrypted_name)
    
    days = df['day_name'].unique()
    timetable_data = {
        "prn": [prn] * len(days),
        "subject": [],
        "teacher": [],
        "day_name": [],
        "lecture_type": [],
        "lecture_timing": [],
        "week_number": []
    }
    
    for day in days:
        day_data = df[df['day_name'] == day]  # Filter data for each day
        
        # Sort by lecture_timing and select the earliest
        day_data_sorted = day_data.sort_values(by="lecture_timing", ascending=True)
        
        # Select the earliest lecture for the day (first row after sorting)
        earliest_lecture = day_data_sorted.iloc[0]
        
        # Collect all subjects, teachers, lecture types, and timings
        subjects = day_data_sorted['subject_name'].tolist()
        teachers = [decrypted_teacher_names[i] for i in day_data_sorted.index]
        lecture_types = day_data_sorted['lecture_type'].tolist()
        lecture_timings = day_data_sorted['lecture_timing'].astype(str).tolist()  # Convert time to string
        
        # Convert lecture timings to AM/PM format, but keep all timings
        lecture_timings = [convert_to_am_pm(time) for time in lecture_timings]
        
        # Keep the earliest time only and put it in the structure
        timetable_data["subject"].append(subjects)  # Keep all subjects for the day
        timetable_data["teacher"].append(teachers)  # Keep all teachers for the day
        timetable_data["day_name"].append(day)
        timetable_data["lecture_type"].append(lecture_types)  # Keep all lecture types for the day
        timetable_data["lecture_timing"].append([lecture_timings[0]])  # Only keep the earliest time for the day
        timetable_data["week_number"].append(int(earliest_lecture['week_number']))  # Keep the week number
    
    return timetable_data
