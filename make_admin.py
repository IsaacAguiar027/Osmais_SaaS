"""
Uso: python make_admin.py email@exemplo.com
Torna um usuário existente administrador do sistema.
"""
import sys
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    if len(sys.argv) < 2:
        print("Uso: python make_admin.py email@exemplo.com")
        sys.exit(1)

    email = sys.argv[1]
    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario:
        print(f"Usuário com email '{email}' não encontrado.")
        sys.exit(1)

    usuario.is_admin = True
    db.session.commit()
    print(f"✅ '{usuario.nome}' ({email}) agora é administrador!")
