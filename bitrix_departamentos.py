import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros

def get_bitrix_departamentos():

    try:
 
        nome_carga = 'bitrix_departamentos'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL da API Bitrix: {parametro_carga}")

        response = requests.get(parametro_carga)
        data = response.json()

        if 'result' in data:
            df = pd.DataFrame(data['result'])
        else:
            df = pd.DataFrame([data])

        print(f"✔️ Registros extraídos: {len(df)}")

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)


    try: 

        fn_inserirRegistros(cnx.conn, df, "extract.bitrix_departamentos")
        print("Dados Inserido na Tabela")

    except Exception as ex:
        print("-> Erro no inserir dados na tabela!")
        print(f"Erro: {ex}")
        sys.exit(1)

    except Exception as ex:
        print("❌ Erro na carga dos dados do Bitrix!")
        print(ex)
        sys.exit(1)

