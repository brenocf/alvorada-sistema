import sqlite3
import json
from datetime import datetime
import pandas as pd

DB_PATH = "radar.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela Empresas
    # Armazena os dados principais e mapeados. 
    # 'dados_extra' guarda o JSON completo para campos que não precisam de coluna dedicada (flexibilidade).
    c.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            cnpj TEXT PRIMARY KEY,
            razao_social TEXT,
            nome_fantasia TEXT,
            status_crm TEXT DEFAULT 'Novo', -- Novo, Em Negociação, Cliente, Descartado
            grupo_atividade TEXT,
            descricao_atividade TEXT,
            risco TEXT,
            porte TEXT,
            status_taxa TEXT,
            telefone TEXT,
            qsa TEXT,
            logradouro TEXT,
            numero TEXT,
            bairro TEXT,
            municipio TEXT,
            uf TEXT,
            cep TEXT,
            rota_link TEXT,
            data_abertura TEXT,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dados_extra TEXT
        )
    ''')
    
    # Tabela Interações
    c.execute('''
        CREATE TABLE IF NOT EXISTS interacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj_empresa TEXT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT, -- Ligação, Visita, Email, Whatsapp, Nota
            notas TEXT,
            proximo_passo TEXT,
            FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
        )
    ''')
    
    # Tabela Propostas / Financeiro
    c.execute('''
        CREATE TABLE IF NOT EXISTS propostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj_empresa TEXT,
            cliente_nome TEXT,
            servico TEXT,
            valor REAL,
            status TEXT DEFAULT 'Aberto', -- Aberto, Pago, Atrasado, Cancelado
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_vencimento TEXT,
            FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
        )
    ''')

    # Tabela Obrigações / Calendário
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

    # Tabela GED / Arquivos
    c.execute('''
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj_empresa TEXT,
            nome_arquivo TEXT,
            caminho_fisico TEXT,
            tipo TEXT,
            data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
        )
    ''') 

    # Tabela Usuários (Login)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT
        )
    ''')
    
    # Criar admin padrão se não existir
    try:
        # Senha padrão 'admin' (hash simples para demo)
        import hashlib
        pass_hash = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name) VALUES (?, ?, ?)", 
                  ("admin", pass_hash, "Administrador"))
    except:
        pass
    
    conn.commit()
    conn.close()

def upsert_empresa(dados_dict):
    """
    Insere ou Atualiza uma empresa no banco com lógica inteligente:
    - Se não existir: INSERE.
    - Se existir:
        - Compara dados novos com antigos.
        - Se dados novos forem vazios e antigo existir, MATÉM o antigo (Complementar).
        - Se dados novos forem diferentes e não vazios, ATUALIZA.
        - Se tudo for igual, IGNORA (Skip).
    Retorna: "inserted", "updated", "skipped" ou "error".
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Para acessar por nome
    c = conn.cursor()
    
    cnpj = dados_dict.get('cnpj')
    if not cnpj: return "error"

    try:
        # 1. Buscar Existente
        c.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
        existing = c.fetchone()
        
        # Preparar dados de entrada
        dados_extra = json.dumps(dados_dict, default=str)
        
        # Campos mapeados para comparação/update
        # (Nome Coluna DB, Chave Dict Entrada)
        fields_map = [
            ("razao_social", "razao_social"),
            ("nome_fantasia", "nome_fantasia"),
            ("grupo_atividade", "grupo_descricao"),
            ("descricao_atividade", "cnae_fiscal_descricao"),
            ("risco", "tag_risco"),
            ("porte", "porte_calculado"),
            ("status_taxa", "status_taxa"),
            ("telefone", "telefone"),
            ("qsa", "qsa"),
            ("logradouro", "logradouro"),
            ("numero", "numero"),
            ("bairro", "bairro"),
            ("municipio", "municipio"),
            ("uf", "uf"),
            ("cep", "cep"),
            ("rota_link", "Rota"),
            ("data_abertura", "data_inicio_atividade")
        ]
        
        if existing:
            # 2. Lógica de Comparação e Merge
            changes_detected = False
            new_values = []
            update_clause = []
            
            for col_db, key_in in fields_map:
                old_val = existing[col_db]
                new_val_raw = dados_dict.get(key_in)
                
                # Normalização para comparação (tratar None como "")
                old_str = str(old_val) if old_val is not None else ""
                new_str = str(new_val_raw) if new_val_raw is not None else ""
                
                final_val = old_val # Default: Manter
                
                if new_str and new_str != old_str:
                    # Dado novo é diferente e não vazio -> ATUALIZAR
                    final_val = new_val_raw
                    changes_detected = True
                elif not old_str and new_str:
                     # Dado antigo vazio e novo existe -> COMPLEMENTAR
                     final_val = new_val_raw
                     changes_detected = True
                
                # Para query UPDATE
                update_clause.append(f"{col_db} = ?")
                new_values.append(final_val)

            # --- DETECÇÃO DE MUDANÇA NO JSON (Enriquecimento) ---
            # O bug anterior ignorava mudanças apenas nos dados extras (ex: CNAEs Secundários, Porte Receita)
            existing_extra_str = existing['dados_extra']
            if existing_extra_str != dados_extra:
                changes_detected = True

            # Sempre atualizar o JSON blob e data
            update_clause.append("dados_extra = ?")
            new_values.append(dados_extra)
            update_clause.append("data_atualizacao = CURRENT_TIMESTAMP")
            
            # Adicionar CNPJ para o WHERE
            new_values.append(cnpj)
            
            if changes_detected:
                sql = f"UPDATE empresas SET {', '.join(update_clause)} WHERE cnpj = ?"
                c.execute(sql, new_values)
                conn.commit()
                return "updated"
            else:
                return "skipped"

        else:
            # 3. Inserção Limpa
            # Construir tupla na ordem correta
            cols = [f[0] for f in fields_map] + ["dados_extra", "cnpj"]
            vals = [dados_dict.get(f[1]) for f in fields_map] + [dados_extra, cnpj] # ordem: campos..., extra, cnpj (que é a PK, mas insert precisa)
            
            # Ajuste insert: precisamos listar colunas explicitamente
            placeholders = ",".join(["?"] * len(vals))
            cols_str = ",".join(cols)
            
            c.execute(f"INSERT INTO empresas ({cols_str}) VALUES ({placeholders})", vals)
            conn.commit()
            return "inserted"

    except Exception as e:
        print(f"Erro no Upsert: {e}")
        return "error"
    finally:
        conn.close()

def get_carteira(filtro_bairro=None, filtro_status=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM empresas WHERE 1=1"
    params = []
    
    if filtro_bairro and filtro_bairro != "Todos":
        query += " AND bairro = ?"
        params.append(filtro_bairro)
        
    if filtro_status and filtro_status != "Todos":
        query += " AND status_crm = ?"
        params.append(filtro_status)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_empresa(cnpj):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
    row = c.fetchone()
    conn.close()
    if row:
        # Converter row para dict com nomes das colunas
        cols = [description[0] for description in c.description]
        return dict(zip(cols, row))
    return None

def update_status_crm(cnpj, novo_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE empresas SET status_crm = ? WHERE cnpj = ?", (novo_status, cnpj))
    conn.commit()
    conn.close()

def add_interacao(cnpj, tipo, notas, proximo_passo=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO interacoes (cnpj_empresa, tipo, notas, proximo_passo)
        VALUES (?, ?, ?, ?)
    ''', (cnpj, tipo, notas, proximo_passo))
    conn.commit()
    conn.close()

def get_historico(cnpj):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM interacoes WHERE cnpj_empresa = ? ORDER BY data_hora DESC", conn, params=(cnpj,))
    conn.close()
    return df

def add_proposta(cnpj, cliente_nome, servico, valor, data_vencimento, status="Aberto"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO propostas (cnpj_empresa, cliente_nome, servico, valor, data_vencimento, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cnpj, cliente_nome, servico, valor, data_vencimento, status))
    conn.commit()
    conn.close()

def get_propostas(filtro_status=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM propostas WHERE 1=1"
    params = []
    
    if filtro_status and filtro_status != "Todos":
        query += " AND status = ?"
        params.append(filtro_status)
        
    query += " ORDER BY data_criacao DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_status_proposta(id_proposta, novo_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE propostas SET status = ? WHERE id = ?", (novo_status, id_proposta))
    conn.commit()
    conn.close()

def add_obrigacao(cnpj, titulo, data_prazo, tipo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO obrigacoes (cnpj_empresa, titulo, data_prazo, tipo)
        VALUES (?, ?, ?, ?)
    ''', (cnpj, titulo, data_prazo, tipo))
    conn.commit()
    conn.close()

def get_obrigacoes(filtro_concluido=False):
    conn = sqlite3.connect(DB_PATH)
    # Join para pegar nome da empresa
    query = '''
        SELECT o.*, e.razao_social, e.nome_fantasia 
        FROM obrigacoes o
        LEFT JOIN empresas e ON o.cnpj_empresa = e.cnpj
        WHERE 1=1
    '''
    
    if not filtro_concluido:
        query += " AND o.concluido = 0"
        
    query += " ORDER BY data_prazo ASC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def concluir_obrigacao(id_obrigacao):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE obrigacoes SET concluido = 1 WHERE id = ?", (id_obrigacao,))
    conn.commit()
    conn.close()

import hashlib

def create_user(username, password, full_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)", 
                  (username, pass_hash, full_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("SELECT id, full_name FROM users WHERE username = ? AND password_hash = ?", (username, pass_hash))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {"id": user[0], "name": user[1]}
    return None

def add_arquivo(cnpj, nome, caminho, tipo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO arquivos (cnpj_empresa, nome_arquivo, caminho_fisico, tipo) VALUES (?, ?, ?, ?)", 
              (cnpj, nome, caminho, tipo))
    conn.commit()
    conn.close()

def get_arquivos(cnpj):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM arquivos WHERE cnpj_empresa = ? ORDER BY data_upload DESC", conn, params=(cnpj,))
    conn.close()
    return df
