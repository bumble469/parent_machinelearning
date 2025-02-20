import pandas as pd
import pickle
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score

DATA_FILE = os.path.join("data/attendance", "attendance_dataset.csv")
MODEL_FILE = os.path.join("models/attendance", "voting_model.pkl")
SCALER_FILE = os.path.join("models/attendance", "scaler.pkl")
ENCODERS_PATH = os.path.join("models","attendance")
PROCESSED_DATA_PATH = os.path.join("data/attendance", "processed")

os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

async def train_and_save_model():
    print("Retraining model...")
    retrieved_data = pd.read_csv(DATA_FILE)
    dataset = pd.DataFrame(retrieved_data)
    numerical_cols = dataset.select_dtypes(include=['float64', 'int64']).columns
    dataset[numerical_cols] = dataset[numerical_cols].fillna(dataset[numerical_cols].mean())

    categorical_cols = dataset.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        dataset[col] = dataset[col].fillna(dataset[col].mode()[0])

    dataset['date'] = pd.to_datetime(dataset['date'])
    dataset['weekday'] = dataset['date'].dt.day_name()
    dataset['attendance_percentage'] = dataset['attendance'] * 100

    weekly_attendance = dataset.groupby(['prn', 'subject', 'week_number'])['attendance_percentage'].mean().reset_index()
    weekly_attendance.rename(columns={'attendance_percentage': 'attendance_percentage_weekly'}, inplace=True)

    daywise_attendance = dataset.groupby(['prn', 'weekday'])['attendance_percentage'].mean().reset_index()
    daywise_attendance.rename(columns={'attendance_percentage': 'attendance_percentage_daily'}, inplace=True)

    lecture_type_attendance = dataset.groupby(['prn', 'lecture_type'])['attendance_percentage'].mean().reset_index()
    lecture_type_attendance.rename(columns={'attendance_percentage': 'lecture_type_attendance_percentage'}, inplace=True)

    lecture_timing_attendance = dataset.groupby(['prn', 'lecture_timing'])['attendance_percentage'].mean().reset_index()
    lecture_timing_attendance.rename(columns={'attendance_percentage': 'lecture_timing_attendance_percentage'}, inplace=True)

    if 'attendance_percentage_weekly' in dataset.columns:
        dataset.drop(columns=['attendance_percentage_weekly'], inplace=True)
    dataset = dataset.merge(weekly_attendance, on=['prn', 'subject', 'week_number'], how='left')

    if 'attendance_percentage_daily' in dataset.columns:
        dataset.drop(columns=['attendance_percentage_daily'], inplace=True)
    dataset = dataset.merge(daywise_attendance, on=['prn', 'weekday'], how='left')

    if 'lecture_type_attendance_percentage' in dataset.columns:
        dataset.drop(columns=['lecture_type_attendance_percentage'], inplace=True)
    dataset = dataset.merge(lecture_type_attendance, on=['prn', 'lecture_type'], how='left')

    if 'lecture_timing_attendance_percentage' in dataset.columns:
        dataset.drop(columns=['lecture_timing_attendance_percentage'], inplace=True)
    dataset = dataset.merge(lecture_timing_attendance, on=['prn', 'lecture_timing'], how='left')

    teacher_probability = dataset.groupby(['teacher', 'subject'])['attendance_percentage'].mean().reset_index()
    teacher_probability.rename(columns={'attendance_percentage': 'teacher_probability'}, inplace=True)

    if 'teacher_probability' in dataset.columns:
        dataset.drop(columns=['teacher_probability'], inplace=True)
    dataset = dataset.merge(teacher_probability, on=['teacher', 'subject'], how='left')

    le_subject = LabelEncoder()
    le_teacher = LabelEncoder()
    le_day = LabelEncoder()
    le_lecture_type = LabelEncoder()
    le_festival = LabelEncoder()

    dataset['subject'] = le_subject.fit_transform(dataset['subject'])
    dataset['teacher'] = le_teacher.fit_transform(dataset['teacher'])
    dataset['day_name'] = le_day.fit_transform(dataset['day_name'])
    dataset['lecture_type'] = le_lecture_type.fit_transform(dataset['lecture_type'])
    dataset['festival'] = le_festival.fit_transform(dataset['festival'])

    with open(os.path.join(ENCODERS_PATH, 'le_subject.pkl'), 'wb') as f:
        pickle.dump(le_subject, f)
    with open(os.path.join(ENCODERS_PATH, 'le_teacher.pkl'), 'wb') as f:
        pickle.dump(le_teacher, f)
    with open(os.path.join(ENCODERS_PATH, 'le_day.pkl'), 'wb') as f:
        pickle.dump(le_day, f)
    with open(os.path.join(ENCODERS_PATH, 'le_lecture_type.pkl'), 'wb') as f:
        pickle.dump(le_lecture_type, f)
    with open(os.path.join(ENCODERS_PATH, 'le_festival.pkl'), 'wb') as f:
        pickle.dump(le_festival, f)

    dataset['lecture_timing'] = pd.to_datetime(dataset['lecture_timing'], format='%H:%M')
    dataset['time_in_minutes'] = dataset['lecture_timing'].dt.hour * 60 + dataset['lecture_timing'].dt.minute

    features = ['prn', 'subject', 'teacher', 'day_name', 'lecture_type',
                'time_in_minutes', 'week_number', 'attendance_percentage_weekly',
                'attendance_percentage_daily', 'teacher_probability', 
                'lecture_type_attendance_percentage', 'lecture_timing_attendance_percentage']
    target = 'attendance'

    X = dataset[features]
    y = dataset[target]

    dataset.dropna(inplace=True)
    dataset.to_csv(os.path.join(PROCESSED_DATA_PATH, "processed_attendance_dataset.csv"), index=False)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    dt_model = DecisionTreeClassifier(criterion='entropy', min_samples_split=5, min_samples_leaf=2, random_state=42)

    param_grid_dt = {
        'max_depth': [5, 10, 20],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 5]
    }

    grid_search_dt = GridSearchCV(dt_model, param_grid_dt, cv=5, n_jobs=-1, scoring='accuracy')
    grid_search_dt.fit(X_train_scaled, y_train)

    best_dt = grid_search_dt.best_estimator_
    print("Best Decision Tree Parameters:", grid_search_dt.best_params_)

    y_pred_dt = best_dt.predict(X_test_scaled)
    accuracy_dt = accuracy_score(y_test, y_pred_dt)
    print(f"Decision Tree Test Accuracy: {accuracy_dt:.4f}")

    log_reg = LogisticRegression(penalty='l2', solver='liblinear', random_state=42)

    param_grid_log = {
        'C': [0.1, 1, 10],
        'solver': ['liblinear', 'saga'] 
    }

    grid_search_log = GridSearchCV(log_reg, param_grid_log, cv=5, n_jobs=-1, scoring='accuracy')
    grid_search_log.fit(X_train_scaled, y_train)

    best_log_reg = grid_search_log.best_estimator_
    print("Best Logistic Regression Parameters:", grid_search_log.best_params_)

    y_pred_log = best_log_reg.predict(X_test_scaled)
    accuracy_log = accuracy_score(y_test, y_pred_log)
    print(f"Logistic Regression Test Accuracy: {accuracy_log:.4f}")

    voting_clf = VotingClassifier(
        estimators=[('dt', best_dt), ('log_reg', best_log_reg)],
        voting='soft'
    )

    voting_clf.fit(X_train_scaled, y_train)

    y_pred_voting = voting_clf.predict(X_test_scaled)
    accuracy_voting = accuracy_score(y_test, y_pred_voting)
    print(f"Voting Classifier Test Accuracy: {accuracy_voting:.4f}")

    with open(MODEL_FILE, 'wb') as model_file:
        pickle.dump(voting_clf, model_file)

    with open(SCALER_FILE, 'wb') as scaler_file:
        pickle.dump(scaler, scaler_file)

    for name, encoder in zip(['le_day', 'le_subject', 'le_teacher', 'le_lecture_type','le_festival'], 
                         [le_day, le_subject, le_teacher, le_lecture_type, le_festival]):
        with open(os.path.join(ENCODERS_PATH, f"{name}.pkl"), 'wb') as f:
            pickle.dump(encoder, f)


