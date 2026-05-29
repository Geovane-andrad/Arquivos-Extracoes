import pandas as pd
import requests
import sys

import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure


def get_bitrix_spa_etapas():

    try:
        nome_carga = 'bitrix_etapa_spa'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL da API Bitrix: {parametro_carga}")

        response = requests.get(parametro_carga)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            raise Exception(data.get('error_description', data['error']))

        if isinstance(data.get('result'), list):
            registros = data['result']
        elif isinstance(data.get('result'), dict):
            registros = data['result'].get('items', [])
        else:
            raise Exception("Estrutura inesperada da resposta da API.")

        if not registros:
            print("⚠️ Nenhum registro retornado.")
            return

        df = pd.DataFrame(registros)

        df_final = df[[
            'ID',
            'ENTITY_ID',
            'STATUS_ID',
            'NAME',
            'NAME_INIT',
            'SORT',
            'SYSTEM',
            'CATEGORY_ID',
            'COLOR',
            'SEMANTICS'
        ]]

        print(f"✅ Extração concluída! Total de registros: {len(df_final)}")

        fn_inserirRegistros(cnx.conn, df_final, "extract.bitrix_etapa_spa")
        run_procedure('extract.sp_merger_bitrix_campos_etapas()')

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)

    except Exception as ex:
        print(f"❌ Erro na extração ou gravação: {ex}")
        sys.exit(1)


# Chamada removida daqui — o Airflow chama a função diretamente via python_callable