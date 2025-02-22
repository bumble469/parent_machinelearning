from quart import Quart, jsonify, request
from quart_cors import cors
import os
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from db.utils.flask_security import wake_up_flask_api
from services.marks_predictions import predict_marks
from db.marks_data_fetch import fetch_student_data
from services.attendance_predictions import predict_attendance
from db.attendance_data_fetch import process_all_students
from db.attendance_timetable_fetch import fetch_latest_timetable
from scripts.retrain_attendance_model import train_and_save_model
import uvicorn

app = Quart(__name__)
app = cors(app, allow_origin=["http://localhost:3000"])

DATA_FILE = os.path.join("data", "attendance", "processed", "processed_attendance_dataset.csv")

if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE, na_values=['NaN', '?', ''])
else:
    data = pd.DataFrame()  

@app.route('/predict-marks', methods=['POST'])
async def predict_marks_api():
    try:
        await wake_up_flask_api()
        input_data = await request.get_json()
        prn = input_data.get("prn")

        if not prn:
            return jsonify({"error": "No PRN provided"}), 400

        student_data = await fetch_student_data(prn)

        if student_data.empty:
            return jsonify({"error": "Student data not found"}), 404

        input_data = student_data.to_dict(orient="records")[0]
        predictions = predict_marks(input_data)

        return jsonify(predictions)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/predict-attendance', methods=['POST'])
async def predict_attendance_api():
    try:
        await wake_up_flask_api()
        input_data = await request.get_json()
        prn = input_data.get("prn")
        
        if not prn:
            return jsonify({"error": "PRN is required"}), 400

        week_data = await fetch_latest_timetable(prn)

        if not week_data:
            return jsonify({"error": "No timetable data found for this PRN"}), 404

        predictions = predict_attendance(week_data, data)

        if isinstance(predictions, dict):
            return jsonify(predictions), 200
        
        predictions_json = predictions.to_dict(orient='records')
        return jsonify(predictions_json), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


async def schedule_attendance_processing():
    await process_all_students()  
    await train_and_save_model()  

def run_scheduled_task():
    asyncio.run(schedule_attendance_processing())  

scheduler = BackgroundScheduler()
scheduler.add_job(run_scheduled_task, "interval", weeks=5)  
scheduler.start()

# if __name__ == '__main__':
#     uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)