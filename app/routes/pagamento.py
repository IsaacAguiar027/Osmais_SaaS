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
    access_token    = os.environ.get('MP_ACCESS_TOKEN', '').strip()
    preco_mensal    = float(os.environ.get('MP_PRECO_MENSAL',    30.00))
    preco_semestral = float(os.environ.get('MP_PRECO_SEMESTRAL', 150.00))
    preco_anual     = float(os.environ.get('MP_PRECO_ANUAL',    240.00))
    base_url        = os.environ.get('MP_BASE_URL', 'https://www.systemaos.com.br').rstrip('/')

    if not access_token:
        print('[MP] ERRO: MP_ACCESS_TOKEN nao configurado!')
        return None

    if plano not in ['mensal', 'semestral', 'anual']:
        print(f'[MP] ERRO: Plano invalido: {plano}')
        return None

    email_payer = email if (email and '@' in email) else 'cliente@osmais.com.br'

    titulos = {
        'mensal':    'OSmais - Plano Mensal',
        'semestral': 'OSmais - Plano Semestral',
        'anual':     'OSmais - Plano Anual',
    }
    precos = {
        'mensal':    preco_mensal,
        'semestral': preco_semestral,
        'anual':     preco_anual,
    }

    preco  = round(float(precos[plano]), 2)
    titulo = titulos[plano]

    print(f"[MP] Criando preferencia | plano={plano} preco={preco} email={email_payer}")

    dados = {
        'items': [{
            'id':          plano,
            'title':       titulo,
            'description': f'Assinatura OSmais - Plano {plano.capitalize()}',
            'quantity':    1,
            'unit_price':  preco,
            'currency_id': 'BRL'
        }],
        'payer': {'email': email_payer},
        'external_reference': f'{usuario_id}:{plano}',
        'back_urls': {
            'success': f'{base_url}/pagamento/sucesso',
            'failure': f'{base_url}/pagamento/falha',
            'pending': f'{base_url}/pagamento/aguardando'
        },
        'auto_return':          'approved',
        'notification_url':     f'{base_url}/pagamento/webhook',
        'statement_descriptor': 'OSMAIS',
        'expires':              False
    }

    url = 'https://api.mercadopago.com/checkout/preferences'
    req = urllib.request.Request(
        url,
        data=json.dumps(dados).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type':  'application/json',
            'X-Idempotency-Key': f'{usuario_id}-{plano}-{int(datetime.utcnow().timestamp())}'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resultado = json.loads(resp.read().decode())
            print(f"[MP] Preferencia criada: {resultado.get('id')} | {resultado.get('init_point')}")
            return resultado
    except urllib.error.HTTPError as e:
        erro = e.read().decode()
        print(f'[MP] ERRO HTTP {e.code}: {erro}')
        return None
    except Exception as e:
        print(f'[MP] ERRO: {str(e)}')
        return None


def mp_criar_assinatura(plano, usuario_id, email):
    access_token = os.environ.get('MP_ACCESS_TOKEN', '').strip()
    preco_mensal = float(os.environ.get('MP_PRECO_MENSAL', 30.00))
    base_url     = os.environ.get('MP_BASE_URL', 'https://www.systemaos.com.br').rstrip('/')

    if not access_token:
        return None

    dados = {
        'reason': 'OSmais - Plano Mensal (recorrente)',
        'auto_recurring': {
            'frequency':          1,
            'frequency_type':     'months',
            'transaction_amount': round(preco_mensal, 2),
            'currency_id':        'BRL'
        },
        'payer_email':        email,
        'external_reference': f'{usuario_id}:{plano}',
        'back_url':           f'{base_url}/pagamento/sucesso',
        'notification_url':   f'{base_url}/pagamento/webhook'
    }

    req = urllib.request.Request(
        'https://api.mercadopago.com/preapproval',
        data=json.dumps(dados).encode('utf-8'),
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f'[MP] Erro assinatura: {e.read().decode()}')
        return None


# ─────────────────────────── ROTAS ───────────────────────────

@pagamento_bp.route('/planos')
@login_required
def planos():
    preco_mensal    = float(os.environ.get('MP_PRECO_MENSAL',    30.00))
    preco_semestral = float(os.environ.get('MP_PRECO_SEMESTRAL', 150.00))
    preco_anual     = float(os.environ.get('MP_PRECO_ANUAL',    240.00))
    public_key      = os.environ.get('MP_PUBLIC_KEY', '')
    return render_template('pagamento/planos.html',
                           preco_mensal=preco_mensal,
                           preco_semestral=preco_semestral,
                           preco_anual=preco_anual,
                           public_key=public_key)


@pagamento_bp.route('/assinar/<plano>')
@login_required
def assinar(plano):
    planos_validos = ('mensal', 'semestral', 'anual', 'mensal_recorrente')
    if plano not in planos_validos:
        flash('Plano invalido.', 'erro')
        return redirect(url_for('pagamento.planos'))

    if plano == 'mensal_recorrente':
        resultado = mp_criar_assinatura('mensal', current_user.id, current_user.email)
        if not resultado or 'init_point' not in resultado:
            flash('Erro ao criar assinatura recorrente. Tente novamente.', 'erro')
            return redirect(url_for('pagamento.planos'))
        return redirect(resultado['init_point'])

    current_user.plano = plano
    db.session.commit()

    resultado = mp_criar_preferencia(plano, current_user.id, current_user.email)
    if not resultado or 'init_point' not in resultado:
        flash('Erro ao conectar com o Mercado Pago. Tente novamente.', 'erro')
        return redirect(url_for('pagamento.planos'))

    return redirect(resultado['init_point'])


@pagamento_bp.route('/sucesso')
@login_required
def sucesso():
    payment_id   = request.args.get('payment_id')
    status       = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref:
        try:
            usuario_id, plano = external_ref.split(':')
            usuario = Usuario.query.get(int(usuario_id))
            if usuario and usuario.id == current_user.id:
                _ativar_plano(usuario, plano, payment_id)
                flash(f'Pagamento aprovado! Plano {plano} ativado. Bom trabalho!', 'sucesso')
        except Exception as e:
            print(f'[MP] Erro ao ativar plano: {e}')

    return render_template('pagamento/sucesso.html')


@pagamento_bp.route('/falha')
def falha():
    return render_template('pagamento/falha.html')


@pagamento_bp.route('/pendente')
def pendente():
    return render_template('pagamento/pendente.html')


@pagamento_bp.route('/aguardando')
def aguardando():
    payment_id   = request.args.get('payment_id')
    status       = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref and current_user.is_authenticated:
        try:
            usuario_id, plano = external_ref.split(':')
            usuario = Usuario.query.get(int(usuario_id))
            if usuario and usuario.id == current_user.id:
                _ativar_plano(usuario, plano, payment_id)
                return redirect(url_for('pagamento.sucesso',
                                        payment_id=payment_id,
                                        status=status,
                                        external_reference=external_ref))
        except Exception as e:
            print(f'[MP] Erro aguardando: {e}')

    return render_template('pagamento/aguardando.html')


@pagamento_bp.route('/confirmar')
@login_required
def confirmar():
    """Endpoint AJAX chamado pela tela de aguardando. Ativa o plano se aprovado."""
    payment_id   = request.args.get('payment_id')
    status       = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref and ':' in external_ref:
        try:
            usuario_id, plano = external_ref.split(':')
            usuario = Usuario.query.get(int(usuario_id))

            if usuario and usuario.id == current_user.id:
                access_token = os.environ.get('MP_ACCESS_TOKEN', '').strip()
                if payment_id and access_token:
                    try:
                        req = urllib.request.Request(
                            f'https://api.mercadopago.com/v1/payments/{payment_id}',
                            headers={'Authorization': f'Bearer {access_token}'},
                            method='GET'
                        )
                        with urllib.request.urlopen(req, timeout=10) as r:
                            pag = json.loads(r.read().decode())
                            if pag.get('status') != 'approved':
                                return jsonify({'ok': False, 'motivo': 'pagamento_nao_aprovado'})
                    except Exception as e:
                        print(f'[MP] Erro ao verificar pagamento: {e}')

                _ativar_plano(usuario, plano, payment_id)
                return jsonify({'ok': True, 'plano': plano})

        except Exception as e:
            print(f'[MP] Erro no confirmar: {e}')
            return jsonify({'ok': False, 'motivo': str(e)})

    if current_user.acesso_ativo:
        return jsonify({'ok': True, 'plano': current_user.plano})

    return jsonify({'ok': False, 'motivo': 'parametros_invalidos'})


@pagamento_bp.route('/status')
@login_required
def status_pagamento():
    usuario = Usuario.query.get(current_user.id)
    if usuario and usuario.assinatura_expira_em and usuario.assinatura_expira_em > datetime.utcnow():
        return jsonify({'status': 'aprovado'})
    return jsonify({'status': 'pendente'})


@pagamento_bp.route('/detalhes')
@login_required
def detalhes_pagamento():
    usuario = Usuario.query.get(current_user.id)
    if not usuario:
        return jsonify({'erro': 'Usuario nao encontrado'})
    nomes  = {'mensal': 'Mensal', 'semestral': 'Semestral', 'anual': 'Anual'}
    valores = {
        'mensal':    float(os.environ.get('MP_PRECO_MENSAL',    30)),
        'semestral': float(os.environ.get('MP_PRECO_SEMESTRAL', 150)),
        'anual':     float(os.environ.get('MP_PRECO_ANUAL',    240)),
    }
    return jsonify({'plano': nomes.get(usuario.plano, usuario.plano), 'valor': valores.get(usuario.plano, 0)})


@pagamento_bp.route('/webhook', methods=['POST'])
def webhook():
    dados        = request.get_json(silent=True) or {}
    tipo         = dados.get('type') or request.args.get('type')
    resource_id  = dados.get('data', {}).get('id') or request.args.get('data.id')
    access_token = os.environ.get('MP_ACCESS_TOKEN', '').strip()

    def mp_get(url):
        req = urllib.request.Request(url,
                                     headers={'Authorization': f'Bearer {access_token}'},
                                     method='GET')
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())

    if tipo == 'payment' and resource_id:
        try:
            pag = mp_get(f'https://api.mercadopago.com/v1/payments/{resource_id}')
            if pag.get('status') == 'approved':
                ref = pag.get('external_reference', '')
                if ':' in ref:
                    uid, plano = ref.split(':')
                    u = Usuario.query.get(int(uid))
                    if u:
                        _ativar_plano(u, plano, str(resource_id))
        except Exception as e:
            print(f'[MP] webhook payment erro: {e}')

    elif tipo == 'subscription_preapproval' and resource_id:
        try:
            ass = mp_get(f'https://api.mercadopago.com/preapproval/{resource_id}')
            if ass.get('status') == 'authorized':
                ref = ass.get('external_reference', '')
                if ':' in ref:
                    uid, _ = ref.split(':')
                    u = Usuario.query.get(int(uid))
                    if u:
                        _ativar_plano(u, 'mensal', str(resource_id))
        except Exception as e:
            print(f'[MP] webhook assinatura erro: {e}')

    elif tipo == 'subscription_authorized_payment' and resource_id:
        try:
            cob = mp_get(f'https://api.mercadopago.com/authorized_payments/{resource_id}')
            if cob.get('status') == 'processed':
                ass = mp_get(f'https://api.mercadopago.com/preapproval/{cob.get("preapproval_id")}')
                ref = ass.get('external_reference', '')
                if ':' in ref:
                    uid, _ = ref.split(':')
                    u = Usuario.query.get(int(uid))
                    if u:
                        _ativar_plano(u, 'mensal', str(resource_id))
        except Exception as e:
            print(f'[MP] webhook renovacao erro: {e}')

    return jsonify({'status': 'ok'}), 200


def _ativar_plano(usuario, plano, payment_id):
    agora = datetime.utcnow()
    usuario.plano         = plano
    usuario.mp_payment_id = payment_id
    base    = usuario.assinatura_expira_em if (usuario.assinatura_expira_em and usuario.assinatura_expira_em > agora) else agora
    duracao = {'mensal': timedelta(days=30), 'semestral': timedelta(days=180), 'anual': timedelta(days=365)}
    usuario.assinatura_expira_em = base + duracao.get(plano, timedelta(days=30))
    db.session.commit()
    print(f"[MP] Plano {plano} ativado ate {usuario.assinatura_expira_em}")
