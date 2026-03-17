from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app.models import Estoque
from app import db

estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')


@estoque_bp.route('/')
@login_required
def lista():
    itens = Estoque.query.order_by(Estoque.nome).all()
    return render_template('estoque/lista.html', itens=itens)


@estoque_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        quantidade = int(request.form.get('quantidade') or 0)
        preco_custo = float(request.form.get('preco_custo') or 0)

        item = Estoque(nome=nome, quantidade=quantidade, preco_custo=preco_custo)
        db.session.add(item)
        db.session.commit()
        flash('Item adicionado ao estoque!', 'sucesso')
        return redirect(url_for('estoque.lista'))

    return render_template('estoque/lista.html', itens=Estoque.query.order_by(Estoque.nome).all())


@estoque_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    item = Estoque.query.get_or_404(id)
    itens = Estoque.query.order_by(Estoque.nome).all()

    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.quantidade = int(request.form.get('quantidade') or 0)
        item.preco_custo = float(request.form.get('preco_custo') or 0)
        db.session.commit()
        flash('Item atualizado!', 'sucesso')
        return redirect(url_for('estoque.lista'))

    return render_template('estoque/lista.html', itens=itens, editando=item)


@estoque_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    item = Estoque.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item removido do estoque.', 'sucesso')
    return redirect(url_for('estoque.lista'))
