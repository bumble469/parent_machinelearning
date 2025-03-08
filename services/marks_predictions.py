import pickle
import numpy as np
import pandas as pd
import os
MODEL_FOLDER = os.path.join('models/marks')

with open(os.path.join(MODEL_FOLDER, 'linear_model.pkl'), 'rb') as f:
    loaded_model = pickle.load(f)

with open(os.path.join(MODEL_FOLDER, 'scaler.pkl'), 'rb') as f:
    scaler = pickle.load(f)

def predict_marks(input_data):
    try:
        latest_sem = input_data.get("current_sem")
        if latest_sem is None:
            return {"error": "Missing current_sem in input data"}

        total_obtainable_marks = {
            sem: input_data.get(f"sem_{sem}_obtainable_total", 1000) or 1000
            for sem in range(1, 7)
        }

        if latest_sem not in total_obtainable_marks:
            return {"error": f"Total obtainable marks for Semester {latest_sem} is missing"}

        input_features = []
        feature_names = []

        for s in range(max(1, latest_sem - 2), latest_sem):
            feature_marks = input_data.get(f"sem_{s}_marks_percentage", 50)
            input_features.append(feature_marks)
            feature_names.append(f"sem_{s}_marks_percentage")

        attendance_perc = input_data.get(f"sem_{latest_sem}_attendance_perc", 50)
        input_features.append(attendance_perc)
        feature_names.append(f"sem_{latest_sem}_attendance_perc")

        input_features = np.array([input_features])

        if latest_sem in loaded_model and latest_sem in scaler:
            model = loaded_model[latest_sem]
            scale = scaler[latest_sem]

            input_features_df = pd.DataFrame(input_features, columns=feature_names)
            input_features_scaled = scale.transform(input_features_df)

            predicted_marks = model.predict(input_features_scaled)[0]
            
            final_predicted_marks = (predicted_marks / 100) * total_obtainable_marks[latest_sem]
            final_predicted_marks = max(0, min(int(round(final_predicted_marks)), total_obtainable_marks[latest_sem]))

            predicted_perc = (final_predicted_marks / total_obtainable_marks[latest_sem]) * 100

            grade_thresholds = {
                "O": 80, "A+": 70, "A": 60, "B+": 55, "B": 50, "C": 45, "D": 40, "F": 0
            }

            def get_grade_range(percentage):
                for grade, threshold in grade_thresholds.items():
                    if percentage >= threshold:
                        return grade
                return "F"

            predicted_grade_range = get_grade_range(predicted_perc)

            def get_previous_sem_data(semester):
                if semester < 1:
                    return {"perc": "N/A", "marks": "N/A", "total_obtainable": "N/A", "grade": "N/A"}
                marks = input_data.get(f"sem_{semester}_marks_total", 0)
                total_marks = total_obtainable_marks.get(semester, 1000)
                perc = (marks / total_marks) * 100 if total_marks else 0
                grade = get_grade_range(perc)
                return {"perc": round(perc, 2), "marks": marks, "total_obtainable": total_marks, "grade": grade}

            prev_sem1 = get_previous_sem_data(latest_sem - 1)
            prev_sem2 = get_previous_sem_data(latest_sem - 2)

            return {
                "latest_sem": latest_sem,
                "current_attendance_perc": attendance_perc,
                "predicted_perc": round(predicted_perc, 2),
                "predicted_grade_range": predicted_grade_range,
                "prev_sem1_marks": prev_sem1["marks"],
                "prev_sem1_total_obtainable": prev_sem1["total_obtainable"],
                "prev_sem1_perc": round((prev_sem1["marks"] / prev_sem1["total_obtainable"]) * 100, 2) if prev_sem1["total_obtainable"] > 0 else None,
                "prev_sem1_grade": prev_sem1["grade"],
                "prev_sem2_marks": prev_sem2["marks"],
                "prev_sem2_total_obtainable": prev_sem2["total_obtainable"],
                "prev_sem2_perc": round((prev_sem2["marks"] / prev_sem2["total_obtainable"]) * 100, 2) if prev_sem2["total_obtainable"] > 0 else None,
                "prev_sem2_grade": prev_sem2["grade"]
            }

        else:
            return {"error": f"No trained model or scaler found for Semester {latest_sem}."}
    except Exception as e:
        return {"error": str(e)}
