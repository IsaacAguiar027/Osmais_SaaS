from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app.models import Cliente
from app import db

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')


@clientes_bp.route('/')
@login_required
def lista():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes/lista.html', clientes=clientes)


@clientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email')

        cliente = Cliente(nome=nome, telefone=telefone, email=email)
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente cadastrado!', 'sucesso')
        return redirect(url_for('clientes.lista'))

    return render_template('clientes/novo.html')


@clientes_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente removido.', 'sucesso')
    return redirect(url_for('clientes.lista'))
