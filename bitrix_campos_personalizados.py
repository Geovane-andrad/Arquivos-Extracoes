import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure

def get_bitrix_campos_personalizados():
    try:
        nome_carga = 'bitrix_company_userfield_list'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)
        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")
        print(f"🔗 URL base da API Bitrix: {parametro_carga}")

        lista = []
        inicio = 0
        total_registros = 0

        # ===== 1️⃣ Extração dos userfields =====
        while True:
            url_com_paginacao = (
                f"{parametro_carga}&start={inicio}" if "?" in parametro_carga else f"{parametro_carga}?start={inicio}"
            )
            response = requests.get(url_com_paginacao)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                print(f"❌ Erro na extração: {data.get('error_description', data['error'])}")
                sys.exit(1)

            if 'result' in data and isinstance(data['result'], list):
                current_page_records = data['result']
                lista.extend(current_page_records)
                total_registros += len(current_page_records)
                print(f"Página {inicio // 50 + 1} extraída. Total acumulado: {total_registros}")
            else:
                print("⚠️ Nenhum campo 'result' encontrado ou formato inesperado.")
                break

            if 'next' in data and data['next'] is not None:
                inicio = data['next']
            else:
                print("✅ Fim da paginação. Extração concluída.")
                break

        df = pd.DataFrame(lista)
        print(f"\n✅ Extração concluída com sucesso! Total de registros: {len(df)}")

        df = df[['ID', 'ENTITY_ID', 'FIELD_NAME', 'USER_TYPE_ID']]

        # ===== 2️⃣ Extração dos nomes amigáveis =====
        nome_carga_campos_amigaveis = "bitrix_company_fields"
        parametro_carga_campos_amigaveis = get_parametroCarga_bitrix(nome_carga_campos_amigaveis)
        if not parametro_carga_campos_amigaveis:
            raise ValueError("Parâmetros da carga 'bitrix_company_fields' não encontrado.")

        print(f"🔗 URL API Campos Amigáveis: {parametro_carga_campos_amigaveis}")

        response_campos = requests.get(parametro_carga_campos_amigaveis)
        response_campos.raise_for_status()
        data_campos = response_campos.json()

        if 'result' not in data_campos:
            raise ValueError("Campo 'result' não encontrado na resposta da API bitrix_company_fields.")

        campos_dict = data_campos['result']

        # ===== 3️⃣ Mapeia formLabel por FIELD_NAME =====
        df['formLabel'] = df['FIELD_NAME'].map(
            lambda field: campos_dict.get(field, {}).get('formLabel', None)
        )
    
    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro de requisição API: {req_err}")
        sys.exit(1)
    
    except Exception as ex:
        print(f"❌ Erro inesperado: {ex}")
        sys.exit(1)

    try: 

       fn_inserirRegistros(cnx.conn, df, "extract.bitrix_campos_personalizados")
       print("Dados Inserido na Tabela")

    except Exception as ex:
       print("-> Erro no inserir dados na tabela!")
       print(f"Erro: {ex}")
       sys.exit(1)

get_bitrix_campos_personalizados()