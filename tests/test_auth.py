import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from auth import authenticate_user, register_user
from config import Config
from models import init_db


class AuthTests(unittest.TestCase):
    def setUp(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        self.temp_db = temp_file.name
        Config.DATABASE_PATH = self.temp_db
        init_db()
        sys.modules.pop('app', None)
        self.app_module = importlib.import_module('app')
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        sys.modules.pop('app', None)

    def test_register_and_authenticate_user(self):
        self.assertTrue(register_user('alice', 'pass123'))
        self.assertFalse(register_user('alice', 'otherpass'))

        user = authenticate_user('alice', 'pass123')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'alice')

    def test_admin_account_is_created_for_admin_login(self):
        user = authenticate_user('admin', 'admin123')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'admin')

    def test_student_errors_show_safe_message(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'

        with patch('app.add_student', side_effect=Exception('boom')):
            response = self.client.post(
                '/students',
                data={'action': 'add', 'full_name': 'Test', 'register_number': '123'},
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Unable to process student request right now.', response.get_data(as_text=True))

    def test_attendance_errors_show_safe_message(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'

        response = self.client.post(
            '/attendance',
            data={'register_number': 'missing', 'status': 'present'},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('No student was found with that register number.', response.get_data(as_text=True))

    def test_init_db_adds_missing_student_columns_for_older_database(self):
        conn = sqlite3.connect(self.temp_db)
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        conn.commit()
        conn.close()

        init_db()

        conn = sqlite3.connect(self.temp_db)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(students)")]
        conn.close()

        self.assertIn('register_number', columns)


if __name__ == '__main__':
    unittest.main()
