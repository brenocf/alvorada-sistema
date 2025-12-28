from datetime import datetime

import cnae_mapping

def analisar_leads(empresas, mapa_cnaes_completo=None):
    """
    Aplica as regras de negócio:
    - Identifica automaticamente a qual Grupo da Lei a empresa pertence.
    - Filtro 1: Licenciamento Inicial (< 120 dias)
    - Filtro 2: RAMA (> 1 ano)
    - Risco: Grupos 03.00 e 23.00
    """
    if mapa_cnaes_completo is None:
        mapa_cnaes_completo = cnae_mapping.LEI_TO_CNAE
        
    leads_processados = []
    
    # Preparar índice reverso para busca rápida: CNAE -> Grupo
    cnae_to_group = {}
    for grp_id, info in mapa_cnaes_completo.items():
        for cnae in info['cnaes']:
            # Normalizar para comparar (sem pontuacao)
            cnae_clean = cnae.replace("-", "").replace("/", "")
            cnae_to_group[cnae_clean] = {"id": grp_id, "desc": info['descricao']}
            cnae_to_group[cnae] = {"id": grp_id, "desc": info['descricao']} # Manter com pontuacao tbm
            
    for emp in empresas:
        # --- 1. CONSOLIDAR LISTA DE CNAES (PRINCIPAL + SECUNDÁRIOS) ---
        lista_cnaes_empresa = []
        
        # Principal
        p = str(emp.get('cnae_fiscal_principal', ''))
        if p: lista_cnaes_empresa.append(p)
        
        # Secundários
        sec = emp.get('cnaes_secundarios', [])
        if isinstance(sec, list):
            for s in sec:
                if s: lista_cnaes_empresa.append(str(s))
        
        # Variáveis de Estado
        status = "Sem Licenciamento Obrigatório"
        acao = "Ignorar"
        tag_risco = ""
        grupo_id = "N/A"
        grupo_desc = "Outros"
        porte_calculado = "Não Classificado"
        status_taxa = "Em Análise" # Novo campo
        
        # --- 2. BUSCA INTELIGENTE DE GRUPO (Match por Código OU Palavra-Chave) ---
        grupo_encontrado = None
        
        # Estratégia A: Match Exato de Código (Mais Rápido e Seguro)
        # Estratégia A: Match Exato de Código (Mais Rápido e Seguro)
        for cnae_teste in lista_cnaes_empresa:
            # Se vier no formato "CODIGO - TEXTO", pega só o código
            cnae_only = cnae_teste.split(" - ")[0]
            cnae_clean = cnae_only.replace("-", "").replace("/", "").strip()
            
            match = cnae_to_group.get(cnae_only) or cnae_to_group.get(cnae_clean)
            if match:
                grupo_encontrado = match
                break
        
        # Estratégia B: Match por Palavra-Chave (Se falhar a A)
        # Varre a descrição do CNAE (se houver) em busca das keywords definidas no mapa
        if not grupo_encontrado:
            descricao_cnae_completa = str(emp.get('cnae_fiscal_descricao', '')).lower()
            
            # Percorre todos os grupos para checar keywords
            for grp_id, info in mapa_cnaes_completo.items():
                if "keywords" in info:
                    for keyword in info["keywords"]:
                        if keyword.lower() in descricao_cnae_completa:
                            grupo_encontrado = {"id": grp_id, "desc": info["descricao"]}
                            break # Encontrou palavra-chave, define grupo
                if grupo_encontrado: break
        
        if grupo_encontrado:
            grupo_id = grupo_encontrado["id"]
            grupo_desc = grupo_encontrado["desc"]
            
            # REGRA ESPECÍFICA: Comércio de Veículos (Grupo 06)
            if grupo_id == "06.00" and "veículos" in str(emp.get('cnae_fiscal_descricao','')).lower():
                tag_risco = "Atenção: Verificar Oficina/Lavagem Anexa"
            
            # --- CÁLCULO DE PORTE (ANEXO II) ---
            # --- CÁLCULO DE PORTE (ANEXO II - AMBIENTAL) ---
            # Este é o porte para fins de LICENCIAMENTO (COEMA/Municipal), não o da Receita.
            # Baseado em Potencial Poluidor x Porte (M, P, M, G, E)
            
            porte_receita = emp.get('porte_receita', 'Não Informado') # ME, EPP, DEMAIS (Apenas informativo)
            
            # Cálculo Técnico (Estimativa para Licenciamento)
            # 1. Obter parâmetros (com valores default 0)
            area_m2 = emp.get('area_construida', 0) 
            faturamento = emp.get('faturamento_estimado') or emp.get('capital_social') or 0
            
            # Tentar processar funcionários
            funcionarios = 0
            try:
                func_raw = emp.get('qtde_funcionarios', 0)
                if isinstance(func_raw, str) and '-' in func_raw:
                    funcionarios = int(func_raw.split('-')[1])
                else:
                    funcionarios = int(func_raw)
            except:
                funcionarios = 0

            # Lógica de Loteamentos
            p_cnae_safe = str(emp.get('cnae_fiscal_principal', ''))
            cnae_check_lote = p_cnae_safe.replace("-", "").replace("/", "")
            is_loteamento = cnae_check_lote in ["4213800", "4110700", "6810203"]

            # Lógica de Loteamentos (Mantida)
            if is_loteamento:
                area_ha = area_m2 / 10000.0 
                if area_ha <= 10: porte_calculado = "Micro"
                elif area_ha <= 30: porte_calculado = "Pequeno"
                elif area_ha <= 50: porte_calculado = "Médio"
                elif area_ha <= 100: porte_calculado = "Grande"
                else: porte_calculado = "Excepcional"
            else:
                # Tabela 1 - Regra Geral
                # Definição dos Limites (Estimativa baseada em Faturamento/Funcionários como proxy de magnitude)
                L_MIC_FAT = 575000
                L_PEQ_FAT = 1150000
                L_MED_FAT = 11500000
                L_GRA_FAT = 85500000
                
                portes = []
                
                if faturamento <= L_MIC_FAT: portes.append(1)
                elif faturamento <= L_PEQ_FAT: portes.append(2)
                elif faturamento <= L_MED_FAT: portes.append(3)
                elif faturamento <= L_GRA_FAT: portes.append(4)
                else: portes.append(5)
                
                if funcionarios <= 7: portes.append(1)
                elif funcionarios <= 50: portes.append(2)
                elif funcionarios <= 100: portes.append(3)
                elif funcionarios <= 500: portes.append(4)
                else: portes.append(5)
                
                if area_m2 > 0:
                    if area_m2 <= 250: portes.append(1)
                    elif area_m2 <= 1000: portes.append(2)
                    elif area_m2 <= 5000: portes.append(3)
                    elif area_m2 <= 10000: portes.append(4)
                    else: portes.append(5)
                
                max_porte = max(portes)
                mapa_nomes = {1:"Micro", 2:"Pequeno", 3:"Médio", 4:"Grande", 5:"Excepcional"}
                porte_calculado = mapa_nomes[max_porte]
            
            # --- CÁLCULO DA TAXA (ART. 16 - LEI 2.917) ---
            natureza = str(emp.get('natureza_juridica', '')).upper()
            
            # Se for Microempresa (Porte Lido ou Calculado como Micro) OU MEI
            # Nota: O porte_calculado é nossa melhor estimativa técnica
            is_mei = "MEI" in natureza or "MICROEMPREENDEDOR" in natureza
            is_micro = porte_calculado == "Micro"
            
            if is_mei or is_micro:
                status_taxa = "ISENTO (Art. 16)"
            else:
                status_taxa = "Sujeito a Taxa (Anexo II)"

            
            # --- LÓGICA DE LICENCIAMENTO ---
            # Regras de Licenciamento só se aplicam se for do grupo
            try:
                data_inicio = emp.get('data_inicio_atividade')
                if data_inicio:
                    data_abertura = datetime.strptime(data_inicio, "%Y-%m-%d")
                    hoje = datetime.now()
                    dias_abertura = (hoje - data_abertura).days
                    
                    if dias_abertura <= 120:
                        status = "Oportunidade de Licenciamento Inicial (LP/LI)"
                        acao = "Contatar para Licenciamento"
                    elif dias_abertura > 365:
                        status = "Venda Recorrente (RAMA)"
                        acao = "Oferecer Renovação/Monitoramento"
                    else:
                        status = "Monitoramento Padrão"
                        acao = "Verificar Regularidade"
                else:
                    status = "Data Indisponível"
                    
                # Risco
                if grupo_id in ["03.00", "23.00"]:
                    tag_risco = "ALTO POTENCIAL"
                
                # Se for "Micro" e não tiver risco alto -> Baixo Impacto (simplificação)
                if porte_calculado == "Micro" and not tag_risco:
                    tag_risco = "BAIXO IMPACTO"
                    
            except Exception as e:
                print(f"Erro processando data: {e}")
                status = "Data Inválida"

        # Adiciona campos enriquecidos
        emp_enriquecida = emp.copy()
        emp_enriquecida['grupo_id'] = grupo_id
        emp_enriquecida['grupo_descricao'] = grupo_desc
        emp_enriquecida['status_radar'] = status
        emp_enriquecida['acao_recomendada'] = acao
        emp_enriquecida['tag_risco'] = tag_risco
        emp_enriquecida['porte_calculado'] = porte_calculado # Ambiental
        emp_enriquecida['porte_receita'] = porte_receita     # CNPJ
        emp_enriquecida['status_taxa'] = status_taxa
        
        # Garantir campos de UI para evitar KeyError
        for campo in ['bairro', 'logradouro', 'numero', 'cep', 'telefone', 'qsa', 'cnaes_secundarios']:
             if campo not in emp_enriquecida:
                 emp_enriquecida[campo] = [] if campo == 'cnaes_secundarios' else ""
        
        leads_processados.append(emp_enriquecida)
        
    return leads_processados
