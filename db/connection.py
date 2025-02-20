import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ✅ Ensure the driver has proper spacing
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server").replace(" ", "+")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "1433")  # Default to 1433 if not set

def get_db_connection():
    """Creates a direct connection using pyodbc."""
    try:
        conn = pyodbc.connect(
            f"DRIVER={{{DB_DRIVER}}};"
            f"SERVER={DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
        print("✅ Connected to the database!")

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        if row:
            print("✅ Database connection is successful!")
        
        return conn
    except Exception as e:
        print(f"❌ Error connecting to the database: {e}")
        raise


def get_db_engine():
    """Creates an SQLAlchemy engine for ORM-based queries."""
    try:
        engine = create_engine(
            f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_DATABASE}"
            f"?driver={DB_DRIVER}&TrustServerCertificate=yes",
            fast_executemany=True
        )
        print("✅ SQLAlchemy Engine created successfully!")
        return engine
    except Exception as e:
        print(f"❌ Error creating SQLAlchemy engine: {e}")
        raise
