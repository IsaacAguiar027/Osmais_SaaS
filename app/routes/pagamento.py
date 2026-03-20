# Adicione esta rota no app/routes/pagamento.py
# Logo após a rota /aguardando

@pagamento_bp.route('/confirmar')
@login_required
def confirmar():
    """
    Endpoint AJAX chamado pela tela de aguardando.
    Ativa o plano se o pagamento foi aprovado.
    """
    payment_id   = request.args.get('payment_id')
    status       = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref and ':' in external_ref:
        try:
            usuario_id, plano = external_ref.split(':')
            usuario = Usuario.query.get(int(usuario_id))

            if usuario and usuario.id == current_user.id:
                # Verifica diretamente no MP se o pagamento realmente foi aprovado
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
                        # Se não conseguir verificar, confia no parâmetro da URL
                        pass

                _ativar_plano(usuario, plano, payment_id)
                return jsonify({'ok': True, 'plano': plano})

        except Exception as e:
            print(f'[MP] Erro no confirmar: {e}')
            return jsonify({'ok': False, 'motivo': str(e)})

    # Fallback: verifica se já tem plano ativo
    if current_user.acesso_ativo:
        return jsonify({'ok': True, 'plano': current_user.plano})

    return jsonify({'ok': False, 'motivo': 'parametros_invalidos'})
