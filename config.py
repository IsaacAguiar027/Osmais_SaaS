import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'troque-essa-chave-em-producao'

    # ── Banco de dados ────────────────────────────────────────
    # Supabase fornece a DATABASE_URL no painel:
    # Project Settings → Database → Connection string → Python
    # Formato: postgresql://postgres:[senha]@db.[projeto].supabase.co:5432/postgres
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    # Supabase usa postgres:// mas SQLAlchemy precisa de postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    # Fallback para SQLite local em desenvolvimento
    if not DATABASE_URL:
        DATABASE_URL = 'sqlite:///' + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'osmais_dev.db'
        )

    SQLALCHEMY_DATABASE_URI     = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Conexões pool para Supabase (PostgreSQL)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping':    True,   # reconecta se cair
        'pool_recycle':     300,    # recicla conexões a cada 5 min
        'pool_size':        5,
        'max_overflow':     10,
        'connect_args': {
            'connect_timeout': 10,
            'options':         '-c timezone=America/Sao_Paulo'
        } if DATABASE_URL.startswith('postgresql') else {}
    }

    # ── Email ─────────────────────────────────────────────────
    MAIL_SERVER        = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT          = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS       = True
    MAIL_USERNAME      = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD      = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    # ── Mercado Pago ──────────────────────────────────────────
    MP_ACCESS_TOKEN    = os.environ.get('MP_ACCESS_TOKEN', '')
    MP_PUBLIC_KEY      = os.environ.get('MP_PUBLIC_KEY', '')
    MP_PRECO_MENSAL    = float(os.environ.get('MP_PRECO_MENSAL',    30.00))
    MP_PRECO_SEMESTRAL = float(os.environ.get('MP_PRECO_SEMESTRAL', 150.00))
    MP_PRECO_ANUAL     = float(os.environ.get('MP_PRECO_ANUAL',    240.00))
    MP_TRIAL_DIAS      = int(os.environ.get('MP_TRIAL_DIAS', 7))
    MP_BASE_URL        = os.environ.get('MP_BASE_URL', 'https://www.systemaos.com.br')


def get_config():
    return Config
