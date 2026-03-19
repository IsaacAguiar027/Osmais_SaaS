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
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 29.00))
    preco_anual = float(os.environ.get('MP_PRECO_ANUAL', 300.00))

    if plano == 'mensal':
        titulo = 'OSmais — Plano Mensal'
        preco = preco_mensal
    else:
        titulo = 'OSmais — Plano Anual'
        preco = preco_anual

    base_url = 'https://www.systemaos.com.br'

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
            'success': f'{base_url}/pagamento/aguardando',
            'failure': f'{base_url}/pagamento/falha',
            'pending': f'{base_url}/pagamento/aguardando'
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




def mp_criar_assinatura(plano, usuario_id, email):
    """Cria assinatura recorrente no Mercado Pago (débito automático)"""
    access_token = os.environ.get('MP_ACCESS_TOKEN')
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 29.00))
    base_url = 'https://www.systemaos.com.br'

    dados = {
        'reason': 'OSmais — Plano Mensal',
        'auto_recurring': {
            'frequency': 1,
            'frequency_type': 'months',
            'transaction_amount': preco_mensal,
            'currency_id': 'BRL'
        },
        'payer_email': email,
        'external_reference': f'{usuario_id}:{plano}',
        'back_url': f'{base_url}/pagamento/sucesso',
        'notification_url': f'{base_url}/pagamento/webhook'
    }

    url = 'https://api.mercadopago.com/preapproval'
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
        print(f'[MP] Erro ao criar assinatura: {erro}')
        return None

@pagamento_bp.route('/planos')
@login_required
def planos():
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 29.00))
    preco_anual = float(os.environ.get('MP_PRECO_ANUAL', 300.00))
    public_key = os.environ.get('MP_PUBLIC_KEY', '')
    return render_template('pagamento/planos.html',
                           preco_mensal=preco_mensal,
                           preco_anual=preco_anual,
                           public_key=public_key)


@pagamento_bp.route('/assinar/<plano>')
@login_required
def assinar(plano):
    if plano not in ('mensal', 'anual', 'mensal_recorrente'):
        flash('Plano inválido.', 'erro')
        return redirect(url_for('pagamento.planos'))

    # Plano mensal recorrente usa API de assinaturas
    if plano == 'mensal_recorrente':
        resultado = mp_criar_assinatura('mensal', current_user.id, current_user.email)
        if not resultado:
            flash('Erro ao criar assinatura. Tente novamente.', 'erro')
            return redirect(url_for('pagamento.planos'))
        return redirect(resultado['init_point'])

    # Plano avulso (mensal ou anual)
    resultado = mp_criar_preferencia(plano, current_user.id, current_user.email)

    if not resultado:
        flash('Erro ao conectar com Mercado Pago. Tente novamente.', 'erro')
        return redirect(url_for('pagamento.planos'))

    return redirect(resultado['init_point'])

@pagamento_bp.route('/status')
@login_required
def status_pagamento():
    usuario = Usuario.query.get(current_user.id)

    if usuario and usuario.assinatura_expira_em:
        if usuario.assinatura_expira_em > datetime.utcnow():
            return jsonify({'status': 'aprovado'})

    return jsonify({'status': 'pendente'})


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
    resource_id = dados.get('data', {}).get('id') or request.args.get('data.id')

    access_token = os.environ.get('MP_ACCESS_TOKEN')

    # Pagamento avulso
    if tipo == 'payment' and resource_id:
        url = f'https://api.mercadopago.com/v1/payments/{resource_id}'
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
                        _ativar_plano(usuario, plano, str(resource_id))
                        print(f'[MP] Plano {plano} ativado para usuário {usuario_id}')
        except Exception as e:
            print(f'[MP] Erro no webhook pagamento: {e}')

    # Assinatura recorrente
    elif tipo == 'subscription_preapproval' and resource_id:
        url = f'https://api.mercadopago.com/preapproval/{resource_id}'
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            method='GET'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                assinatura = json.loads(resp.read().decode())
            status = assinatura.get('status')
            ref = assinatura.get('external_reference', '')
            print(f'[MP] Assinatura {resource_id} status={status} ref={ref}')
            if status == 'authorized' and ':' in ref:
                usuario_id, plano = ref.split(':')
                usuario = Usuario.query.get(int(usuario_id))
                if usuario:
                    _ativar_plano(usuario, 'mensal', str(resource_id))
                    print(f'[MP] Assinatura ativada para usuário {usuario_id}')
            elif status in ('cancelled', 'paused') and ':' in ref:
                usuario_id, _ = ref.split(':')
                usuario = Usuario.query.get(int(usuario_id))
                if usuario and usuario.plano == 'mensal':
                    # Não cancela imediatamente — deixa expirar naturalmente
                    print(f'[MP] Assinatura {status} para usuário {usuario_id}')
        except Exception as e:
            print(f'[MP] Erro no webhook assinatura: {e}')

    # Cobrança recorrente (renovação automática)
    elif tipo == 'subscription_authorized_payment' and resource_id:
        url = f'https://api.mercadopago.com/authorized_payments/{resource_id}'
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            method='GET'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                cobranca = json.loads(resp.read().decode())
            if cobranca.get('status') == 'processed':
                preapproval_id = cobranca.get('preapproval_id')
                # Busca a assinatura para pegar o external_reference
                url2 = f'https://api.mercadopago.com/preapproval/{preapproval_id}'
                req2 = urllib.request.Request(
                    url2,
                    headers={'Authorization': f'Bearer {access_token}'},
                    method='GET'
                )
                with urllib.request.urlopen(req2) as resp2:
                    assinatura = json.loads(resp2.read().decode())
                ref = assinatura.get('external_reference', '')
                if ':' in ref:
                    usuario_id, _ = ref.split(':')
                    usuario = Usuario.query.get(int(usuario_id))
                    if usuario:
                        _ativar_plano(usuario, 'mensal', str(resource_id))
                        print(f'[MP] Renovação automática ativada para usuário {usuario_id}')
        except Exception as e:
            print(f'[MP] Erro no webhook renovação: {e}')

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
