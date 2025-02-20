import pickle
import pandas as pd
import numpy as np
import os

MODEL_FOLDER = os.path.join("models", "attendance")
with open(os.path.join(MODEL_FOLDER, 'le_day.pkl'), 'rb') as f:
    le_day = pickle.load(f)
with open(os.path.join(MODEL_FOLDER, 'le_subject.pkl'), 'rb') as f:
    le_subject = pickle.load(f)
with open(os.path.join(MODEL_FOLDER, 'le_teacher.pkl'), 'rb') as f:
    le_teacher = pickle.load(f)
with open(os.path.join(MODEL_FOLDER, 'le_lecture_type.pkl'), 'rb') as f:
    le_lecture_type = pickle.load(f)
with open(os.path.join(MODEL_FOLDER, 'scaler.pkl'), 'rb') as f:
    scaler = pickle.load(f)
with open(os.path.join(MODEL_FOLDER, 'voting_model.pkl'), 'rb') as model_file:
    voting_model = pickle.load(model_file)

def predict_attendance(week_data, dataset):
    week_df = pd.DataFrame(week_data)
    week_df['day_name'] = le_day.transform(week_df['day_name'])

    flattened_data = []

    # Flatten input data for prediction
    for _, row in week_df.iterrows():
        day = row['day_name']
        prn = row['prn']
        for subject, teacher, lecture_type, timing in zip(row['subject'], row['teacher'], row['lecture_type'], row['lecture_timing']):
            flattened_data.append({
                'prn': prn,
                'subject': subject,
                'teacher': teacher,
                'day_name': day,
                'lecture_type': lecture_type,
                'time_in_minutes': pd.to_datetime(timing, format='%I:%M:%S %p').hour * 60,
                'week_number': row['week_number']
            })

    flattened_df = pd.DataFrame(flattened_data)
    flattened_df['subject'] = le_subject.transform(flattened_df['subject'])
    flattened_df['teacher'] = le_teacher.transform(flattened_df['teacher'])
    flattened_df['lecture_type'] = le_lecture_type.transform(flattened_df['lecture_type'])
    
    # Get attendance trends for each row in the flattened dataset
    def get_attendance_trends(prn, subject, teacher, lecture_type, lecture_timing, max_weeks=5):
        current_week = dataset['week_number'].max()

        trends = dataset[(dataset['prn'] == prn) & 
                        (dataset['subject'] == subject) & 
                        (dataset['teacher'] == teacher) & 
                        (dataset['lecture_type'] == lecture_type) & 
                        (dataset['time_in_minutes'] == lecture_timing) & 
                        (dataset['week_number'] >= current_week - max_weeks)]
        
        if not trends.empty:
            return (
                trends['attendance_percentage_weekly'].mean(),
                trends['attendance_percentage_daily'].mean(),
                trends['lecture_type_attendance_percentage'].mean(),
                trends['lecture_timing_attendance_percentage'].mean(),
                trends['teacher_probability'].mean()
            )
        else:          
            trends_fallback = dataset[(dataset['prn'] == prn) & 
                                    (dataset['subject'] == subject) & 
                                    (dataset['teacher'] == teacher)]
            
            if not trends_fallback.empty:
                return (
                    trends_fallback['attendance_percentage_weekly'].mean(),
                    trends_fallback['attendance_percentage_daily'].mean(),
                    trends_fallback['lecture_type_attendance_percentage'].mean(),
                    trends_fallback['lecture_timing_attendance_percentage'].mean(),
                    trends_fallback['teacher_probability'].mean()
                )
            
            trends_fallback = dataset[(dataset['prn'] == prn) & 
                                    (dataset['subject'] == subject) & 
                                    (dataset['day_name'] == lecture_timing)]
            
            if not trends_fallback.empty:
                return (
                    trends_fallback['attendance_percentage_weekly'].mean(),
                    trends_fallback['attendance_percentage_daily'].mean(),
                    trends_fallback['lecture_type_attendance_percentage'].mean(),
                    trends_fallback['lecture_timing_attendance_percentage'].mean(),
                    trends_fallback['teacher_probability'].mean()
                )

            trends_fallback = dataset[(dataset['prn'] == prn) & 
                                    (dataset['subject'] == subject) & 
                                    (dataset['lecture_type'] == lecture_type)]
            
            if not trends_fallback.empty:
                return (
                    trends_fallback['attendance_percentage_weekly'].mean(),
                    trends_fallback['attendance_percentage_daily'].mean(),
                    trends_fallback['lecture_type_attendance_percentage'].mean(),
                    trends_fallback['lecture_timing_attendance_percentage'].mean(),
                    trends_fallback['teacher_probability'].mean()
                )

            trends_fallback = dataset[(dataset['prn'] == prn) & 
                                    (dataset['subject'] == subject) & 
                                    (dataset['time_in_minutes'] == lecture_timing)]
            
            if not trends_fallback.empty:
                return (
                    trends_fallback['attendance_percentage_weekly'].mean(),
                    trends_fallback['attendance_percentage_daily'].mean(),
                    trends_fallback['lecture_type_attendance_percentage'].mean(),
                    trends_fallback['lecture_timing_attendance_percentage'].mean(),
                    trends_fallback['teacher_probability'].mean()
                )          
            return None, None, 0, 0, 0

    attendance_trends = []
    for _, row in flattened_df.iterrows():
        trends = get_attendance_trends(row['prn'], row['subject'], row['teacher'], row['lecture_type'], row['time_in_minutes'])
        attendance_trends.append(trends)

    (flattened_df['attendance_percentage_weekly'], 
        flattened_df['attendance_percentage_daily'], 
        flattened_df['lecture_type_attendance_percentage'], 
        flattened_df['lecture_timing_attendance_percentage'],
        flattened_df['teacher_probability']) = zip(*attendance_trends)
    
    flattened_df.fillna(flattened_df.mean(), inplace=True)

    features = ['prn', 'subject', 'teacher', 'day_name', 'lecture_type', 
            'time_in_minutes', 'week_number', 'attendance_percentage_weekly', 
            'attendance_percentage_daily', 'teacher_probability', 
            'lecture_type_attendance_percentage', 'lecture_timing_attendance_percentage']
    
    flattened_df_scaled = scaler.transform(flattened_df[features])

    flattened_df['predictions'] = voting_model.predict_proba(flattened_df_scaled)[:, 1]

    flattened_df['weighted_prediction'] = flattened_df.groupby(['day_name'])['predictions'].transform('mean')

    average_predictions = flattened_df.groupby('day_name')['weighted_prediction'].mean().reset_index()

    average_predictions.columns = ['day_name', 'average_prediction']

    average_predictions['day_name'] = le_day.inverse_transform(average_predictions['day_name'])

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    average_predictions['day_order'] = average_predictions['day_name'].apply(lambda x: day_order.index(x))

    average_predictions_sorted = average_predictions.sort_values('day_order')

    average_predictions_sorted = average_predictions_sorted.drop(columns='day_order')

    prn_to_filter = week_df['prn'][0]
    overall_attendance_data = dataset[dataset['prn'] == prn_to_filter]

    # Calculate the current attendance for each subject
    attendance_by_subject = (
        overall_attendance_data.groupby('subject')['attendance']
        .mean()  # Mean of attendance (1 for present, 0 for absent)
        .reset_index()
    )

    attendance_by_subject['attendance_percentage'] = attendance_by_subject['attendance'] * 100
    attendance_by_subject = attendance_by_subject.drop(columns=['attendance'])

    # Decode the subject labels
    attendance_by_subject['subject'] = le_subject.inverse_transform(attendance_by_subject['subject'])

    # Calculate the total number of lectures and the current attended lectures
    attendance_by_subject['total_lectures'] = overall_attendance_data.groupby('subject')['attendance'].count().values
    attendance_by_subject['attended_lectures'] = attendance_by_subject['attendance_percentage'] * attendance_by_subject['total_lectures'] / 100

    # Calculate the new percentage if the student attends the next lecture
    attendance_by_subject['new_percentage_attend'] = (
        (attendance_by_subject['attended_lectures'] + 1) / (attendance_by_subject['total_lectures'] + 1)
    ) * 100

    # Calculate the new percentage if the student misses the next lecture
    attendance_by_subject['new_percentage_miss'] = (
        attendance_by_subject['attended_lectures'] / (attendance_by_subject['total_lectures'] + 1)
    ) * 100

    # Create a result structure to return
    result = {
        "attendance_by_subject": attendance_by_subject[['subject', 'attendance_percentage', 'new_percentage_attend', 'new_percentage_miss']].to_dict(orient='records'),
        "daily_predictions": average_predictions_sorted.to_dict(orient='records')
    }

    return result
