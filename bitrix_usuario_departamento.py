import pandas as pd
import requests
import sys
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros

def get_bitrix_usuarios_departamentos():
    try:
        nome_carga = 'bitrix_usuarios'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL base da API Bitrix: {parametro_carga}")

        lista_usuarios = []
        inicio = 0
        total_registros = 0

        # 🔁 Loop de paginação
        while True:
            url_com_paginacao = f"{parametro_carga}?start={inicio}"
            print(f"\n➡️ Fazendo requisição para: {url_com_paginacao}")

            response = requests.get(url_com_paginacao)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                print(f"❌ Erro no loop da extração: {data.get('error_description', data['error'])}")
                sys.exit(1)

            if 'result' in data and isinstance(data['result'], list):
                current_page_records = data['result']
                lista_usuarios.extend(current_page_records)
                total_registros += len(current_page_records)
                print(f"Página {inicio // 50 + 1} extraída com {len(current_page_records)} registros.")
                print(f"Total acumulado: {total_registros}")
            else:
                print("⚠️ Nenhum campo 'result' encontrado ou formato inesperado.")
                break

            if 'next' in data and data['next'] is not None:
                inicio = data['next']
            else:
                print("✅ Fim da paginação: 'next' não encontrado. Extração finalizada.")
                break

        # Converte para DataFrame
        df = pd.DataFrame(lista_usuarios)
        print(f"\n✅ Extração concluída com sucesso! Total de registros: {len(df)}")
        print("🔧 Gerando tabela auxiliar de departamentos...")

        df_departamentos = (
            df.explode("UF_DEPARTMENT")  # transforma listas em linhas
              .dropna(subset=["UF_DEPARTMENT"])  # remove valores nulos
              .loc[:, ["ID", "UF_DEPARTMENT"]]  # mantém apenas colunas desejadas
        )

        print(f"✅ Tabela gerada com {len(df_departamentos)} linhas (ID x UF_DEPARTMENT).")

        df_departamentos_final = df_departamentos[["ID", "UF_DEPARTMENT"]]

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        sys.exit(1)
    
    try:
        fn_inserirRegistros(cnx.conn, df_departamentos_final, "extract.bitrix_usuarios_departamentos")
        
    except Exception as ex:
        print("-> ❌ Erro ao inserir dados na tabela auxiliar!")
        print(f"Erro: {ex}")
        sys.exit(1)
