
import re
import calendar
from datetime import datetime
import zipfile
import os
import time

def renomear_arquivo_antecipacao(pasta):
    padrao = re.compile(r"TRANSACOES\.ANTECIPADAS_C82_MovingPay_(\d{2}\.\d{2}\.\d{4})_(\d{2}\.\d{2}\.\d{4})_.*\.zip")

    for arquivo in os.listdir(pasta):
        if arquivo.endswith(".zip") and "TRANSACOES.ANTECIPADAS" in arquivo:
            caminho_antigo = os.path.join(pasta, arquivo)
            match = padrao.search(arquivo)  # <- Aqui trocamos de .match() para .search()

            print(f"Testando arquivo: {arquivo}")
            print(f"Match encontrado? {'✅ Sim' if match else '❌ Não'}")

            if match:
                data_ini = datetime.strptime(match.group(1), "%d.%m.%Y")
                data_fim = datetime.strptime(match.group(2), "%d.%m.%Y")

                if data_ini.month == data_fim.month and data_ini.year == data_fim.year:
                    meses_pt = {
                        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
                        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
                        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
                    }
                    nome_mes = meses_pt[data_ini.month]
                    novo_nome = f"TRANSACOES.ANTECIPADAS_MovingPay_{nome_mes}_{data_ini.year}.zip"
                    caminho_novo = os.path.join(pasta, novo_nome)

                    print(f"Renomeando:\n  De: {caminho_antigo}\n  Para: {caminho_novo}")

                    if os.path.exists(caminho_novo):
                        os.remove(caminho_novo)

                    os.rename(caminho_antigo, caminho_novo)
                    print(f"✅ Arquivo renomeado para: {novo_nome}")
                    return
                else:
                    print("ℹ️ Datas abrangem meses diferentes — mantendo nome original.")


def extrair_e_renomear_zip(pasta_origem, pasta_destino_base):
    """
    Extrai o arquivo .xlsx de um .zip diretamente para a pasta de destino,
    renomeando-o no processo e sem criar subpastas.
    """
    print("\n--- Iniciando processo de extração e renomeação direta ---")
    
    # 1. Validações iniciais das pastas
    if not os.path.isdir(pasta_origem):
        print(f"❌ ERRO CRÍTICO: A pasta de origem '{pasta_origem}' não existe.")
        return
    if not os.path.isdir(pasta_destino_base):
        print(f"❌ ERRO CRÍTICO: A pasta de destino '{pasta_destino_base}' não existe. Criando-a...")
        os.makedirs(pasta_destino_base, exist_ok=True)

    # 2. Itera sobre os arquivos na pasta de origem
    for arquivo_zip in os.listdir(pasta_origem):
        if arquivo_zip.endswith(".zip") and "TRANSACOES.ANTECIPADAS_MovingPay" in arquivo_zip:
            caminho_zip = os.path.join(pasta_origem, arquivo_zip)
            print(f"\nProcessando arquivo ZIP: {arquivo_zip}")

            try:
                # 3. Define o nome e o caminho final do arquivo .xlsx
                nome_base_zip = os.path.splitext(arquivo_zip)[0]
                nome_final_xlsx = f"{nome_base_zip}.xlsx"
                caminho_destino_final = os.path.join(pasta_destino_base, nome_final_xlsx)
                
                print(f"Destino final do arquivo: {caminho_destino_final}")

                with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                    # 4. Encontra o arquivo .xlsx dentro do ZIP
                    nome_xlsx_no_zip = None
                    for nome_interno in zip_ref.namelist():
                        if nome_interno.endswith('.xlsx'):
                            nome_xlsx_no_zip = nome_interno
                            break # Encontrou o arquivo, pode parar de procurar

                    if nome_xlsx_no_zip:
                        print(f"Encontrado '{nome_xlsx_no_zip}' dentro do ZIP. Extraindo...")
                        
                        # 5. Extrai o conteúdo em memória
                        dados_arquivo = zip_ref.read(nome_xlsx_no_zip)
                        
                        # 6. Salva o conteúdo diretamente no destino final com o nome correto
                        with open(caminho_destino_final, 'wb') as f_out:
                            f_out.write(dados_arquivo)
                        
                        print(f"✅ Arquivo salvo com sucesso em: {caminho_destino_final}")
                    else:
                        print(f"⚠️ AVISO: Nenhum arquivo .xlsx foi encontrado dentro de '{arquivo_zip}'.")

            except zipfile.BadZipFile:
                print(f"❌ ERRO CRÍTICO: O arquivo '{arquivo_zip}' está corrompido.")
            except PermissionError:
                print(f"❌ ERRO DE PERMISSÃO: O script não tem permissão para escrever em '{pasta_destino_base}'.")
            except Exception as e:
                print(f"❌ Ocorreu um erro inesperado ao processar '{arquivo_zip}': {e}")

    print("\n--- Processo finalizado ---")


