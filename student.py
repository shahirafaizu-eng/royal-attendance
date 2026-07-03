from models import get_db_connection


def get_all_students():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM students ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_student(full_name, register_number):
    conn = get_db_connection()
    existing = conn.execute(
        'SELECT id FROM students WHERE register_number = ?', (register_number,)
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        'INSERT INTO students (full_name, register_number) VALUES (?, ?)',
        (full_name, register_number),
    )
    conn.commit()
    conn.close()
    return True


def remove_student(student_id):
    conn = get_db_connection()
    result = conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    return result.rowcount > 0


def get_student_by_register_number(register_number):
    conn = get_db_connection()
    student = conn.execute(
        'SELECT * FROM students WHERE register_number = ?', (register_number,)
    ).fetchone()
    conn.close()
    return dict(student) if student else None
