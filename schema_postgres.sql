
-- Tabela Empresas
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
);

-- Tabela Interações
CREATE TABLE IF NOT EXISTS interacoes (
    id SERIAL PRIMARY KEY,
    cnpj_empresa TEXT REFERENCES empresas(cnpj),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT,
    notas TEXT,
    proximo_passo TEXT
);

-- Tabela Propostas
CREATE TABLE IF NOT EXISTS propostas (
    id SERIAL PRIMARY KEY,
    cnpj_empresa TEXT REFERENCES empresas(cnpj),
    cliente_nome TEXT,
    servico TEXT,
    valor REAL,
    status TEXT DEFAULT 'Aberto',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_vencimento TEXT
);

-- Tabela Obrigações
CREATE TABLE IF NOT EXISTS obrigacoes (
    id SERIAL PRIMARY KEY,
    cnpj_empresa TEXT REFERENCES empresas(cnpj),
    titulo TEXT,
    data_prazo TEXT,
    tipo TEXT,
    concluido BOOLEAN DEFAULT FALSE
);

-- Tabela Arquivos
CREATE TABLE IF NOT EXISTS arquivos (
    id SERIAL PRIMARY KEY,
    cnpj_empresa TEXT REFERENCES empresas(cnpj),
    nome_arquivo TEXT,
    caminho_fisico TEXT,
    tipo TEXT,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela Usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT
);

-- Admin Default (Senha: admin)
INSERT INTO users (username, password_hash, full_name) 
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Administrador')
ON CONFLICT (username) DO NOTHING;
