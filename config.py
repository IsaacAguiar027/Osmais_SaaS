import os

class Config:
    # Chave secreta para sessões (troque em produção!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'osmais-dev-secret-key-2024'

    # Banco de dados SQLite (arquivo local, perfeito para começar)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'osmais.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email (esqueceu a senha)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
