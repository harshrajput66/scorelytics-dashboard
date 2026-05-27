import sqlite3
import os
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_performance.db")

def get_connection():
    """Establishes a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id   TEXT PRIMARY KEY,
        name         TEXT NOT NULL,
        class_level  TEXT NOT NULL CHECK(class_level IN ('Class 11', 'Class 12')),
        stream       TEXT NOT NULL CHECK(stream IN ('Medical', 'Non-Medical', 'Commerce', 'Arts')),
        email        TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_records (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id           TEXT    NOT NULL,
        subject              TEXT    NOT NULL,
        score                REAL    NOT NULL,
        attendance_rate      REAL    NOT NULL,
        study_hours_per_week REAL    NOT NULL,
        parental_involvement TEXT    CHECK(parental_involvement IN ('Low', 'Medium', 'High')),
        extracurricular      TEXT    CHECK(extracurricular IN ('Yes', 'No')),
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def reset_db():
    """Resets the database by dropping and recreating tables."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS performance_records")
    cursor.execute("DROP TABLE IF EXISTS students")
    conn.commit()
    conn.close()
    init_db()

def insert_students_bulk(students_list):
    """
    Inserts students in bulk.
    students_list: List of tuples (student_id, name, class_level, stream, email)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO students (student_id, name, class_level, stream, email) "
        "VALUES (?, ?, ?, ?, ?)",
        students_list
    )
    conn.commit()
    conn.close()

def insert_performance_records_bulk(records_list):
    """
    Inserts performance records in bulk.
    records_list: List of tuples
      (student_id, subject, score, attendance_rate, study_hours_per_week, parental_involvement, extracurricular)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO performance_records
        (student_id, subject, score, attendance_rate, study_hours_per_week, parental_involvement, extracurricular)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        records_list
    )
    conn.commit()
    conn.close()

def get_students_df():
    """Retrieves all students as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

def get_performance_df():
    """Retrieves all performance records joined with student metadata."""
    conn = get_connection()
    query = """
    SELECT
        p.id,
        p.student_id,
        s.name,
        s.class_level,
        s.stream,
        s.email,
        p.subject,
        p.score,
        p.attendance_rate,
        p.study_hours_per_week,
        p.parental_involvement,
        p.extracurricular
    FROM performance_records p
    JOIN students s ON p.student_id = s.student_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_student_details(student_id):
    """
    Retrieves a student's profile and performance records.
    Returns: (student_info_dict, performance_df)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, None

    student_info = dict(row)

    query = """
    SELECT subject, score, attendance_rate, study_hours_per_week, parental_involvement, extracurricular
    FROM performance_records
    WHERE student_id = ?
    """
    performance_df = pd.read_sql_query(query, conn, params=(student_id,))
    conn.close()

    return student_info, performance_df

def execute_custom_query(query, params=None):
    """
    Executes a user-provided SQL query.
    SELECT → returns DataFrame; others → executes and returns status message.
    """
    conn = get_connection()
    try:
        is_select = query.strip().lower().startswith("select")
        if is_select:
            df = pd.read_sql_query(query, conn, params=params)
            return {"type": "select", "data": df}
        else:
            cursor = conn.cursor()
            cursor.execute(query, params) if params else cursor.execute(query)
            conn.commit()
            return {"type": "write", "data": f"Query executed successfully. Rows affected: {conn.total_changes}"}
    except Exception as e:
        return {"type": "error", "data": str(e)}
    finally:
        conn.close()
