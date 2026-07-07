import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'royal-attendance-secret-key')
    # When deployed to Vercel (serverless), the project root is read-only.
    # Use the writable temporary directory when running under Vercel.
    if os.environ.get('VERCEL') or os.environ.get('NOW'):
        DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/database.db')
    else:
        DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'database.db'))
