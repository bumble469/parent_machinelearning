import pandas as pd
from db.connection import get_db_engine
from db.utils.flask_security import call_flask_decrypt_api
import json

async def fetch_subject_teacher_mapping(prn):
    engine = get_db_engine()
    query = """
        SELECT prn,
            subject_name,
            teacher_name,
            week_number,
            day_name,
            day_no,
            lecture_type,
            lecture_timing,
            attendance,
            festival,
            date
        FROM psat_final.dbo.vw_student_attendance_details
        WHERE prn = ? AND teacher_name IS NOT NULL
    """
    
    df = pd.read_sql(query, engine, params=(prn,))
    
    # Rename columns as necessary at the start of the function
    df.rename(columns={
        "subject_name": "subject",
        "teacher_name": "teacher"
    }, inplace=True)
    
    subject_teacher_mapping = df[['subject', 'teacher']].drop_duplicates()

    decrypted_teacher_names = []
    for index, row in subject_teacher_mapping.iterrows():
        encrypted_data = row['teacher']
        
        encrypted_data_json = json.loads(encrypted_data)
        final_data = encrypted_data_json['final_data']
        encrypted_aes_key = encrypted_data_json['encrypted_aes_key']
        
        decrypted_name = await call_flask_decrypt_api(final_data, encrypted_aes_key)
        
        decrypted_teacher_names.append(decrypted_name)

    subject_teacher_mapping['teacher'] = decrypted_teacher_names

    return df, subject_teacher_mapping[['subject', 'teacher']]

async def fill_missing_teacher_names(df, prn):
    original_df, subject_teacher_mapping = await fetch_subject_teacher_mapping(prn)
    
    teacher_mapping_dict = subject_teacher_mapping.set_index('subject')['teacher'].to_dict()
    
    # Ensure the column names match when applying the mapping
    df['teacher'] = df.apply(lambda row: teacher_mapping_dict.get(row['subject'], row['teacher']), axis=1)
    
    return df

async def getFinalAttendance(prn):
    engine = get_db_engine()
    query = """
        SELECT prn,
            subject_name,
            teacher_name,
            week_number,
            day_name,
            day_no,
            lecture_type,
            lecture_timing,
            attendance,
            festival,
            CAST(date AS DATE) AS date  -- Converts datetime to date
        FROM psat_final.dbo.vw_student_attendance_details
        WHERE prn = ?
    """
    
    df = pd.read_sql(query, engine, params=(prn,))

    # Rename columns for consistency
    df.rename(columns={"subject_name": "subject", "teacher_name": "teacher"}, inplace=True)

    # Convert attendance (True → 1, False → 0)
    df['attendance'] = df['attendance'].apply(lambda x: 1 if x else 0)

    # Convert festival (True → "TRUE", False → "FALSE")
    df['festival'] = df['festival'].apply(lambda x: 'TRUE' if x else 'FALSE')

    # Convert date format to YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # Convert lecture timing format from HH:MM:SS to HH:MM
    df['lecture_timing'] = pd.to_datetime(df['lecture_timing'], format='%H:%M:%S').dt.strftime('%H:%M')

    # Fill missing teacher names
    updated_df = await fill_missing_teacher_names(df, prn)
    
    # Save the formatted DataFrame to a CSV file
    file_path = f"data/attendance/attendance_dataset.csv"
    updated_df.to_csv(file_path, index=False)  # Save CSV without row index
    
    print(f"Attendance data saved to {file_path}")
    return "Data Loaded!"

async def fetch_unique_prns():
    engine = get_db_engine()
    query = "SELECT DISTINCT student_id FROM psat_final.dbo.student_data"
    df = pd.read_sql(query, engine)
    return df['student_id'].tolist()

async def process_all_students():
    prns = await fetch_unique_prns()
    for prn in prns:
        await getFinalAttendance(prn)

