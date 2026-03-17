from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ordem, Cliente

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    total_abertas = Ordem.query.filter(Ordem.status != 'concluida').count()
    total_clientes = Cliente.query.count()
    ordens_recentes = Ordem.query.order_by(Ordem.criado_em.desc()).limit(5).all()

    return render_template('dashboard/index.html',
        total_abertas=total_abertas,
        total_clientes=total_clientes,
        ordens_recentes=ordens_recentes
    )
