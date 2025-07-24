import psycopg2
from config import Config

def get_db_connection():
    try:
        conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
        return conn
    except Exception as e:
        print("Error connecting to the database:", str(e))
        raise
