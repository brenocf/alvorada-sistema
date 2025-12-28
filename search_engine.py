import random
from datetime import datetime, timedelta
import requests

def gerar_cnpj_ficticio():
    def d(n): return [random.randint(0, 9) for _ in range(n)]
    return "".join(map(str, d(14)))

def gerar_data_abertura_recente():
    # Gera uma data nos últimos 120 dias (com 30% de chance)
    # ou uma data mais antiga (70% de chance) para testar os filtros corretamente
    if random.random() < 0.3:
        dias = random.randint(0, 119)
    else:
        dias = random.randint(366, 365*5) # Entre 1 e 5 anos atrás
    
    data = datetime.now() - timedelta(days=dias)
    return data.strftime("%Y-%m-%d")

def buscar_cnpj_brasilapi(cnpj):
    """
    Busca dados reais de um CNPJ na BrasilAPI.
    """
    cnpj_limpo = "".join(filter(str.isdigit, cnpj))
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Normalizar para o formato esperado pelo sistema
            return {
                "cnpj": data.get("cnpj"),
                "razao_social": data.get("razao_social"),
                "nome_fantasia": data.get("nome_fantasia") or data.get("razao_social"),
                "data_inicio_atividade": data.get("data_inicio_atividade"),
                "cnae_fiscal_principal": data.get("cnae_fiscal_principal", {}).get("code"), # BrasilAPI retorna objeto
                "cnae_fiscal_descricao": data.get("cnae_fiscal_principal", {}).get("text"),
                "municipio": data.get("municipio"),
                "uf": data.get("uf"),
                "logradouro": data.get("logradouro"),
                "numero": data.get("numero"),
                "bairro": data.get("bairro")
            }
        else:
            return None
    except Exception as e:
        print(f"Erro na API: {e}")
        return None

def buscar_empresas(cidade_ibge="2305506", cnae_alvo=None, mock_mode=True, cnpj_especifico=None):
    """
    Busca empresas.
    - Se cnpj_especifico for fornecido: busca dados REAIS na BrasilAPI (ignora mock_mode).
    - Se mock_mode=True: gera dados fictícios.
    """
    
    resultados = []

    # 1. Busca Real por CNPJ Específico (Prioridade)
    if cnpj_especifico:
        dados_reais = buscar_cnpj_brasilapi(cnpj_especifico)
        if dados_reais:
            resultados.append(dados_reais)
        return resultados
    
    # 2. Modo Mock (Demonstração de Lote)
    if mock_mode:
        # Gerar 20 leads fictícios para teste
        # Misturar CNAEs do alvo com aleatórios
        
        cnaes_possiveis = []
        if cnae_alvo:
            if isinstance(cnae_alvo, list):
                cnaes_possiveis = cnae_alvo
            else:
                cnaes_possiveis = [cnae_alvo]
        
        nomes_comercio = ["Mercadinho", "Posto", "Oficina", "Farmácia", "Padaria"]
        nomes_industria = ["Indústria", "Fábrica", "Confecção", "Serraria", "Reciclagem"]
        sobrenomes = ["do João", "Iguatu", "Ceará", "Progresso", "Central", "Norte", "Sul"]
        
        for _ in range(50):
            tipo = random.choice(["EIRELI", "LTDA", "MEI", "S.A."])
            setor = random.choice([nomes_comercio, nomes_industria])
            nome_fantasia = f"{random.choice(setor)} {random.choice(sobrenomes)}"
            razao_social = f"{nome_fantasia.upper()} {tipo}"
            
            # Escolhe um CNAE: 50% chance de ser um dos CNAEs alvo (se houver), 50% aleatório
            cnae_escolhido = "0000-0/00"
            if cnaes_possiveis and random.random() < 0.6:
                cnae_escolhido = random.choice(cnaes_possiveis)
            else:
                cnae_escolhido = f"{random.randint(1000,9999)}-{random.randint(0,9)}/{random.randint(0,99):02d}"

            
            empresa = {
                "cnpj": gerar_cnpj_ficticio(),
                "razao_social": razao_social,
                "nome_fantasia": nome_fantasia,
                "data_inicio_atividade": gerar_data_abertura_recente(),
                "cnae_fiscal_principal": cnae_escolhido,
                "municipio": "IGUATU",
                "uf": "CE",
                "municipio": "IGUATU",
                "uf": "CE",
                "bairro": random.choice(["Centro", "Flores", "Brasília", "Alto do Jucá", "Areias", "Veneza"]),
                "logradouro": "Rua Exemplo",
                "numero": str(random.randint(10, 999)),
                "cnaes_secundarios": [f"{random.randint(1000,9999)}-{random.randint(0,9)}/{random.randint(0,99):02d}" for _ in range(random.randint(0, 3))]
            }
            resultados.append(empresa)
            
    else:
        # Busca sem CNPJ específico e sem Mock não é suportada por APIs gratuitas para "Varredura da Cidade"
        pass

    return resultados

import re

def extrair_cnpjs_de_texto(texto):
    """
    Extrai todos os padrões de CNPJ (formatados ou não) de um texto arbitrário.
    """
    regex_formatado = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
    encontrados = re.findall(regex_formatado, texto)
    cnpjs_unicos = list(set(encontrados))
    return cnpjs_unicos

def parse_cnpja_record(item):
    """
    Parser estrito para OfficeDto (Detalhes) e OfficePageRecordDto (Lista).
    Baseado na Schema Oficial fornecida:
    root -> taxId (CNPJ)
    root -> company -> name (Razão)
    root -> company -> equity (Capital)
    root -> company -> size -> text (Porte Receita)
    root -> company -> members -> person -> name (QSA)
    root -> alias (Fantasia)
    root -> sideActivities (Secundárias)
    root -> address (Endereço)
    """
    # 1. Navegação Segura para Sub-objetos
    company = item.get("company") or {}
    address = item.get("address") or {}
    main_act = item.get("mainActivity") or {}
    
    # 2. Dados Cadastrais Básicos
    cnpj = item.get("taxId", "")
    razao = company.get("name", item.get("alias", ""))
    fantasia = item.get("alias") or company.get("name", "")
    abertura = item.get("founded", "")
    
    # 3. Porte e Capital (Dados da Receita)
    # Schema: company.size.text
    size_obj = company.get("size") or {}
    porte_receita = size_obj.get("text", "Não Informado")
    
    # Schema: company.equity
    capital_social = company.get("equity", 0)
    
    # 4. Sócios (QSA)
    # Schema: company.members[].person.name
    members = company.get("members") or []
    # Fallback para listas onde members pode estar na raiz (embora schema diga company)
    if not members and "members" in item: 
        members = item["members"]
        
    qsa_names = []
    for m in members:
        # Tenta person.name
        person = m.get("person") or {}
        name = person.get("name")
        # Fallback direto se a estrutura mudar
        if not name: name = m.get("name")
        
        if name: qsa_names.append(name)
    
    qsa_str = ", ".join(qsa_names)

    # 5. Atividades (CNAEs)
    # Principal
    cnae_p_code = str(main_act.get("id", ""))
    cnae_p_text = main_act.get("text", "")
    
    # Secundárias
    # Schema: sideActivities[].id / text
    # Fallback legado: secondaryActivities
    side_acts = item.get("sideActivities") or item.get("secondaryActivities") or []
    cnaes_sec_list = []
    
    if isinstance(side_acts, list):
        for act in side_acts:
            a_id = str(act.get("id", ""))
            a_txt = act.get("text", "")
            if a_id:
                if a_txt:
                    cnaes_sec_list.append(f"{a_id} - {a_txt}")
                else:
                    cnaes_sec_list.append(a_id)
                    
    # 6. Endereço
    logradouro = address.get("street", "")
    numero = address.get("number", "")
    bairro = address.get("district", "")
    municipio_nome = address.get("city", "IGUATU")
    uf = address.get("state", "CE")
    cep = address.get("zip", "")
    
    # 7. Contato
    phones = item.get("phones") or []
    phone_str = ""
    if phones and isinstance(phones, list):
        p0 = phones[0]
        area = p0.get("area", "")
        num = p0.get("number", "")
        if area and num:
            phone_str = f"({area}) {num}"
            
    # Natureza Jurídica
    nature_obj = company.get("nature") or {}
    nat_text = nature_obj.get("text") or str(nature_obj.get("id", ""))

    return {
        "cnpj": cnpj,
        "razao_social": razao,
        "nome_fantasia": fantasia,
        "data_inicio_atividade": abertura,
        "cnae_fiscal_principal": cnae_p_code,
        "cnae_fiscal_descricao": cnae_p_text,
        "cnaes_secundarios": cnaes_sec_list,
        "municipio": municipio_nome,
        "uf": uf,
        "logradouro": logradouro,
        "numero": numero,
        "bairro": bairro,
        "cep": cep,
        "qsa": qsa_str,
        "telefone": phone_str,
        "natureza_juridica": nat_text,
        "porte_receita": porte_receita,
        "capital_social": capital_social
    }

def consultar_detalhes_cnpj(api_key, cnpj):
    """
    Busca dados COMPLETOS de uma empresa específica (custo de crédito se não estiver em cache).
    Endpoint: GET /office/{taxId}
    """
    headers = {"Authorization": api_key}
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    url = f"https://api.cnpja.com/office/{cnpj_clean}"
    
    # Parâmetro maxAge para evitar cache antigo/vazio conforme dica do usuário
    params = {"maxAge": 15} 
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code == 200:
            data = response.json() # OfficeDto
            return parse_cnpja_record(data)
        elif response.status_code == 404:
            return None
        else:
            print(f"Erro Details API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erro Conn Details: {e}")
        return None

def buscar_cnpja_comercial(api_key, cnaes_alvo=None, cidade_ibge="2305506"):
    # ... (código existente de setup) ...
    resultados = []
    headers = {
        "Authorization": f"{api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.cnpja.com/office"
    params = {
        "address.municipality.in": int(cidade_ibge), 
        "limit": 20, 
        "founded.gte": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            lista = data.get('records', [])
            
            if not lista:
                return [], "API retornou sucesso mas lista vazia (Verifique se há empresas novas)."

            for item in lista:
                emp = parse_cnpja_record(item)
                resultados.append(emp)
                
            return resultados, None
            
        elif response.status_code == 401:
            return None, "Erro 401: Chave de API Inválida ou Expirada."
        elif response.status_code == 429:
            return None, "Erro 429: Créditos esgotados."
        else:
            return None, f"Erro {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, f"Erro de Conexão: {str(e)}"

