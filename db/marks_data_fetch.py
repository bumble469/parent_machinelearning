import pickle
import pandas as pd
import os
import asyncio
from db.connection import get_db_engine  
from db.utils.flask_security import call_flask_decrypt_api
import json

MODEL_FOLDER = os.path.join('models/marks')

# Load models and scaler for different semesters
with open(os.path.join(MODEL_FOLDER, 'linear_model.pkl'), 'rb') as f:
    loaded_model = pickle.load(f)

with open(os.path.join(MODEL_FOLDER, 'scaler.pkl'), 'rb') as f:
    scaler = pickle.load(f)

async def fetch_student_data(prn):
    engine = get_db_engine()
    
    query = """
        SELECT prn,
            student_full_name,
            current_sem,
            sem_1_attendance_perc,
            sem_1_marks_total,
            sem_1_obtainable_total,
            sem_2_attendance_perc,
            sem_2_marks_total,
            sem_2_obtainable_total,
            sem_3_attendance_perc,
            sem_3_marks_total,
            sem_3_obtainable_total,
            sem_4_attendance_perc,
            sem_4_marks_total,
            sem_4_obtainable_total,
            sem_5_attendance_perc,
            sem_5_marks_total,
            sem_5_obtainable_total,
            sem_6_attendance_perc,
            sem_6_marks_total,
            sem_6_obtainable_total
        FROM psat_final.dbo.student_academic_summary
        WHERE prn = ?
    """

    df = await asyncio.to_thread(pd.read_sql, query, engine, params=(prn,))
    
    if 'student_full_name' in df.columns and not df.empty:
        encrypted_info = df['student_full_name'].iloc[0]
        
        decrypted_data = json.loads(encrypted_info)
        
        encrypted_data = decrypted_data['final_data']
        encrypted_aes_key = decrypted_data['encrypted_aes_key']
        
        decrypted_name = await call_flask_decrypt_api(encrypted_data, encrypted_aes_key)
        
        df['student_full_name'] = decrypted_name
    
    for sem in range(1, 7):
        marks_col = f'sem_{sem}_marks_total'
        obtainable_col = f'sem_{sem}_obtainable_total'
        perc_col = f'sem_{sem}_marks_percentage'
        
        if marks_col in df.columns and obtainable_col in df.columns:
            df[perc_col] = (df[marks_col] / df[obtainable_col]) * 100

    return df


