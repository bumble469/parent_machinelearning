import pymssql
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "1433")

def get_db_connection():
    """Creates a direct connection using pymssql."""
    try:
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            port=int(DB_PORT)
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
    """Creates an SQLAlchemy engine using pymssql."""
    try:
        engine = create_engine(
            f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_DATABASE}"
        )
        print("✅ SQLAlchemy Engine created successfully!")
        return engine
    except Exception as e:
        print(f"❌ Error creating SQLAlchemy engine: {e}")
        raise
