import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'osmais-dev-secret-key-2024'

    # Lógica do banco:
    # 1. Se tiver DATABASE_URL (PostgreSQL) usa ele
    # 2. Se estiver no Railway (tem volume /data) usa /data/osmais.db
    # 3. Senão usa SQLite local (desenvolvimento)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif os.path.isdir('/data'):
        # Volume do Railway
        SQLALCHEMY_DATABASE_URI = 'sqlite:////data/osmais.db'
    else:
        # Desenvolvimento local
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'osmais.db'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
