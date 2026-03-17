from app import create_app, db
import sqlalchemy as sa

app = create_app()

with app.app_context():
    # Migrações
    with db.engine.connect() as conn:
        try:
            conn.execute(sa.text("ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ is_admin adicionada")
        except Exception:
            pass

        try:
            conn.execute(sa.text("ALTER TABLE clientes ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"))
            conn.commit()
            print("✅ usuario_id adicionada")
        except Exception:
            pass

    # Garante admin a cada deploy
    from app.models import Usuario
    admin = Usuario.query.filter_by(email='isaac_aguiar027@outlook.com').first()
    if admin:
        admin.is_admin = True
        db.session.commit()
        print("✅ Admin garantido")
    else:
        print("⚠️ Usuário não encontrado — crie a conta primeiro no site")
        

if __name__ == '__main__':
    app.run()