from app import app
app.testing = True
client = app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'

resp = client.post('/students', data={'action': 'add', 'full_name': 'Test', 'register_number': '123'}, follow_redirects=True)
print('students', resp.status_code)
print(resp.get_data(as_text=True))

resp2 = client.post('/attendance', data={'register_number': '123', 'status': 'present'}, follow_redirects=True)
print('attendance', resp2.status_code)
print(resp2.get_data(as_text=True))
