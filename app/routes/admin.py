from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models import Usuario, Cliente, Ordem
from app import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator para verificar se o usuário é admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Apenas administradores podem acessar.', 'erro')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard de administrador"""
    total_usuarios = Usuario.query.count()
    total_clientes = Cliente.query.count()
    total_ordens = Ordem.query.count()
    usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    
    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         total_clientes=total_clientes,
                         total_ordens=total_ordens,
                         usuarios=usuarios)


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """Lista de todos os usuários"""
    usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    """Editar usuário"""
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.nome_loja = request.form.get('nome_loja')
        usuario.plano = request.form.get('plano')
        usuario.is_admin = request.form.get('is_admin') == 'on'
        
        try:
            db.session.commit()
            flash(f'Usuário {usuario.nome} atualizado com sucesso!', 'sucesso')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'erro')
    
    return render_template('admin/editar_usuario.html', usuario=usuario)


@admin_bp.route('/usuarios/<int:id>/deletar', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(id):
    """Deletar usuário e todos os seus dados"""
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir deletar a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode deletar sua própria conta!', 'erro')
        return redirect(url_for('admin.usuarios'))
    
    nome_usuario = usuario.nome
    email = usuario.email
    
    try:
        # Deletar ordens do usuário (através dos clientes)
        clientes = Cliente.query.filter_by(usuario_id=usuario.id).all()
        for cliente in clientes:
            Ordem.query.filter_by(cliente_id=cliente.id).delete()
        
        # Deletar clientes
        Cliente.query.filter_by(usuario_id=usuario.id).delete()
        
        # Deletar usuário
        db.session.delete(usuario)
        db.session.commit()
        
        flash(f'Usuário {nome_usuario} ({email}) deletado com sucesso!', 'sucesso')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário: {str(e)}', 'erro')
    
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuarios/<int:id>/resetar-senha', methods=['POST'])
@login_required
@admin_required
def resetar_senha_usuario(id):
    """Resetar senha de um usuário para 123456"""
    usuario = Usuario.query.get_or_404(id)
    
    try:
        nova_senha = '123456'
        usuario.set_senha(nova_senha)
        db.session.commit()
        
        flash(f'Senha de {usuario.nome} foi resetada para: {nova_senha}', 'sucesso')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao resetar senha: {str(e)}', 'erro')
    
    return redirect(url_for('admin.editar_usuario', id=usuario.id))


@admin_bp.route('/clientes')
@login_required
@admin_required
def clientes():
    """Lista de todos os clientes"""
    clientes = Cliente.query.all()
    return render_template('admin/clientes.html', clientes=clientes)


@admin_bp.route('/ordens')
@login_required
@admin_required
def ordens():
    """Lista de todas as ordens"""
    ordens = Ordem.query.order_by(Ordem.criado_em.desc()).all()
    return render_template('admin/ordens.html', ordens=ordens)
