# Dicionário de Mapeamento: Lei Municipal Iguatu -> CNAEs
# Baseado na descrição de atividades da Lei 2.917/2021

# Cada chave é o código do grupo na Lei, e o valor é uma lista de CNAEs prováveis.
# Nota: CNAEs são strings com pontuação para facilitar a busca/visualização,
# mas na lógica de comparação pode ser necessário remover pontuação dependendo da fonte de dados.

LEI_TO_CNAE = {
    "01.00": {
        "descricao": "AGROPECUÁRIA",
        "cnaes": ["0151-2/01", "0151-2/02", "0151-2/03", "0154-7/00", "0155-5/01", "0155-5/05", "0119-9/99", "0122-9/00", "0161-0/01", "4683-4/00"]
    },
    "02.00": {
        "descricao": "AQUICULTURA",
        "cnaes": ["0321-3/01", "0321-3/02", "0321-3/03", "0321-3/04", "0321-3/05", "0322-1/01", "0322-1/02", "0322-1/07", "0322-1/99"]
    },
    "03.00": {
        "descricao": "RESÍDUOS SÓLIDOS (ALTO RISCO)",
        "cnaes": ["3811-4/00", "3812-2/00", "3821-1/00", "3822-0/00", "3831-9/01", "3831-9/99", "3832-7/00", "3839-4/99", "4930-2/03", "4687-7/01"]
    },
    "04.00": {
        "descricao": "FLORESTAL",
        "cnaes": ["0210-1/01", "0210-1/03", "0210-1/07", "0220-9/01", "0220-9/02", "0230-6/00"]
    },
    "05.00": {
        "descricao": "IND. MADEIRA",
        "cnaes": ["1610-2/03", "1610-2/04", "1629-3/01", "3101-2/00", "3102-1/00", "1622-6/99"]
    },
    "06.00": {
        "descricao": "COMÉRCIO E SERVIÇOS",
        "cnaes": ["1311-1/00", "1312-0/00", "1340-5/01", "1340-5/02", "1412-6/01", "1412-6/03", "1510-6/00", "1531-9/01"],
        "keywords": ["veículos", "peças", "automotivo"]
    },
    "07.00": {
        "descricao": "IND. BORRACHA E PLÁSTICOS",
        "cnaes": ["2219-6/00", "2222-6/00", "2229-3/02", "2229-3/99", "3832-7/00"]
    },
    "08.00": {
        "descricao": "MINERAÇÃO / EXTRAÇÃO",
        "cnaes": ["0810-0/06", "0810-0/07", "0810-0/99", "0990-4/03", "2392-3/00"],
        "keywords": ["mineração", "extração", "areia", "pedra", "rocha", "barro", "cerâmica"]
    },
    "09.00": {
        "descricao": "ENERGIA",
        "cnaes": ["3511-5/01", "3511-5/03", "3512-3/00", "3514-0/00", "4321-5/00"]
    },
    "10.00": {
        "descricao": "IND. METALÚRGICA",
        "cnaes": ["2451-2/00", "2539-0/01", "2539-0/02", "2599-3/02", "2541-1/00", "2543-8/00"]
    },
    "11.00": {
        "descricao": "ELETRÔNICOS E TRANSPORTE",
        "cnaes": ["2610-8/00", "2710-4/00", "2910-7/01", "2930-1/01", "3091-1/01", "4520-0/01", "4520-0/02"]
    },
    "12.00": {
        "descricao": "PAPEL E EDITORA",
        "cnaes": ["1721-4/00", "1722-2/00", "1811-3/02", "1813-0/99", "3839-4/99"]
    },
    "13.00": {
        "descricao": "ALIMENTAR E BEBIDAS",
        "cnaes": ["1011-2/01", "1012-1/01", "1051-1/00", "1091-1/01", "1091-1/02", "1113-5/02", "1122-4/01", "1099-6/04"]
    },
    "14.00": {
        "descricao": "LOGÍSTICA E TRANSPORTE",
        "cnaes": ["5211-7/99", "4930-2/01", "4930-2/02", "5223-1/00", "5229-0/99"]
    },
    "15.00": {
        "descricao": "ENERGIA E COMBUSTÍVEIS",
        "cnaes": ["3511-5/01", "3514-0/00", "4731-8/00", "4681-8/01", "4681-8/02"]
    },
    "16.00": {
        "descricao": "SANEAMENTO",
        "cnaes": ["3600-6/01", "3701-1/00", "3600-6/02"]
    },
    "17.00": {
        "descricao": "SAÚDE E LABORATÓRIOS",
        "cnaes": ["8610-1/01", "8610-1/02", "8640-2/02", "7210-0/00", "8690-9/99"]
    },
    "18.00": {
        "descricao": "SERVIÇOS E COMÉRCIO (ALIMENTAR)",
        "cnaes": ["4711-3/01", "4711-3/02", "4520-0/00", "9511-8/00", "9521-5/00"],
        "keywords": ["carne", "frigorífico", "embutidos", "abatedouro", "laticínios", "leite"]
    },
    "19.00": {
        "descricao": "EDUCAÇÃO E CULTURA",
        "cnaes": ["8513-9/00", "8520-1/00", "7220-7/00", "9101-5/00", "9102-3/01"]
    },
    "20.00": {
        "descricao": "INFRAESTRUTURA CIVIL / LOTEAMENTOS",
        "cnaes": ["4120-4/00", "4313-4/00", "4211-1/01", "4213-8/00", "4399-1/00", "6810-2/03"]
    },
    "21.00": {
        "descricao": "TURISMO E LAZER",
        "cnaes": ["5510-8/01", "5510-8/02", "5510-8/03", "9321-2/00", "9311-5/00", "9329-8/99"]
    },
    "22.00": {
        "descricao": "DIVERSOS / OUTROS",
        "cnaes": []
    },
    "23.00": {
         "descricao": "IND. TÊXTIL / VESTUÁRIO", 
         "cnaes": ["1412-6/01"] 
    },
    "24.00": {
        "descricao": "INDÚSTRIAS DIVERSAS (CONCRETO)",
        "cnaes": [
            "1813-0/99", "3103-9/00", "2330-3/05", "3211-6/02"
        ],
        "keywords": ["concreto", "usina", "cimento", "artefatos", "pré-moldado", "argamassa", "britagem"]
    }
}
