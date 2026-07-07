from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
import logging
from logging import FileHandler
import os
import tempfile

from auth import authenticate_user, create_default_admin, login_required, register_user, link_user_to_student
from attendance import get_attendance_records, get_today_stats, mark_attendance
from config import Config
from models import init_db
from student import add_student, get_all_students, get_student_by_register_number, remove_student

app = Flask(__name__)
app.config.from_object(Config)

# log errors to a file for easier debugging in environments where console
# output may not be available. The file is written to the project root.
try:
    # Prefer a writable location for logs when running in serverless (Vercel)
    if os.environ.get('VERCEL') or os.environ.get('NOW'):
        log_path = os.environ.get('ERROR_LOG_PATH', os.path.join(tempfile.gettempdir(), 'error.log'))
    else:
        log_path = os.environ.get('ERROR_LOG_PATH', 'error.log')

    file_handler = FileHandler(log_path)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(file_handler)
except Exception:
    # If logging setup fails (e.g., read-only filesystem), continue without file logging
    app.logger.exception('Failed to configure file logging')

try:
    init_db()
except Exception:
    app.logger.exception('Database initialization failed at startup')

# Ensure admin user exists where possible. Log failures but do not crash
try:
    create_default_admin()
except Exception:
    app.logger.exception('Creating default admin failed at startup')

# Attempt to auto-link users to students by username==register_number
try:
    from models import auto_link_users_by_username
    auto_link_users_by_username()
except Exception:
    app.logger.exception('Auto-linking users to students failed at startup')


@app.errorhandler(HTTPException)
def handle_http_error(error):
    if error.code == 404:
        flash('The page you requested was not found.', 'warning')
    else:
        flash('A request error occurred. Please try again.', 'warning')
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.errorhandler(Exception)
def handle_general_error(error):
    app.logger.exception('Unhandled application error')
    flash('Something went wrong. Please try again.', 'danger')
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            # make the session permanent so user stays logged in until they logout
            session.permanent = True
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Please complete all signup details.', 'warning')
        elif register_user(username, password):
            flash('Account created successfully. You can log in now.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists or is invalid.', 'warning')
    return render_template('signup.html')


@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_today_stats()
    recent = get_attendance_records(limit=8)
    return render_template('dashboard.html', stats=stats, recent=recent)


def is_admin_user():
    return session.get('username') == 'admin'


@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    try:
        if request.method == 'POST':
            if not is_admin_user():
                flash('Only the admin account can add or remove students.', 'danger')
                return redirect(url_for('students'))

            action = request.form.get('action')
            if action == 'add':
                name = request.form.get('full_name', '').strip()
                register_number = request.form.get('register_number', '').strip()
                if not name or not register_number:
                    flash('Please complete all student details.', 'warning')
                else:
                    success = add_student(name, register_number)
                    if success:
                        flash('Student added successfully.', 'success')
                    else:
                        flash('This register number already exists.', 'warning')
            elif action == 'delete':
                student_id = request.form.get('student_id')
                if remove_student(student_id):
                    flash('Student removed successfully.', 'success')
                else:
                    flash('Student could not be removed.', 'danger')
        student_list = get_all_students()
        return render_template('students.html', students=student_list)
    except Exception:
        app.logger.exception('Error while processing student request')
        flash('Unable to process student request right now.', 'danger')
        return redirect(url_for('students'))


@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    try:
        if request.method == 'POST':
            status = request.form.get('status')
            # If not admin, force the register number to the logged-in username
            if not is_admin_user():
                register_number = session.get('username', '')
            else:
                register_number = request.form.get('register_number', '').strip()

            if not register_number or status not in {'present', 'absent'}:
                flash('Please enter a valid register number and status.', 'warning')
            else:
                student = get_student_by_register_number(register_number)
                if student:
                    mark_attendance(student['id'], status)
                    flash(f'{student["full_name"]} marked as {status}.', 'success')
                else:
                    if is_admin_user():
                        flash('No student was found with that register number.', 'danger')
                    else:
                        flash('Your account is not linked to a student record.', 'danger')

        stats = get_today_stats()
        records = get_attendance_records(limit=10)
        return render_template('attendance.html', stats=stats, records=records)
    except Exception:
        app.logger.exception('Error while processing attendance request')
        flash('Unable to save attendance right now.', 'danger')
        return redirect(url_for('attendance'))


@app.route('/report')
@login_required
def report():
    records = get_attendance_records(limit=50)
    return render_template('report.html', records=records)


@app.route('/link', methods=['GET', 'POST'])
@login_required
def link():
    if not is_admin_user():
        flash('Only admin can access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        register_number = request.form.get('register_number', '').strip()
        if not username or not register_number:
            flash('Please provide both username and register number.', 'warning')
        else:
            if link_user_to_student(username, register_number):
                flash('User linked to student successfully.', 'success')
            else:
                flash('Could not link user to student. Check values.', 'danger')
    return render_template('link.html')


@app.route('/profile')
@login_required
def profile():
    stats = get_today_stats()
    return render_template('profile.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
