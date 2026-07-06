from flask import Flask, flash, redirect, render_template, request, session, url_for

from auth import authenticate_user, create_default_admin, login_required, register_user
from attendance import get_attendance_records, get_today_stats, mark_attendance
from config import Config
from models import init_db
from student import add_student, get_all_students, get_student_by_register_number, remove_student

app = Flask(__name__)
app.config.from_object(Config)

init_db()
create_default_admin()


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
            flash('Account created successfully. Please log in.', 'success')
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


@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    if request.method == 'POST':
        register_number = request.form.get('register_number', '').strip()
        status = request.form.get('status')
        if not register_number or status not in {'present', 'absent'}:
            flash('Please enter a valid register number and status.', 'warning')
        else:
            student = get_student_by_register_number(register_number)
            if student:
                mark_attendance(student['id'], status)
                flash(f'{student["full_name"]} marked as {status}.', 'success')
            else:
                flash('No student was found with that register number.', 'danger')

    stats = get_today_stats()
    records = get_attendance_records(limit=10)
    return render_template('attendance.html', stats=stats, records=records)


@app.route('/report')
@login_required
def report():
    records = get_attendance_records(limit=50)
    return render_template('report.html', records=records)


@app.route('/profile')
@login_required
def profile():
    stats = get_today_stats()
    return render_template('profile.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
