# OSmais — Sistema de Gestão para Assistências Técnicas

Sistema SaaS simples e funcional para controle de Ordens de Serviço, clientes e estoque.

## Stack
- **Backend:** Python + Flask
- **Frontend:** Tailwind CSS + HTMX
- **Banco de dados:** SQLite (local)
- **Autenticação:** Flask-Login

---

## Como rodar o projeto

### 1. Pré-requisitos
- Python 3.10 ou superior instalado
- pip (vem com o Python)

### 2. Clone ou baixe o projeto
```bash
cd osmais
```

### 3. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv
```

Ative o ambiente:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Rode o servidor
```bash
python run.py
```

### 6. Acesse no navegador
```
http://localhost:5000
```

Na primeira vez, crie uma conta em `/auth/registrar`.

---

## Estrutura do projeto

```
osmais/
├── app/
│   ├── __init__.py        # Cria o app Flask
│   ├── models/            # Tabelas do banco de dados
│   ├── routes/            # Rotas (páginas)
│   ├── templates/         # HTML das páginas
│   └── static/            # CSS e JS
├── config.py              # Configurações
├── run.py                 # Inicia o servidor
└── requirements.txt       # Dependências
```

---

## Próximos passos sugeridos
- [ ] Geração de PDF do orçamento
- [ ] Notificação por WhatsApp/email
- [ ] Filtro e busca nas OS
- [ ] Relatório de faturamento
- [ ] Multi-usuário por loja (multi-tenant)
