import os

# Carrega o .env ANTES de qualquer import do Flask
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ[key.strip()] = value.strip()
    print(f'[.env] Carregado: MAIL_USERNAME={os.environ.get("MAIL_USERNAME")}')
else:
    print('[.env] Arquivo não encontrado!')

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
