from app import create_app, db
import sqlalchemy as sa

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(sa.text('ALTER TABLE ordens ADD COLUMN garantia_dias INTEGER DEFAULT 0'))
        except:
            pass
        conn.commit()
    print('Banco atualizado!')