import os
import app as app_module
from config import Config
from models import init_db

Config.DATABASE_PATH = 'tmp_repro.db'
if os.path.exists(Config.DATABASE_PATH):
    os.remove(Config.DATABASE_PATH)
init_db()
app_module.init_db()
app_module.create_default_admin()
client = app_module.app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
resp = client.post('/students', data={'action': 'add', 'full_name': 'Test', 'register_number': '123'}, follow_redirects=True)
print(resp.status_code)
print(resp.get_data(as_text=True))
