from app import app


def run():
    client = app.test_client()
    with client:
        # Try signup flow
        resp = client.post('/signup', data={'username': 'bob', 'password': 'secret'}, follow_redirects=True)
        print('/signup status:', resp.status_code)
        print(resp.get_data(as_text=True)[:400])

        # Login as admin
        resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        print('Admin login status:', resp.status_code)
        # Add a student
        resp = client.post(
            '/students',
            data={'action': 'add', 'full_name': 'Test Student', 'register_number': 'REG123'},
            follow_redirects=True,
        )
        print('/students add status:', resp.status_code)
        print(resp.get_data(as_text=True)[:1000])

        # Mark attendance for that student
        resp = client.post(
            '/attendance',
            data={'register_number': 'REG123', 'status': 'present'},
            follow_redirects=True,
        )
        print('/attendance mark status:', resp.status_code)
        print(resp.get_data(as_text=True)[:1000])


if __name__ == '__main__':
    run()
