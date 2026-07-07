from datetime import datetime

from models import get_db_connection


def mark_attendance(student_id, status):
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    marked_at = datetime.now().strftime('%H:%M:%S')
    conn.execute(
        'INSERT INTO attendance (student_id, attendance_date, status, marked_at) VALUES (?, ?, ?, ?)',
        (student_id, today, status, marked_at),
    )
    conn.commit()
    conn.close()


def get_today_stats():
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    present = conn.execute(
        'SELECT COUNT(*) as count FROM attendance WHERE attendance_date = ? AND status = ?',
        (today, 'present'),
    ).fetchone()[0]
    absent = conn.execute(
        'SELECT COUNT(*) as count FROM attendance WHERE attendance_date = ? AND status = ?',
        (today, 'absent'),
    ).fetchone()[0]
    total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()[0]
    conn.close()
    return {'present': present, 'absent': absent, 'total_students': total_students}


def get_attendance_records(limit=20):
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT a.id, a.attendance_date, a.status, a.marked_at, s.full_name, s.register_number
        FROM attendance a
        LEFT JOIN students s ON s.id = a.student_id
        ORDER BY a.id DESC
        LIMIT ?
        ''',
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
