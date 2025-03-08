import pymssql
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "1433")

def get_db_connection():
    try:
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            port=int(DB_PORT),
            login_timeout=10, 
        )
        logger.info("Connected to the database successfully!")
        return conn
    except pymssql.InterfaceError as e:
        logger.error("Database connection failed due to network issues or incorrect credentials.")
        raise
    except pymssql.DatabaseError as e:
        logger.error("Database error occurred: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error connecting to the database: %s", e)
        raise

def get_db_engine():
    try:
        engine = create_engine(
            f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_DATABASE}",
            pool_size=20,         
            max_overflow=10,      
            pool_timeout=30,      
            pool_recycle=1800, 
        )
        logger.info("SQLAlchemy Engine created successfully with connection pooling!")
        return engine
    except Exception as e:
        logger.error("Error creating SQLAlchemy engine: %s", e)
        raise
