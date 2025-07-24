import os
from apps.utils.db import get_db_connection


def initialize_db():
    schema_path = os.path.join(os.path.dirname(__file__), ".../models/schema.sql")

    with open(schema_path, "r") as f:
        schema = f.read()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(schema)
    conn.commit()
    cur.close()
    conn.close()

    print("Database initialized successfully.")

if __name__ == "__main__":
    initialize_db()
