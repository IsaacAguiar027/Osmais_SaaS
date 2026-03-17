from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.models import Ordem, Cliente
from app import db

ordens_bp = Blueprint('ordens', __name__, url_prefix='/ordens')


@ordens_bp.route('/')
@login_required
def lista():
    ordens = Ordem.query.order_by(Ordem.criado_em.desc()).all()
    return render_template('ordens/lista.html', ordens=ordens)


@ordens_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        dispositivo = request.form.get('dispositivo')
        problema = request.form.get('problema')
        valor = request.form.get('valor') or 0

        ordem = Ordem(
            cliente_id=cliente_id,
            dispositivo=dispositivo,
            problema=problema,
            valor=float(valor)
        )
        db.session.add(ordem)
        db.session.commit()
        flash('OS criada com sucesso!', 'sucesso')
        return redirect(url_for('ordens.lista'))

    return render_template('ordens/nova.html', clientes=clientes)


@ordens_bp.route('/<int:id>')
@login_required
def detalhe(id):
    ordem = Ordem.query.get_or_404(id)
    return render_template('ordens/detalhe.html', ordem=ordem)


@ordens_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    ordem = Ordem.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if request.method == 'POST':
        ordem.cliente_id = request.form.get('cliente_id')
        ordem.dispositivo = request.form.get('dispositivo')
        ordem.problema = request.form.get('problema')
        ordem.diagnostico = request.form.get('diagnostico')
        ordem.servico_realizado = request.form.get('servico_realizado')
        ordem.valor_peca = float(request.form.get('valor_peca') or 0)
        ordem.valor_mao_obra = float(request.form.get('valor_mao_obra') or 0)
        # Calcula automático, mas respeita edição manual do usuário
        valor_manual = request.form.get('valor')
        valor_auto = ordem.valor_peca + ordem.valor_mao_obra
        ordem.valor = float(valor_manual) if valor_manual and float(valor_manual) != valor_auto else valor_auto
        ordem.status = request.form.get('status')
        db.session.commit()
        flash('OS atualizada!', 'sucesso')
        return redirect(url_for('ordens.detalhe', id=ordem.id))

    return render_template('ordens/editar.html', ordem=ordem, clientes=clientes)


@ordens_bp.route('/<int:id>/pdf')
@login_required
def pdf(id):
    ordem = Ordem.query.get_or_404(id)
    return render_template('ordens/pdf.html', ordem=ordem)


@ordens_bp.route('/<int:id>/pdf/compartilhar/<token>')
def pdf_publico(id, token):
    """Rota pública para compartilhar PDF via WhatsApp"""
    ordem = Ordem.query.get_or_404(id)
    
    # Validar token (válido por 7 dias)
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Verifica se o token é válido para essa OS
        ordem_id_token = s.loads(token, salt='pdf-compartilhar', max_age=7*24*3600)
        if ordem_id_token != id:
            return "Acesso negado", 403
    except (SignatureExpired, BadSignature):
        return "Link expirado ou inválido", 403
    
    return render_template('ordens/pdf.html', ordem=ordem)


@ordens_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    ordem = Ordem.query.get_or_404(id)
    db.session.delete(ordem)
    db.session.commit()
    flash('OS removida.', 'sucesso')
    return redirect(url_for('ordens.lista'))
