import os


class Config:
    SECRET_KEY = 'royal-attendance-secret-key'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
