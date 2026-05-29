import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure

def get_bitrix_company():
    
    try:
        nome_carga = 'bitrix_company'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        campos = [
            'ID', 'COMPANY_TYPE', 'TITLE', 'LEAD_ID', 'HAS_PHONE', 'HAS_EMAIL', 'HAS_IMOL',
            'ASSIGNED_BY_ID', 'CREATED_BY_ID', 'MODIFY_BY_ID', 'INDUSTRY', 'CURRENCY_ID',
            'EMPLOYEES', 'COMMENTS', 'DATE_CREATE', 'DATE_MODIFY', 'OPENED', 'IS_MY_COMPANY',
            'ORIGINATOR_ID', 'ORIGIN_ID', 'LAST_ACTIVITY_BY', 'LAST_ACTIVITY_TIME',
            'LAST_COMMUNICATION_TIME', 'UF_CRM_6079A84B2FF32'
        ]

        parametro_campos_selecionado = '&'.join(f"select[]={campo}" for campo in campos)


        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL base da API Bitrix: {parametro_carga}")

        lista = []
        inicio = 0
        total_registros = 0

        while True:
            
            url = f"{parametro_carga}?{parametro_campos_selecionado}"    

            url_com_paginacao = (
                f"{url}&start={inicio}" if "?" in url else f"{url}?start={inicio}"
            )

            response = requests.get(url_com_paginacao)
            response.raise_for_status()
            data = response.json()

            # Verifica erro na resposta
            if 'error' in data:
                print(f"❌ Erro no loop da extração: {data.get('error_description', data['error'])}")
                sys.exit(1)

            # Verifica e adiciona registros
            if 'result' in data and isinstance(data['result'], list):
                current_page_records = data['result']
                lista.extend(current_page_records)
                total_registros += len(current_page_records)

                print(f"Página {inicio // 50 + 1} extraída. Total acumulado: {total_registros}")

            else:
                print("⚠️ Nenhum campo 'result' encontrado ou formato inesperado.")
                break

            # Controle de paginação
            if 'next' in data and data['next'] is not None:
                inicio = data['next']
            else:
                print("✅ Fim da paginação: 'next' não encontrado. Extração finalizada.")
                break

        # Cria o DataFrame final (fora do while)
        df = pd.DataFrame(lista)
        print(f"\n✅ Extração concluída com sucesso! Total de registros: {len(df)}")

        limpar_caracteres_desconhecido = [
            "TITLE",
            "COMMENTS",
            "ORIGINATOR_ID",
            'UF_CRM_6079A84B2FF32'
        ]

        for col in limpar_caracteres_desconhecido:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("'", "", regex=False)
                    .str.replace('"', "", regex=False)
                )


    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)

    try: 

       fn_inserirRegistros(cnx.conn, df, "extract.bitrix_company")
       run_procedure('extract.sp_merge_bitrix_company()')
       print("Dados Inserido na Tabela")

    except Exception as ex:
       print("-> Erro no inserir dados na tabela!")
       print(f"Erro: {ex}")
       sys.exit(1)

get_bitrix_company()