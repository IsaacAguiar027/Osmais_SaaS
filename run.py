import os

# Carrega o .env ANTES de qualquer import do Flask
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ[key.strip()] = value.strip()
    print(f'[.env] Carregado: MAIL_USERNAME={os.environ.get("MAIL_USERNAME")}')
else:
    print('[.env] Arquivo não encontrado!')

from app import create_app, db
from app.models import Usuario
import sqlalchemy as sa

app = create_app()

# Setup inicial — roda uma vez e não faz nada nas próximas
with app.app_context():
    # Garante colunas novas no banco de produção
    with db.engine.connect() as conn:
        for col in [
            "ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0",
            "ALTER TABLE usuarios ADD COLUMN nome_loja VARCHAR(100) DEFAULT 'Minha Assistencia'",
            "ALTER TABLE usuarios ADD COLUMN plano VARCHAR(20) DEFAULT 'trial'",
            "ALTER TABLE usuarios ADD COLUMN trial_expira_em DATETIME",
            "ALTER TABLE usuarios ADD COLUMN assinatura_expira_em DATETIME",
            "ALTER TABLE usuarios ADD COLUMN mp_payment_id VARCHAR(100)",
            "ALTER TABLE ordens ADD COLUMN servico_realizado TEXT",
            "ALTER TABLE ordens ADD COLUMN valor_peca FLOAT DEFAULT 0.0",
            "ALTER TABLE ordens ADD COLUMN valor_mao_obra FLOAT DEFAULT 0.0",
        ]:
            try:
                conn.execute(sa.text(col))
            except:
                pass
        conn.commit()

    # Define admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    if ADMIN_EMAIL:
        u = Usuario.query.filter_by(email=ADMIN_EMAIL).first()
        if u and not u.is_admin:
            u.is_admin = True
            db.session.commit()
            print(f'[ADMIN] {ADMIN_EMAIL} definido como admin.')

if __name__ == '__main__':
    app.run(debug=True)
