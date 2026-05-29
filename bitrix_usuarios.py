import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure

def get_bitrix_usuarios():
    
    try:
        nome_carga = 'bitrix_usuarios'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL base da API Bitrix: {parametro_carga}")

        lista_usuarios = []
        inicio = 0
        total_registros = 0

        while True:
            # Monta a URL com paginação
            url_com_paginacao = f"{parametro_carga}?start={inicio}"

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
                lista_usuarios.extend(current_page_records)
                total_registros += len(current_page_records)

                print(f"Página {inicio // 50 + 1} extraída. Total acumulado: {total_registros}.")
                
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
        df = pd.DataFrame(lista_usuarios)
        print(f"\n✅ Extração concluída com sucesso! Total de registros: {len(df)}")

        df["NAME"] = df["NAME"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        )

        df["LAST_NAME"] = df["LAST_NAME"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        )

        df["SECOND_NAME"] = df["SECOND_NAME"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        )

        df["EMAIL"] = df["EMAIL"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        )

        df_final = df[[
            'ID',
            'XML_ID',
            'ACTIVE',
            'NAME',
            'LAST_NAME',
            'SECOND_NAME',
            'EMAIL',
            'LAST_LOGIN',
            'DATE_REGISTER',
            'TIME_ZONE',
            'IS_ONLINE',
            'PERSONAL_GENDER',
            'PERSONAL_WWW',
            'PERSONAL_BIRTHDAY',
            'PERSONAL_PHOTO',
            'PERSONAL_MOBILE',
            'PERSONAL_CITY',
            'WORK_PHONE',
            'WORK_POSITION',
            'UF_EMPLOYMENT_DATE'
            ]] 

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)

    try: 

        fn_inserirRegistros(cnx.conn, df_final, "extract.bitrix_usuarios")
        run_procedure('extract.sp_merger_bitrix_usuario()')
        print("Dados Inserido na Tabela")

    except Exception as ex:
        print("-> Erro no inserir dados na tabela!")
        print(f"Erro: {ex}")
        sys.exit(1)
