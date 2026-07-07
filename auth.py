from functools import wraps
from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import get_db_connection


def link_user_to_student(username, register_number):
    """Link a user to a student record by username and student register number.
    Returns True on success, False if user or student not found."""
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        student = conn.execute('SELECT id FROM students WHERE register_number = ?', (register_number,)).fetchone()
        if not user or not student:
            return False
        # Ensure column exists
        try:
            conn.execute('UPDATE users SET student_id = ? WHERE id = ?', (student['id'], user['id']))
            conn.commit()
            return True
        except Exception:
            return False
    finally:
        conn.close()


def register_user(username, password):
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return False

    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return False

    conn.execute(
        'INSERT INTO users (username, password_hash) VALUES (?, ?)',
        (username, generate_password_hash(password)),
    )
    conn.commit()
    conn.close()
    return True


def create_default_admin():
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not existing:
        conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            ('admin', generate_password_hash('admin123')),
        )
        conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped
