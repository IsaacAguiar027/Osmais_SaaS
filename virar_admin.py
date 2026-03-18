from app import create_app, db
from app.models import Usuario

app = create_app()
with app.app_context():
    u = Usuario.query.filter_by(email='isaac_aguiar027@outlook.com').first() #email admin
    u.is_admin = True
    db.session.commit()
    print('Admin ativado!')