import requests
import zipfile
import os
import csv
import io
import shutil
from datetime import datetime

# Configuração
BASE_URL = "https://dadosabertos.rfb.gov.br/CNPJ/"
DIR_DADOS = os.path.join(os.getcwd(), "dados_receita")
ARQUIVO_SAIDA = os.path.join(os.getcwd(), "dados", "iguatu_oficial.csv")
CIDADE_ALVO = "IGUATU"
UF_ALVO = "CE"

# Criar pastas
if not os.path.exists(DIR_DADOS):
    os.makedirs(DIR_DADOS)
if not os.path.exists(os.path.dirname(ARQUIVO_SAIDA)):
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA))

def download_file(url, destiny):
    import time
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for tentativa in range(3):
        try:
            print(f"Baixando {url} (Tentativa {tentativa+1}/3)...")
            # verify=False pois o cert da receita as vezes expira ou da erro em cadeias antigas
            with requests.get(url, stream=True, headers=headers, timeout=60, verify=False) as r:
                r.raise_for_status()
                with open(destiny, 'wb') as f:
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and downloaded % (10*1024*1024) == 0: 
                             # Print a cada 10MB para não floodar
                             pass
            print(f"Download concluído: {destiny}")
            return True
        except Exception as e:
            print(f"Erro no download: {e}")
            time.sleep(5) # Espera 5s antes de tentar de novo
    
    print(f"Falha fatal ao baixar {url} após 3 tentativas.")
    return False

def encontrar_codigo_municipio():
    print("Identificando Código TOM de Iguatu...")
    arquivo_zip = os.path.join(DIR_DADOS, "Municipios.zip")
    
    # Baixar Tabela de Municipios
    if not os.path.exists(arquivo_zip):
        success = download_file(f"{BASE_URL}Municipios.zip", arquivo_zip)
        if not success and not os.path.exists(arquivo_zip):
            print("❌ Falha crítica: Não foi possível baixar a tabela de municípios.")
            return None
    
    codigo_encontrado = None
    
    try:
        with zipfile.ZipFile(arquivo_zip) as z:
            nome_csv = z.namelist()[0]
            with z.open(nome_csv) as f:
                for line in f:
                    try:
                        decoded_line = line.decode('latin-1').strip()
                        parts = decoded_line.split(';')
                        if len(parts) >= 2:
                            codigo = parts[0].strip('"')
                            nome = parts[1].strip('"').upper()
                            if nome == CIDADE_ALVO:
                                codigo_encontrado = codigo
                                print(f"✅ Código Encontrado para {CIDADE_ALVO}: {codigo_encontrado}")
                                break
                    except:
                        pass
    except zipfile.BadZipFile:
        print("❌ Erro: Arquivo Municipios.zip corrompido. Apagando para tentar novamente.")
        os.remove(arquivo_zip)
        return None

    return codigo_encontrado

def processar_estabelecimentos(codigo_municipio):
    print(f"Iniciando processamento para o código {codigo_municipio}...")
    
    # Preparar arquivo de saída
    HEADER = [
        "CNPJ_BASICO", "CNPJ_ORDEM", "CNPJ_DV", "MATRIZ_FILIAL", "NOME_FANTASIA", 
        "SITUACAO_CADASTRAL", "DATA_SITUACAO", "MOTIVO_SITUACAO", 
        "NM_CIDADE_EXTERIOR", "PAIS", "DATA_INICIO_ATIVIDADE", "CNAE_PRINCIPAL", 
        "CNAE_SECUNDARIA", "TIPO_LOGRADOURO", "LOGRADOURO", "NUMERO", 
        "COMPLEMENTO", "BAIRRO", "CEP", "UF", "MUNICIPIO_COD", 
        "DDD1", "TELEFONE1", "DDD2", "TELEFONE2", "DDD_FAX", "FAX", 
        "EMAIL", "SITUACAO_ESPECIAL", "DATA_SITUACAO_ESPECIAL"
    ]
    
    # Criar/Limpar arquivo de saída e escrever header
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out, delimiter=';')
        writer.writerow(HEADER)

    # São 10 arquivos de estabelecimentos (0 a 9)
    for i in range(10):
        nome_arquivo = f"Estabelecimentos{i}.zip"
        url = f"{BASE_URL}{nome_arquivo}"
        caminho_zip = os.path.join(DIR_DADOS, nome_arquivo)
        
        try:
            # Baixar
            if not os.path.exists(caminho_zip):
                print(f"--- Baixando Lote {i+1}/10 ---")
                success = download_file(url, caminho_zip)
                if not success:
                    print(f"⚠️ Pular arquivo {nome_arquivo} (Falha no download)")
                    continue
            
            print(f"Processando {nome_arquivo}...")
            
            with zipfile.ZipFile(caminho_zip) as z:
                nome_csv_interno = z.namelist()[0]
                with z.open(nome_csv_interno) as f_in:
                    for line_bytes in f_in:
                        try:
                            line = line_bytes.decode('latin-1')
                            parts = line.split(';')
                            parts = [p.strip('"') for p in parts]
                            
                            if len(parts) > 20:
                                municipio_cod = parts[20]
                                if municipio_cod == codigo_municipio:
                                    with open(ARQUIVO_SAIDA, 'a', encoding='utf-8', newline='') as f_append:
                                        writer = csv.writer(f_append, delimiter=';')
                                        writer.writerow(parts)
                        except Exception:
                            continue 
                            
            # Opcional: Remover zip após processar
            # os.remove(caminho_zip) 
            
        except zipfile.BadZipFile:
            print(f"❌ Zip Corrompido: {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao processar {nome_arquivo}: {e}")

    print(f"Processamento concluído! Arquivo gerado em: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    cod = encontrar_codigo_municipio()
    if cod:
        processar_estabelecimentos(cod)
    else:
        print(f"Não foi possível encontrar o código para {CIDADE_ALVO}.")
