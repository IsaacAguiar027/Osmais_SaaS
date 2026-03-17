from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para continuar.'

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.ordens import ordens_bp
    from app.routes.clientes import clientes_bp
    from app.routes.estoque import estoque_bp
    from app.routes.pagamento import pagamento_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ordens_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(pagamento_bp)
    app.register_blueprint(admin_bp)

    from flask import redirect, url_for, request as freq
    from flask_login import current_user

    @app.before_request
    def verificar_acesso():
        liberadas = (
            "auth.", "pagamento.", "static", "dashboard.landing", "admin."
        )
        endpoint = freq.endpoint or ""
        if any(endpoint.startswith(r) for r in liberadas):
            return None
        if not current_user.is_authenticated:
            return None
        if not current_user.acesso_ativo:
            return redirect(url_for("pagamento.planos"))

    with app.app_context():
        db.create_all()

        # Migrações
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                conn.commit()
        except Exception:
            pass

        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"))
                conn.commit()
        except Exception:
            pass

        # Garante admin
        from app.models import Usuario
        admin = Usuario.query.filter_by(email='isaac_aguiar027@outlook.com').first()
        if admin:
            admin.is_admin = True
            db.session.commit()

    return app