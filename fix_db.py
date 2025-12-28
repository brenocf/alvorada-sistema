
import sqlite3

def fix_missing_table():
    conn = sqlite3.connect("radar.db")
    c = conn.cursor()
    print("Verificando tabela 'obrigacoes'...")
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS obrigacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj_empresa TEXT,
                titulo TEXT,
                data_prazo TEXT, -- YYYY-MM-DD
                tipo TEXT, -- Licença, Visita, Relatório, Taxa
                concluido BOOLEAN DEFAULT 0,
                FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
            )
        ''')
        conn.commit()
        print("Tabela 'obrigacoes' criada/verificada com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_missing_table()
