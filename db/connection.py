import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={os.getenv('DB_DRIVER')};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_DATABASE')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            f"TrustServerCertificate=yes;"
        )
        print('Connected to the database!')

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        if row:
            print("Database connection is successful!")
        
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

def get_db_engine():
    try:
        engine = create_engine(
            f"mssql+pyodbc://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}?"
            f"driver={os.getenv('DB_DRIVER').replace(' ', '+')}&TrustServerCertificate=yes",
            fast_executemany=True
        )
        print("SQLAlchemy Engine created successfully!")
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        raise
