import sqlite3

from config import Config


def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_has_column(conn, table_name, column_name):
    columns = [row[1] for row in conn.execute(f'PRAGMA table_info({table_name})')]
    return column_name in columns


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            register_number TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    if not _table_has_column(conn, 'students', 'register_number'):
        conn.execute('ALTER TABLE students ADD COLUMN register_number TEXT')
    if not _table_has_column(conn, 'students', 'created_at'):
        conn.execute('ALTER TABLE students ADD COLUMN created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP')

    try:
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_students_register_number ON students(register_number)')
    except sqlite3.IntegrityError:
        pass

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        '''
    )
    # Ensure users table has a student_id column to link users to students
    if not _table_has_column(conn, 'users', 'student_id'):
        try:
            conn.execute('ALTER TABLE users ADD COLUMN student_id INTEGER')
        except Exception:
            # Some SQLite versions or states may not allow ALTER; ignore
            pass
    conn.commit()
    conn.close()


def auto_link_users_by_username():
    """Link users to student records where username == register_number."""
    conn = get_db_connection()
    try:
        # Only proceed if student_id column exists
        if _table_has_column(conn, 'users', 'student_id'):
            rows = conn.execute('SELECT id, username FROM users').fetchall()
            for r in rows:
                user_id = r['id']
                username = r['username']
                student = conn.execute('SELECT id FROM students WHERE register_number = ?', (username,)).fetchone()
                if student:
                    conn.execute('UPDATE users SET student_id = ? WHERE id = ?', (student['id'], user_id))
            conn.commit()
    finally:
        conn.close()
