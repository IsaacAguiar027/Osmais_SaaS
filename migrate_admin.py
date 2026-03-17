import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'osmais.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

migracoes = [
    ("usuarios", "is_admin", "ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT 0"),
    ("clientes", "usuario_id", "ALTER TABLE clientes ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"),
]

for tabela, coluna, sql in migracoes:
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"✅ Coluna '{coluna}' adicionada em '{tabela}'!")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print(f"ℹ️  '{coluna}' em '{tabela}' já existe, pulando.")
        else:
            print(f"❌ Erro em '{tabela}.{coluna}': {e}")

conn.close()
print("\nMigração concluída!")