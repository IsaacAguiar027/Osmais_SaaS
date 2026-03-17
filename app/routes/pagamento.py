from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Usuario
from app import db
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import json
import os

pagamento_bp = Blueprint('pagamento', __name__, url_prefix='/pagamento')


def mp_criar_preferencia(plano, usuario_id, email):
    """Cria preferência de pagamento no Mercado Pago via urllib (sem biblioteca externa)"""
    access_token = os.environ.get('MP_ACCESS_TOKEN')
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 59.00))
    preco_anual = float(os.environ.get('MP_PRECO_ANUAL', 497.00))

    if plano == 'mensal':
        titulo = 'OSmais — Plano Mensal'
        preco = preco_mensal
    else:
        titulo = 'OSmais — Plano Anual'
        preco = preco_anual

    base_url = os.environ.get('MP_BASE_URL', request.host_url.rstrip('/'))

    dados = {
        'items': [{
            'title': titulo,
            'quantity': 1,
            'unit_price': preco,
            'currency_id': 'BRL'
        }],
        'payer': {'email': email},
        'external_reference': f'{usuario_id}:{plano}',
        'back_urls': {
            'success': f'{base_url}/pagamento/sucesso',
            'failure': f'{base_url}/pagamento/falha',
            'pending': f'{base_url}/pagamento/pendente'
        },
        'auto_return': 'approved',
        'notification_url': f'{base_url}/pagamento/webhook'
    }

    url = 'https://api.mercadopago.com/checkout/preferences'
    req = urllib.request.Request(
        url,
        data=json.dumps(dados).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resultado = json.loads(resp.read().decode())
            return resultado
    except urllib.error.HTTPError as e:
        erro = e.read().decode()
        print(f'[MP] Erro ao criar preferência: {erro}')
        return None


@pagamento_bp.route('/planos')
@login_required
def planos():
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 59.00))
    preco_anual = float(os.environ.get('MP_PRECO_ANUAL', 497.00))
    public_key = os.environ.get('MP_PUBLIC_KEY', '')
    return render_template('pagamento/planos.html',
                           preco_mensal=preco_mensal,
                           preco_anual=preco_anual,
                           public_key=public_key)


@pagamento_bp.route('/assinar/<plano>')
@login_required
def assinar(plano):
    if plano not in ('mensal', 'anual'):
        flash('Plano inválido.', 'erro')
        return redirect(url_for('pagamento.planos'))

    resultado = mp_criar_preferencia(plano, current_user.id, current_user.email)

    if not resultado:
        flash('Erro ao conectar com Mercado Pago. Tente novamente.', 'erro')
        return redirect(url_for('pagamento.planos'))

    # Redireciona para o checkout do MP
    return redirect(resultado['init_point'])


@pagamento_bp.route('/sucesso')
@login_required
def sucesso():
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref:
        try:
            usuario_id, plano = external_ref.split(':')
            usuario = Usuario.query.get(int(usuario_id))
            if usuario and usuario.id == current_user.id:
                _ativar_plano(usuario, plano, payment_id)
                flash(f'Pagamento aprovado! Plano {plano} ativado com sucesso.', 'sucesso')
        except Exception as e:
            print(f'[MP] Erro ao ativar plano: {e}')

    return render_template('pagamento/sucesso.html')


@pagamento_bp.route('/falha')
@login_required
def falha():
    return render_template('pagamento/falha.html')


@pagamento_bp.route('/pendente')
@login_required
def pendente():
    return render_template('pagamento/pendente.html')


@pagamento_bp.route('/webhook', methods=['POST'])
def webhook():
    """Recebe notificações do Mercado Pago"""
    dados = request.get_json(silent=True) or {}
    tipo = dados.get('type') or request.args.get('type')
    payment_id = dados.get('data', {}).get('id') or request.args.get('data.id')

    if tipo == 'payment' and payment_id:
        access_token = os.environ.get('MP_ACCESS_TOKEN')
        url = f'https://api.mercadopago.com/v1/payments/{payment_id}'
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            method='GET'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                pagamento = json.loads(resp.read().decode())

            if pagamento.get('status') == 'approved':
                ref = pagamento.get('external_reference', '')
                if ':' in ref:
                    usuario_id, plano = ref.split(':')
                    usuario = Usuario.query.get(int(usuario_id))
                    if usuario:
                        _ativar_plano(usuario, plano, str(payment_id))
                        print(f'[MP] Plano {plano} ativado para usuário {usuario_id}')
        except Exception as e:
            print(f'[MP] Erro no webhook: {e}')

    return jsonify({'status': 'ok'}), 200


def _ativar_plano(usuario, plano, payment_id):
    """Ativa o plano do usuário após pagamento confirmado"""
    agora = datetime.utcnow()
    usuario.plano = plano
    usuario.mp_payment_id = payment_id

    if plano == 'mensal':
        usuario.assinatura_expira_em = agora + timedelta(days=30)
    elif plano == 'anual':
        usuario.assinatura_expira_em = agora + timedelta(days=365)

    db.session.commit()
