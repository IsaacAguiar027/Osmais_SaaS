import os
from dotenv import load_dotenv

# Carrega .env (desenvolvimento local). No Railway as vars vêm do ambiente.
load_dotenv()

from app import create_app, db
from app.models import Usuario
import sqlalchemy as sa

app = create_app()

# Migrações seguras — adiciona colunas novas sem quebrar o banco existente
_MIGRATIONS = [
    "ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0",
    "ALTER TABLE usuarios ADD COLUMN nome_loja VARCHAR(100) DEFAULT 'Minha Assistencia'",
    "ALTER TABLE usuarios ADD COLUMN plano VARCHAR(20) DEFAULT 'trial'",
    "ALTER TABLE usuarios ADD COLUMN trial_expira_em DATETIME",
    "ALTER TABLE usuarios ADD COLUMN assinatura_expira_em DATETIME",
    "ALTER TABLE usuarios ADD COLUMN mp_payment_id VARCHAR(100)",
    "ALTER TABLE ordens ADD COLUMN servico_realizado TEXT",
    "ALTER TABLE ordens ADD COLUMN valor_peca FLOAT DEFAULT 0.0",
    "ALTER TABLE ordens ADD COLUMN valor_mao_obra FLOAT DEFAULT 0.0",
    "ALTER TABLE ordens ADD COLUMN garantia_dias INTEGER DEFAULT 0",
]

with app.app_context():
    db.create_all()

    with db.engine.connect() as conn:
        for col_sql in _MIGRATIONS:
            try:
                conn.execute(sa.text(col_sql))
            except Exception:
                pass  # coluna já existe — ignorar
        conn.commit()

    # Promove admin via variável de ambiente ADMIN_EMAIL
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    if ADMIN_EMAIL:
        u = Usuario.query.filter_by(email=ADMIN_EMAIL).first()
        if u and not u.is_admin:
            u.is_admin = True
            db.session.commit()
            print(f'[ADMIN] {ADMIN_EMAIL} definido como admin.')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
