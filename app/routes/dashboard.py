from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ordem, Cliente
from app import db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    total_abertas = Ordem.query.filter(Ordem.status != 'concluida').count()
    total_clientes = Cliente.query.count()
    total_concluidas = Ordem.query.filter_by(status='concluida').count()
    ordens_recentes = Ordem.query.order_by(Ordem.criado_em.desc()).limit(5).all()

    # Faturamento do mês atual
    hoje = datetime.utcnow()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0)
    faturamento_mes = db.session.query(
        func.sum(Ordem.valor)
    ).filter(
        Ordem.status == 'concluida',
        Ordem.atualizado_em >= inicio_mes
    ).scalar() or 0

    # Mão de obra e custo de peças do mês
    mao_obra_mes = db.session.query(
        func.sum(Ordem.valor_mao_obra)
    ).filter(
        Ordem.status == 'concluida',
        Ordem.atualizado_em >= inicio_mes
    ).scalar() or 0

    custo_pecas_mes = db.session.query(
        func.sum(Ordem.valor_peca)
    ).filter(
        Ordem.status == 'concluida',
        Ordem.atualizado_em >= inicio_mes
    ).scalar() or 0

    margem_mes = faturamento_mes - custo_pecas_mes

    # OS por status para gráfico
    status_counts = {
        'aberta': Ordem.query.filter_by(status='aberta').count(),
        'em_reparo': Ordem.query.filter_by(status='em_reparo').count(),
        'ag_peca': Ordem.query.filter_by(status='ag_peca').count(),
        'ag_aprovacao': Ordem.query.filter_by(status='ag_aprovacao').count(),
        'concluida': Ordem.query.filter_by(status='concluida').count(),
        'cancelada': Ordem.query.filter_by(status='cancelada').count(),
    }

    # OS dos últimos 7 dias para gráfico de linha
    os_por_dia = []
    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)
        inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        fim = dia.replace(hour=23, minute=59, second=59)
        count = Ordem.query.filter(
            Ordem.criado_em >= inicio,
            Ordem.criado_em <= fim
        ).count()
        os_por_dia.append({'dia': dia.strftime('%d/%m'), 'count': count})

    return render_template('dashboard/index.html',
        total_abertas=total_abertas,
        total_clientes=total_clientes,
        total_concluidas=total_concluidas,
        faturamento_mes=faturamento_mes,
        ordens_recentes=ordens_recentes,
        status_counts=status_counts,
        os_por_dia=os_por_dia,
        mao_obra_mes=mao_obra_mes,
        custo_pecas_mes=custo_pecas_mes,
        margem_mes=margem_mes
    )
