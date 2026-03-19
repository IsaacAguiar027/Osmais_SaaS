from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Usuario
from app import db
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso restrito.', 'erro')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    total = len(usuarios)
    ativos = sum(1 for u in usuarios if u.acesso_ativo)
    pagantes = sum(1 for u in usuarios if u.plano in ('mensal', 'semestral', 'anual'))
    trials = sum(1 for u in usuarios if u.plano == 'trial' and u.acesso_ativo)
    return render_template('admin/index.html',
                           usuarios=usuarios,
                           total=total,
                           ativos=ativos,
                           pagantes=pagantes,
                           trials=trials)


@admin_bp.route('/usuario/<int:id>/toggle-ativo', methods=['POST'])
@login_required
@admin_required
def toggle_ativo(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'erro')
        return redirect(url_for('admin.index'))

    # Desativar = expirar o acesso agora
    # Ativar = dar mais 30 dias de trial
    if usuario.acesso_ativo:
        usuario.trial_expira_em = datetime.utcnow() - timedelta(days=1)
        usuario.assinatura_expira_em = datetime.utcnow() - timedelta(days=1)
        flash(f'Conta de {usuario.nome} desativada.', 'sucesso')
    else:
        usuario.plano = 'trial'
        usuario.trial_expira_em = datetime.utcnow() + timedelta(days=30)
        flash(f'Conta de {usuario.nome} reativada com 30 dias.', 'sucesso')

    db.session.commit()
    return redirect(url_for('admin.index'))


@admin_bp.route('/usuario/<int:id>/alterar-plano', methods=['POST'])
@login_required
@admin_required
def alterar_plano(id):
    usuario = Usuario.query.get_or_404(id)
    plano = request.form.get('plano')
    dias = int(request.form.get('dias', 30))

    usuario.plano = plano
    expira = datetime.utcnow() + timedelta(days=dias)

    if plano == 'trial':
        usuario.trial_expira_em = expira
    elif plano in ('mensal', 'semestral', 'anual'):
        usuario.assinatura_expira_em = expira
    elif plano == 'expirado':
        usuario.trial_expira_em = datetime.utcnow() - timedelta(days=1)
        usuario.assinatura_expira_em = datetime.utcnow() - timedelta(days=1)

    db.session.commit()
    flash(f'Plano de {usuario.nome} alterado para {plano}.', 'sucesso')
    return redirect(url_for('admin.index'))
