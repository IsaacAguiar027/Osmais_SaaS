import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'osmais-dev-secret-key-2024'

    # Em produção usa PostgreSQL (Railway), em desenvolvimento usa SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'osmais.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
