import sqlite3
import time
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = Path(__file__).with_name("users.db")
SQLITE_TIMEOUT = 10  # seconds
MAX_RETRIES = 3      # retry count for locked DB


# ----------------- Connection -----------------
def get_db_connection():
    """Return a sqlite3 connection with WAL mode + timeout."""
    conn = sqlite3.connect(DB_FILE, timeout=SQLITE_TIMEOUT, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # better concurrency
    return conn


def safe_execute(query, params=(), commit=True):
    """Execute a query safely with retries if database is locked."""
    for attempt in range(MAX_RETRIES):
        try:
            with get_db_connection() as conn:
                cur = conn.execute(query, params)
                if commit:
                    conn.commit()
                return cur
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            raise


# ----------------- Init -----------------
def init_db():
    """Create all tables (users, exams, questions, exam_questions, submissions, event_logs)."""
    with get_db_connection() as conn:
        # Users
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                reset_token TEXT,
                reset_expires INTEGER
            )
        """)

        # Exams
        conn.execute("""
           CREATE TABLE IF NOT EXISTS exams (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              description TEXT,
              faculty_id INTEGER,
              date TEXT,
              FOREIGN KEY(faculty_id) REFERENCES users(id)
           )
        """)

        # Coding Questions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                statement TEXT NOT NULL,
                input_format TEXT,
                output_format TEXT,
                sample_tests TEXT,
                hidden_tests TEXT,
                faculty_id INTEGER,
                language TEXT DEFAULT 'python',
                FOREIGN KEY(faculty_id) REFERENCES users(id)
            )
        """)

        # Exam ↔ Question mapping
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                FOREIGN KEY(exam_id) REFERENCES exams(id),
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        """)

        # Submissions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                language TEXT NOT NULL,
                hash TEXT,
                timestamp INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                score INTEGER DEFAULT 0,
                feedback TEXT,
                FOREIGN KEY(student_id) REFERENCES users(id),
                FOREIGN KEY(exam_id) REFERENCES exams(id),
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        """)

        # Event logs
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                exam_id INTEGER,
                event_type TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                content_length INTEGER,
                FOREIGN KEY(student_id) REFERENCES users(id)
            )
        """)

        # ✅ Ensure `language` column exists in questions (migration helper)
        try:
            conn.execute("ALTER TABLE questions ADD COLUMN language TEXT DEFAULT 'python'")
        except sqlite3.OperationalError:
            # Already exists
            pass

        conn.commit()


# ----------------- User Operations -----------------
def insert_user(email, password, role="student", name=None):
    hashed_pw = generate_password_hash(password)
    try:
        safe_execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name or email.split("@")[0], email.lower(), hashed_pw, role)
        )
        return True
    except sqlite3.IntegrityError:
        return False


def check_user(email, password):
    cur = safe_execute(
        "SELECT id, name, email, password, role FROM users WHERE email = ?",
        (email.lower(),),
        commit=False
    )
    row = cur.fetchone()
    if not row:
        return None
    if check_password_hash(row["password"], password):
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"]
        }
    return None


def update_password(email, new_password):
    hashed_pw = generate_password_hash(new_password)
    safe_execute(
        "UPDATE users SET password=? WHERE email=?",
        (hashed_pw, email.lower())
    )
    return True


# ----------------- Exams -----------------
def insert_exam(title, description=None, faculty_id=None, date=None):
    cur = safe_execute(
        "INSERT INTO exams (title, description, faculty_id, date) VALUES (?, ?, ?, ?)",
        (title, description, faculty_id, date)
    )
    return cur.lastrowid  # ✅ Return exam_id directly


def get_exams(faculty_id=None):
    if faculty_id:
        cur = safe_execute("SELECT * FROM exams WHERE faculty_id=? ORDER BY date ASC", (faculty_id,), commit=False)
    else:
        cur = safe_execute("SELECT * FROM exams ORDER BY date ASC", commit=False)
    return [dict(row) for row in cur.fetchall()]


def delete_exam(exam_id):
    safe_execute("DELETE FROM exams WHERE id=?", (exam_id,))


# ----------------- Questions -----------------
def insert_question(title, statement, input_format, output_format, sample_tests, hidden_tests, faculty_id, language="python"):
    safe_execute("""
        INSERT INTO questions (title, statement, input_format, output_format, sample_tests, hidden_tests, faculty_id, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, statement, input_format, output_format, sample_tests, hidden_tests, faculty_id, language))


def get_questions(faculty_id=None):
    if faculty_id:
        cur = safe_execute("SELECT * FROM questions WHERE faculty_id=?", (faculty_id,), commit=False)
    else:
        cur = safe_execute("SELECT * FROM questions", commit=False)
    return [dict(row) for row in cur.fetchall()]


def delete_question(question_id):
    safe_execute("DELETE FROM questions WHERE id=?", (question_id,))


# ----------------- Exam ↔ Question Mapping -----------------
def link_exam_questions(exam_id, question_ids):
    for qid in question_ids:
        safe_execute(
            "INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)",
            (exam_id, qid)
        )


def get_exam_questions(exam_id):
    cur = safe_execute("""
        SELECT q.id,
               q.title,
               q.statement,
               q.input_format,
               q.output_format,
               q.sample_tests,
               q.hidden_tests,
               q.language
        FROM questions q
        JOIN exam_questions eq ON q.id = eq.question_id
        WHERE eq.exam_id = ?
    """, (exam_id,), commit=False)
    return [dict(row) for row in cur.fetchall()]


# ----------------- Submissions -----------------
def insert_submission(exam_id, student_id, question_id, code, language, code_hash, timestamp):
    safe_execute("""
        INSERT INTO submissions (exam_id, student_id, question_id, code, language, hash, timestamp, status, score, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, NULL)
    """, (exam_id, student_id, question_id, code, language, code_hash, timestamp))


def get_results(student_id):
    cur = safe_execute("""
        SELECT exam_id, question_id, status, score, feedback, timestamp
        FROM submissions
        WHERE student_id = ?
        ORDER BY timestamp DESC
    """, (student_id,), commit=False)
    return [dict(row) for row in cur.fetchall()]


def grade_submission(submission_id, score, feedback):
    safe_execute(
        "UPDATE submissions SET status='graded', score=?, feedback=? WHERE id=?",
        (score, feedback, submission_id)
    )


# ----------------- Event Logs -----------------
def insert_event_log(student_id, exam_id, event_type, timestamp=None, content_length=None):
    if not timestamp:
        timestamp = int(time.time())
    safe_execute("""
        INSERT INTO event_logs (student_id, exam_id, event_type, timestamp, content_length)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, exam_id, event_type, timestamp, content_length))


# ----------------- Reset Token Helpers -----------------
def clear_reset_token_by_token(token):
    safe_execute(
        "UPDATE users SET reset_token=NULL, reset_expires=NULL WHERE reset_token=?",
        (token,)
    )


def clear_reset_token_by_email(email):
    safe_execute(
        "UPDATE users SET reset_token=NULL, reset_expires=NULL WHERE email=?",
        (email.lower(),)
    )


if __name__ == "__main__":
    init_db()
    print("✅ DB initialized at", DB_FILE)
