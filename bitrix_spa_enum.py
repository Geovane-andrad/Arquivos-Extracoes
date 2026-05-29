import pandas as pd
import requests
import sys

import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure


def get_bitrix_spa_enum(spas):

    try:
        rows = []

        nome_carga = 'bitrix_enum_spa'
        url_base = get_parametroCarga_bitrix(nome_carga)

        if not url_base:
            raise ValueError(f"Parâmetro da carga não encontrado: {nome_carga}")

        for codigo_spa in spas:

            parametro_carga = f"{url_base}{codigo_spa}"
            print(f"\n🔗 SPA {codigo_spa} | URL: {parametro_carga}")

            response = requests.get(parametro_carga)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                raise Exception(data.get('error_description', data['error']))

            campos = data['result'].get('fields', data['result'])

            for campo_bitrix, meta in campos.items():

                if meta.get('type') != 'enumeration':
                    continue

                titulo_campo = meta.get('title')

                for item in meta.get('items', []):
                    rows.append({
                        "entity_type_id": codigo_spa,
                        "campo_bitrix": campo_bitrix.lower(),
                        "id_enum": int(item.get("ID")),
                        "ds_enum": item.get("VALUE"),
                        "ds_titulo_campo": titulo_campo
                    })

        df_final = pd.DataFrame(rows)
        print(f"\n✅ Extração concluída! Total de ENUMs: {len(df_final)}")

        fn_inserirRegistros(cnx.conn, df_final, 'extract.bitrix_enum_spa')
        run_procedure('extract.sp_merger_bitrix_campos_enum()')

        print("✅ Dimensão de ENUMs atualizada com sucesso!")

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)

    except Exception as ex:
        print("❌ Erro no processamento da carga!")
        print(f"Erro: {ex}")
        sys.exit(1)


# Chamada removida daqui — o Airflow chama a função diretamente via python_callable
