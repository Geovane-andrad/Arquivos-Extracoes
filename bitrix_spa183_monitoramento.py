import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure

def get_bitrix_spa183_monitoramento():
    
    try:
        nome_carga = 'bitrix_spa183_monitoramento'
        parametro_carga = get_parametroCarga_bitrix(nome_carga)

        if not parametro_carga:
            raise ValueError("Parâmetro da carga não encontrado ou inválido.")

        print(f"🔗 URL base da API Bitrix: {parametro_carga}")

        lista = []
        inicio = 0
        total_registros = 0

        while True:
            # Monta a URL com paginação
            url_com_paginacao = (
                f"{parametro_carga}&start={inicio}" if "?" in parametro_carga else f"{parametro_carga}?start={inicio}"
            )
#            print(f"\n➡️ Fazendo requisição para: {url_com_paginacao}")

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

            elif 'result' in data and isinstance(data['result'], dict) and 'items' in data['result']:
                current_page_records = data['result']['items']
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
            "title",
            "stageId",
            "previousStageId",
            "sourceId",
            "sourceDescription"
        ]

        for col in limpar_caracteres_desconhecido:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("'", "", regex=False)
                    .str.replace('"', "", regex=False)
                )

        df_final = df[[
            "id",
            "xmlId",
            "title",
            "createdBy",
            "updatedBy",
            "movedBy",
            "createdTime",
            "updatedTime",
            "movedTime",
            "categoryId",
            "opened",
            "stageId",
            "previousStageId",
            "begindate",
            "closedate",
            "companyId",
            "contactId",
            "opportunity",
            "isManualOpportunity",
            "taxValue",
            "currencyId",
            "mycompanyId",
            "sourceId",
            "sourceDescription",
            "webformId",
            "ufCrm23_1687780616",
            "ufCrm23_1687780743",
            "ufCrm23_1687781289",
            "ufCrm23_1687781323",
            "ufCrm23_1687781453",
            "ufCrm23_1687781659",
            "ufCrm23_1687784589",
            "ufCrm23_1687785021",
            "ufCrm23_1688067213685",
            "ufCrm23_1690978413",
            "ufCrm23_1690978479",
            "ufCrm23_1690979182",
            "ufCrm23_1690979213",
            "ufCrm23_1690986774",
            "ufCrm23_1690996732",
            "ufCrm23_1690996775",
            "ufCrm23_1690996805",
            "ufCrm23_1690996836",
            "ufCrm23_1691160821",
            "ufCrm23_1691160870",
            "ufCrm23_1691160905",
            "ufCrm23_1691160929",
            "ufCrm23_1691691745",
            "ufCrm23_1694434559",
            "ufCrm23_1694434599",
            "ufCrm23_1694434653",
            "ufCrm23_1694434682",
            "ufCrm23_1697568689650",
            "ufCrm23_1697568760020",
            "ufCrm23_1732891879",
            "assignedById",
            "isRecurring",
            "lastActivityBy",
            "lastActivityTime",
            "lastCommunicationTime",
            "lastCommunicationCallTime",
            "lastCommunicationEmailTime",
            "lastCommunicationImolTime",
            "lastCommunicationWebformTime",
            "utmSource",
            "utmMedium",
            "utmCampaign",
            "utmContent",
            "utmTerm"
        ]]
    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)
    try: 

        fn_inserirRegistros(cnx.conn, df_final, "extract.bitrix_spa_183_monitoramento")
        run_procedure('extract.sp_merge_bitrix_monitoramento()')
        print("Dados Inserido na Tabela")

    except Exception as ex:
        print("-> Erro no inserir dados na tabela!")
        print(f"Erro: {ex}")
        sys.exit(1)