from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nome_loja = db.Column(db.String(100), nullable=False, default='Minha Assistência')
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    is_admin = db.Column(db.Boolean, default=False)

    # Assinatura
    plano = db.Column(db.String(20), default='trial')   # trial | mensal | anual | expirado
    trial_expira_em = db.Column(db.DateTime)
    assinatura_expira_em = db.Column(db.DateTime)
    mp_payment_id = db.Column(db.String(100))

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def acesso_ativo(self):
        agora = datetime.utcnow()
        if self.plano == 'trial':
            return self.trial_expira_em and agora < self.trial_expira_em
        if self.plano in ('mensal', 'anual'):
            return self.assinatura_expira_em and agora < self.assinatura_expira_em
        return False

    @property
    def dias_restantes(self):
        agora = datetime.utcnow()
        if self.plano == 'trial' and self.trial_expira_em:
            delta = self.trial_expira_em - agora
        elif self.assinatura_expira_em:
            delta = self.assinatura_expira_em - agora
        else:
            return 0
        return max(0, delta.days)

    def __repr__(self):
        return f'<Usuario {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Um cliente pode ter várias ordens
    ordens = db.relationship('Ordem', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nome}>'


class Ordem(db.Model):
    __tablename__ = 'ordens'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    dispositivo = db.Column(db.String(100), nullable=False)
    problema = db.Column(db.Text, nullable=False)
    diagnostico = db.Column(db.Text)
    servico_realizado = db.Column(db.Text)
    valor_peca = db.Column(db.Float, default=0.0)       # interno - nao aparece no PDF
    valor_mao_obra = db.Column(db.Float, default=0.0)   # interno - nao aparece no PDF
    valor = db.Column(db.Float, default=0.0)            # total cobrado do cliente
    status = db.Column(db.String(30), default='aberta')
    # Status possíveis: aberta | em_reparo | ag_peca | ag_aprovacao | concluida | cancelada
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Ordem #{self.id} - {self.dispositivo}>'


class Estoque(db.Model):
    __tablename__ = 'estoque'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    preco_custo = db.Column(db.Float, default=0.0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Estoque {self.nome}>'
