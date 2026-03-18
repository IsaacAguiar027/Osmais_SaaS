from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.models import Usuario
from app import db
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def gerar_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='reset-senha')


def verificar_token(token, expiracao=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='reset-senha', max_age=expiracao)
    except (SignatureExpired, BadSignature):
        return None
    return email


def enviar_email(destinatario, assunto, html):
    remetente = os.environ.get('MAIL_USERNAME')
    senha = os.environ.get('MAIL_PASSWORD')
    if not remetente or not senha:
        print('[EMAIL] MAIL_USERNAME ou MAIL_PASSWORD não configurados')
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = assunto
    msg['From'] = remetente
    msg['To'] = destinatario
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        print(f'[EMAIL] Enviado para {destinatario}')
        return True
    except Exception as e:
        print(f'[EMAIL] Erro ao enviar: {e}')
        return False


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_senha(senha):
            login_user(usuario)
            return redirect(url_for('dashboard.index'))
        flash('Email ou senha incorretos.', 'erro')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form.get('nome')
        nome_loja = request.form.get('nome_loja') or 'Minha Assistência'
        email = request.form.get('email')
        senha = request.form.get('senha')

        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'erro')
            return render_template('auth/registrar.html')

        trial_dias = int(os.environ.get('MP_TRIAL_DIAS', 30))
        usuario = Usuario(
            nome=nome,
            nome_loja=nome_loja,
            email=email,
            plano='trial',
            trial_expira_em=datetime.utcnow() + timedelta(days=trial_dias)
        )
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/registrar.html')


@auth_bp.route('/esqueceu-senha', methods=['GET', 'POST'])
def esqueceu_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            token = gerar_token(usuario.email)
            link = url_for('auth.resetar_senha', token=token, _external=True)
            html = render_template('auth/email_reset.html',
                                   nome=usuario.nome,
                                   nome_loja=usuario.nome_loja,
                                   link=link)
            enviado = enviar_email(usuario.email, 'OSmais — Redefinição de senha', html)
            if not enviado:
                flash('Erro ao enviar email. Verifique as configurações.', 'erro')
                return render_template('auth/esqueceu_senha.html')
        flash('Se esse email estiver cadastrado, você receberá um link em breve.', 'sucesso')
        return redirect(url_for('auth.login'))
    return render_template('auth/esqueceu_senha.html')


@auth_bp.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    email = verificar_token(token)
    if not email:
        flash('Link inválido ou expirado. Solicite um novo.', 'erro')
        return redirect(url_for('auth.esqueceu_senha'))
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        flash('Usuário não encontrado.', 'erro')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        senha = request.form.get('senha')
        confirmar = request.form.get('confirmar')
        if senha != confirmar:
            flash('As senhas não coincidem.', 'erro')
            return render_template('auth/resetar_senha.html', token=token)
        if len(senha) < 6:
            flash('A senha deve ter ao menos 6 caracteres.', 'erro')
            return render_template('auth/resetar_senha.html', token=token)
        usuario.set_senha(senha)
        db.session.commit()
        flash('Senha alterada com sucesso! Faça login.', 'sucesso')
        return redirect(url_for('auth.login'))
    return render_template('auth/resetar_senha.html', token=token)


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'dados':
            novo_email = request.form.get('email')
            existe = Usuario.query.filter(
                Usuario.email == novo_email,
                Usuario.id != current_user.id
            ).first()
            if existe:
                flash('Esse email já está em uso.', 'erro')
            else:
                current_user.nome_loja = request.form.get('nome_loja')
                current_user.email = novo_email
                db.session.commit()
                flash('Dados atualizados com sucesso!', 'sucesso')

        elif acao == 'senha':
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirmar = request.form.get('confirmar')
            if not current_user.check_senha(senha_atual):
                flash('Senha atual incorreta.', 'erro')
            elif nova_senha != confirmar:
                flash('As novas senhas não coincidem.', 'erro')
            elif len(nova_senha) < 6:
                flash('A nova senha deve ter ao menos 6 caracteres.', 'erro')
            else:
                current_user.set_senha(nova_senha)
                db.session.commit()
                flash('Senha alterada com sucesso!', 'sucesso')

        elif acao == 'deletar_conta':
            from app.models import Ordem, Cliente, Estoque
            senha = request.form.get('senha_confirmacao')
            if not current_user.check_senha(senha):
                flash('Senha incorreta. Conta não foi deletada.', 'erro')
            else:
                usuario_id = current_user.id
                # Busca clientes do usuário e deleta OS vinculadas
                clientes = Cliente.query.filter_by(usuario_id=usuario_id).all() if hasattr(Cliente, 'usuario_id') else Cliente.query.all()
                for cliente in clientes:
                    Ordem.query.filter_by(cliente_id=cliente.id).delete()
                Cliente.query.filter_by(id=current_user.id).delete() if not hasattr(Cliente, 'usuario_id') else None
                # Deleta o usuário
                u = Usuario.query.get(usuario_id)
                db.session.delete(u)
                db.session.commit()
                logout_user()
                flash('Sua conta foi deletada.', 'sucesso')
                return redirect(url_for('dashboard.landing'))

        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html')


@auth_bp.route('/listar-usuarios-secreto')
def listar_usuarios_secreto():
    token = request.args.get('token')
    secret = os.environ.get('ADMIN_SECRET_TOKEN', '')
    if not secret or token != secret:
        return 'Não autorizado', 403
    usuarios = Usuario.query.all()
    resultado = '<br>'.join([f'{u.id} | {u.email} | admin={u.is_admin}' for u in usuarios])
    return resultado or 'Nenhum usuário encontrado'


@auth_bp.route('/set-admin-secreto')
def set_admin_secreto():
    """Rota secreta para definir admin em produção — só funciona com token correto"""
    token = request.args.get('token')
    secret = os.environ.get('ADMIN_SECRET_TOKEN', '')
    if not secret or token != secret:
        return 'Não autorizado', 403
    email = os.environ.get('ADMIN_EMAIL')
    if not email:
        return 'ADMIN_EMAIL não configurado', 400
    import sqlalchemy as sa
    with db.engine.connect() as conn:
        try:
            conn.execute(sa.text('ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
            conn.commit()
        except:
            pass
    u = Usuario.query.filter_by(email=email).first()
    if not u:
        return f'Usuário {email} não encontrado', 404
    u.is_admin = True
    db.session.commit()
    return f'Admin ativado para {email}!', 200
