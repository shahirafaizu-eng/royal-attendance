import importlib
import os
import sys
import tempfile
import unittest

from auth import authenticate_user, register_user
from config import Config
from models import init_db


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
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


if __name__ == '__main__':
    unittest.main()
