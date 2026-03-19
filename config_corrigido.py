"""
Configuração do SistemaOS
Carrega variáveis de ambiente do .env
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    """Configuração base da aplicação"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///osmais.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mercado Pago
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY')
    MP_PRECO_MENSAL = float(os.environ.get('MP_PRECO_MENSAL', 29.00))
    MP_PRECO_ANUAL = float(os.environ.get('MP_PRECO_ANUAL', 300.00))
    MP_TRIAL_DIAS = int(os.environ.get('MP_TRIAL_DIAS', 30))
    MP_BASE_URL = os.environ.get('MP_BASE_URL', 'https://www.systemaos.com.br')
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    @staticmethod
    def validar_config():
        """Valida se as configurações obrigatórias estão presentes"""
        erros = []
        
        if not Config.MP_ACCESS_TOKEN:
            erros.append("❌ MP_ACCESS_TOKEN não configurado no .env")
        
        if not Config.MP_PUBLIC_KEY:
            erros.append("❌ MP_PUBLIC_KEY não configurado no .env")
        
        if erros:
            print("\n" + "="*70)
            print("⚠️  CONFIGURAÇÃO INCOMPLETA")
            print("="*70)
            for erro in erros:
                print(erro)
            print("\nSolução:")
            print("1. Copie o arquivo .env.example para .env")
            print("2. Adicione suas credenciais do Mercado Pago")
            print("3. Reinicie a aplicação")
            print("="*70 + "\n")
            return False
        
        print("\n✅ Configuração validada com sucesso!")
        print(f"   MP_ACCESS_TOKEN: {Config.MP_ACCESS_TOKEN[:20]}...")
        print(f"   MP_PUBLIC_KEY: {Config.MP_PUBLIC_KEY[:20]}...")
        print(f"   Preço Mensal: R$ {Config.MP_PRECO_MENSAL:.2f}")
        print(f"   Preço Anual: R$ {Config.MP_PRECO_ANUAL:.2f}\n")
        return True


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração de produção"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuração de testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Seleciona a configuração baseado no ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retorna a configuração apropriada"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
