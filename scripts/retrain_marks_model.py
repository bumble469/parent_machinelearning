import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import numpy as np

# File Paths
DATA_FILE = os.path.join("data/marks", "realistic_student_data.xlsx")
MODEL_FILE = os.path.join("models/marks", "ridge_model.pkl")
SCALER_FILE = os.path.join("models/marks", "scaler.pkl")

# Ensure directories exist
os.makedirs("models/marks", exist_ok=True)

# Hardcoded maximum marks per semester
MAX_MARKS = {1: 1000, 2: 1000, 3: 1000, 4: 1000, 5: 800, 6: 800}

def train_models(data_path=DATA_FILE):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    
    # Load dataset
    dataset = pd.read_excel(data_path)
    unique_sems = sorted(dataset['current_sem'].unique())

    models = {}
    scalers = {}

    avg_mae_list = []
    avg_r2_list = []

    for sem in unique_sems:
        if sem == 1:
            continue  # Skip Semester 1 since there's no prior data

        print(f'\n Training model for Semester {sem}...')

        sem_data = dataset[dataset['current_sem'] == sem].copy()

        # Calculate percentages instead of total marks
        for s in range(1, sem + 1):
            if f"sem_{s}_marks_total" in sem_data.columns:
                sem_data[f"sem_{s}_marks_percentage"] = (sem_data[f"sem_{s}_marks_total"] / MAX_MARKS[s]) * 100

        # Define Features (Previous Semester Percentages + Current Attendance)
        features = [f'sem_{s}_marks_percentage' for s in range(max(1, sem - 2), sem)]
        features.append(f'sem_{sem}_attendance_perc')

        # Extract Data
        X = sem_data[features]
        y = sem_data[f'sem_{sem}_marks_percentage']

        # Scale Data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train/Test Split (Stratified for better generalization)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Train Model with Cross-Validation & Regularization
        best_alpha = 10  # Increasing regularization to reduce overfitting
        model = Ridge(alpha=best_alpha)

        # 5-Fold Cross-Validation for More Generalized Results
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
        print(f"Cross-Validation R² for Semester {sem}: {np.mean(cv_scores):.2f}")

        # Train the Model
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"MAE for Semester {sem}: {mae:.2f}")
        print(f"R² Score for Semester {sem}: {r2:.2f}")

        # Store results for averaging
        avg_mae_list.append(mae)
        avg_r2_list.append(r2)

        # Save Model and Scaler
        models[sem] = model
        scalers[sem] = scaler

    # Save using Pickle
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(models, f)

    with open(SCALER_FILE, "wb") as f:
        pickle.dump(scalers, f)

    # Compute Average Metrics
    avg_mae = np.mean(avg_mae_list)
    avg_r2 = np.mean(avg_r2_list)

    print("\nTraining Complete: ")
    print(f"Average MAE: {avg_mae:.2f}")
    print(f"Average R² Score: {avg_r2:.2f}")

    return {"message": "Training successful", "semesters": list(models.keys()), "avg_mae": avg_mae, "avg_r2": avg_r2}

if __name__ == "__main__":
    train_models()
