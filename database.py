
import sqlite3
import json
import logging
from datetime import datetime
import pandas as pd
import streamlit as st

# Tenta importar psycopg2 para Postgres (Cloud)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "radar.db"

def get_connection():
    """
    Retorna conexão com banco de dados.
    Prioridade:
    1. PostgreSQL (via st.secrets["db_url"])
    2. SQLite local (radar.db)
    """
    # Tenta conexão Cloud (Postgres) se configurado
    if HAS_POSTGRES:
        try:
            # Verifica se existe secret configurada
            # Formato esperado no secrets.toml:
            # [postgres]
            # url = "postgres://user:pass@host:port/dbname"
            if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
                conn = psycopg2.connect(st.secrets["postgres"]["url"])
                return conn, "postgres"
        except Exception as e:
            logger.warning(f"Falha ao conectar Postgres: {e}. Usando SQLite.")

    # Fallback: SQLite Local
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"

def run_query(sql, params=None, fetch=False, commit=False):
    """
    Executa query de forma agnóstica (SQLite ou Postgres).
    Trata conversão de placeholders (? vs %s).
    """
    conn, db_type = get_connection()
    result = None
    
    try:
        # Cursor Factory para Postgres retornar dict (igual sqlite3.Row)
        if db_type == "postgres":
            c = conn.cursor(cursor_factory=RealDictCursor)
            # Converter '?' para '%s'
            sql_final = sql.replace("?", "%s")
        else:
            c = conn.cursor()
            sql_final = sql
            
        # Executar
        if params:
            c.execute(sql_final, params)
        else:
            c.execute(sql_final)
            
        # Commit se necessário
        if commit:
            conn.commit()
            
        # Fetch se necessário
        if fetch:
            if "SELECT" in sql.upper() or "RETURNING" in sql.upper():
                result = c.fetchall()
            
    except Exception as e:
        logger.error(f"Erro Query ({db_type}): {e}")
        if db_type == "postgres":
            conn.rollback()
        raise e
    finally:
        conn.close()
        
    return result

def init_db():
    """Inicializa tabelas. Adaptado para sintaxe compatível SQLite/PG."""
    # Tipos de dados compatíveis (TEXT, INTEGER, REAL funcionam em ambos na maioria dos casos simples)
    # TIMESTAMP DEFAULT CURRENT_TIMESTAMP funciona em ambos
    # AUTOINCREMENT no SQLite vs SERIAL/IDENTITY no PG precisa de cuidado.
    # Truque: Usar SERIAL no PG e INTEGER PRIMARY KEY no SQLite.
    
    conn, db_type = get_connection()
    c = conn.cursor()
    
    # Scripts de Criação
    # Para simplicidade neste projeto híbrido, vamos manter a sintaxe SQLite que é 90% compatível
    # mas o Postgres não suporta "INTEGER PRIMARY KEY AUTOINCREMENT".
    # Solução: Criaremos tabelas separadas se for Postgres ou instruiremos o usuário a rodar o schema.sql
    
    # Se for SQLite, roda o init padrão.
    if db_type == "sqlite":
        # ... (Mantendo código original SQLite para compatibilidade local) ...
        c.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                cnpj TEXT PRIMARY KEY,
                razao_social TEXT,
                nome_fantasia TEXT,
                status_crm TEXT DEFAULT 'Novo',
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS interacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj_empresa TEXT,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT,
                notas TEXT,
                proximo_passo TEXT,
                FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS propostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj_empresa TEXT,
                cliente_nome TEXT,
                servico TEXT,
                valor REAL,
                status TEXT DEFAULT 'Aberto',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_vencimento TEXT,
                FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS obrigacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj_empresa TEXT,
                titulo TEXT,
                data_prazo TEXT,
                tipo TEXT,
                concluido BOOLEAN DEFAULT 0,
                FOREIGN KEY(cnpj_empresa) REFERENCES empresas(cnpj)
            )
        ''')
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT
            )
        ''')
        # Admin Default
        try:
            import hashlib
            pass_hash = hashlib.sha256("admin".encode()).hexdigest()
            c.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name) VALUES (?, ?, ?)", 
                    ("admin", pass_hash, "Administrador"))
        except:
            pass
            
        conn.commit()
    
    conn.close()

# --- FUNÇÕES DE NEGÓCIO (Usando run_query Wrapper) ---

def upsert_empresa(dados_dict):
    cnpj = dados_dict.get('cnpj')
    if not cnpj: return "error"

    conn, db_type = get_connection()
    
    try:
        # Select manual para compatibilidade
        if db_type == 'postgres':
            c = conn.cursor(cursor_factory=RealDictCursor)
            c.execute("SELECT * FROM empresas WHERE cnpj = %s", (cnpj,))
            result = c.fetchone()
            existing = dict(result) if result else None
        else:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
            result = c.fetchone()
            existing = dict(result) if result else None
            
        dados_extra = json.dumps(dados_dict, default=str)
        
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
            changes_detected = False
            new_values = []
            update_clause = []
            
            for col_db, key_in in fields_map:
                old_val = existing.get(col_db)
                new_val_raw = dados_dict.get(key_in)
                old_str = str(old_val) if old_val is not None else ""
                new_str = str(new_val_raw) if new_val_raw is not None else ""
                
                final_val = old_val
                if new_str and new_str != old_str:
                    final_val = new_val_raw
                    changes_detected = True
                elif not old_str and new_str:
                     final_val = new_val_raw
                     changes_detected = True
                
                ph = "%s" if db_type == "postgres" else "?"
                update_clause.append(f"{col_db} = {ph}")
                new_values.append(final_val)

            existing_extra_str = existing.get('dados_extra')
            if existing_extra_str != dados_extra:
                changes_detected = True

            ph = "%s" if db_type == "postgres" else "?"
            update_clause.append(f"dados_extra = {ph}")
            new_values.append(dados_extra)
            update_clause.append("data_atualizacao = CURRENT_TIMESTAMP")
            
            new_values.append(cnpj)
            
            if changes_detected:
                ph_where = "%s" if db_type == "postgres" else "?"
                sql = f"UPDATE empresas SET {', '.join(update_clause)} WHERE cnpj = {ph_where}"
                c.execute(sql, new_values)
                conn.commit()
                return "updated"
            else:
                return "skipped"

        else:
            cols = [f[0] for f in fields_map] + ["dados_extra", "cnpj"]
            vals = [dados_dict.get(f[1]) for f in fields_map] + [dados_extra, cnpj]
            
            ph = "%s" if db_type == "postgres" else "?"
            placeholders = ",".join([ph] * len(vals))
            cols_str = ",".join(cols)
            
            c.execute(f"INSERT INTO empresas ({cols_str}) VALUES ({placeholders})", vals)
            conn.commit()
            return "inserted"

    except Exception as e:
        logger.error(f"Erro Upsert: {e}")
        return "error"
    finally:
        conn.close()

def get_carteira(filtro_bairro=None, filtro_status=None):
    conn, db_type = get_connection()
    # Em pandas read_sql, melhor passar a conexão crua e deixar o driver lidar
    # Mas precisamos ajustar a query placeholders
    ph = "%s" if db_type == "postgres" else "?"
    
    query = "SELECT * FROM empresas WHERE 1=1"
    params = []
    
    if filtro_bairro and filtro_bairro != "Todos":
        query += f" AND bairro = {ph}"
        params.append(filtro_bairro)
        
    if filtro_status and filtro_status != "Todos":
        query += f" AND status_crm = {ph}"
        params.append(filtro_status)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_empresa(cnpj):
    rows = run_query("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,), fetch=True)
    if rows:
        # Se for Row (sqlite) converte pra dict, se for RealDictCursor (pg) já é dict
        return dict(rows[0])
    return None

def update_status_crm(cnpj, novo_status):
    run_query("UPDATE empresas SET status_crm = ? WHERE cnpj = ?", (novo_status, cnpj), commit=True)

def add_interacao(cnpj, tipo, notas, proximo_passo=""):
    run_query('''
        INSERT INTO interacoes (cnpj_empresa, tipo, notas, proximo_passo)
        VALUES (?, ?, ?, ?)
    ''', (cnpj, tipo, notas, proximo_passo), commit=True)

def get_historico(cnpj):
    conn, db_type = get_connection()
    ph = "%s" if db_type == "postgres" else "?"
    df = pd.read_sql_query(f"SELECT * FROM interacoes WHERE cnpj_empresa = {ph} ORDER BY data_hora DESC", conn, params=(cnpj,))
    conn.close()
    return df

def add_proposta(cnpj, cliente_nome, servico, valor, data_vencimento, status="Aberto"):
    run_query('''
        INSERT INTO propostas (cnpj_empresa, cliente_nome, servico, valor, data_vencimento, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cnpj, cliente_nome, servico, valor, data_vencimento, status), commit=True)

def get_propostas(filtro_status=None):
    conn, db_type = get_connection()
    ph = "%s" if db_type == "postgres" else "?"
    query = "SELECT * FROM propostas WHERE 1=1"
    params = []
    
    if filtro_status and filtro_status != "Todos":
        query += f" AND status = {ph}"
        params.append(filtro_status)
    query += " ORDER BY data_criacao DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_status_proposta(id_proposta, novo_status):
    run_query("UPDATE propostas SET status = ? WHERE id = ?", (novo_status, id_proposta), commit=True)

def add_obrigacao(cnpj, titulo, data_prazo, tipo):
    run_query('''
        INSERT INTO obrigacoes (cnpj_empresa, titulo, data_prazo, tipo)
        VALUES (?, ?, ?, ?)
    ''', (cnpj, titulo, data_prazo, tipo), commit=True)

def get_obrigacoes(filtro_concluido=False):
    conn, db_type = get_connection()
    query = '''
        SELECT o.*, e.razao_social, e.nome_fantasia 
        FROM obrigacoes o
        LEFT JOIN empresas e ON o.cnpj_empresa = e.cnpj
        WHERE 1=1
    '''
    if not filtro_concluido:
        query += " AND o.concluido = 0" # Postgres trata 0 como false as vezes, mas 0 int funciona
        if db_type == "postgres":
             query = query.replace("o.concluido = 0", "o.concluido = false")

    query += " ORDER BY data_prazo ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def concluir_obrigacao(id_obrigacao):
    # Compatibilidade Boolean: SQLite usa 0/1, PG usa true/false.
    # Mas se definimos como BOOLEAN no PG, 1/0 as vezes falha. Safer: 'true' ou '1'
    # Vamos usar run_query que troca ? por %s mas os params...
    # '1' funciona em ambos geralmente
    run_query("UPDATE obrigacoes SET concluido = 1 WHERE id = ?", (id_obrigacao,), commit=True)

import hashlib

def create_user(username, password, full_name):
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        run_query("INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)", 
                  (username, pass_hash, full_name), commit=True)
        return True
    except Exception:
        return False

def verify_login(username, password):
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    rows = run_query("SELECT id, full_name FROM users WHERE username = ? AND password_hash = ?", 
                     (username, pass_hash), fetch=True)
    if rows:
        r = rows[0]
        # Acesso por chave tanto pra dict (Row) quanto RealDictRow
        return {"id": r["id"], "name": r["full_name"]}
    return None

def add_arquivo(cnpj, nome, caminho, tipo):
    run_query("INSERT INTO arquivos (cnpj_empresa, nome_arquivo, caminho_fisico, tipo) VALUES (?, ?, ?, ?)", 
              (cnpj, nome, caminho, tipo), commit=True)

def get_arquivos(cnpj):
    conn, db_type = get_connection()
    ph = "%s" if db_type == "postgres" else "?"
    df = pd.read_sql_query(f"SELECT * FROM arquivos WHERE cnpj_empresa = {ph} ORDER BY data_upload DESC", conn, params=(cnpj,))
    conn.close()
    return df
