import pandas as pd
import requests
import sys
import json
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure

def get_bitrix_spa138_cadastro():
    
    try:
        nome_carga = 'bitrix_spa138_cadastro'
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
       # df.to_excel('dados_antes_da_formatacao.xlsx', index=False)

        limpar_caracteres_desconhecido = [
            "title",
            "stageId",
            "previousStageId",
            "sourceId",
            "sourceDescription",
            "ufCrm5_1673985300",
            "ufCrm5_1673985372",
            "ufCrm5_1673985431",
            "ufCrm5_1677614410",
            "ufCrm5_1677614456",
            "ufCrm5_1692734261",
            "ufCrm5_1738347285690",
            "ufCrm5_1748882135089",
            "ufCrm5_1750706922788",
            "ufCrm5_1751588044319",
            "ufCrm5_1751588101763"
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
            'id',
            'xmlId',
            'title',
            'createdBy',
            'updatedBy',
            'movedBy',
            'createdTime',
            'updatedTime',
            'movedTime',
            'categoryId',
            'opened',
            'stageId',
            'previousStageId',
            'begindate',
            'closedate',
            'companyId',
            'contactId',
            'opportunity',
            'isManualOpportunity',
            'taxValue',
            'currencyId',
            'mycompanyId',
            'sourceId',
            'sourceDescription',
            'ufCrm5_1673985899',
            'ufCrm5_1673979276',
            'ufCrm5_1673984635',
            'ufCrm5_1673984803',
            'ufCrm5_1673984847',
            'ufCrm5_1673984891',
            'ufCrm5_1673984922',
            'ufCrm5_1673984962',
            'ufCrm5_1673985040',
            'ufCrm5_1673985076',
            'ufCrm5_1673985117',
            'ufCrm5_1673985215',
            'ufCrm5_1673985243',
            'ufCrm5_1673985272',
            'ufCrm5_1673985300',
            'ufCrm5_1673985330',
            'ufCrm5_1673985372',
            'ufCrm5_1673985398',
            'ufCrm5_1673985431',
            'ufCrm5_1673987253',
            'ufCrm5_1674535028',
            'ufCrm5_1674535214',
            'ufCrm5_1674535477',
            'ufCrm5_1674535513',
            'ufCrm5_1674535536',
            'ufCrm5_1674535570',
            'ufCrm5_1674535595',
            'ufCrm5_1674535633',
            'ufCrm5_1674535662',
            'ufCrm5_1674535695',
            'ufCrm5_1674535722',
            'ufCrm5_1674535754',
            'ufCrm5_1674535778',
            'ufCrm5_1674535800',
            'ufCrm5_1674535828',
            'ufCrm5_1674535857',
            'ufCrm5_1674535901',
            'ufCrm5_1674535926',
            'ufCrm5_1674535952',
            'ufCrm5_1674535975',
            'ufCrm5_1674536003',
            'ufCrm5_1677604553232',
            'ufCrm5_1677604630967',
            'ufCrm5_1677614410',
            'ufCrm5_1677614456',
            'ufCrm5_1678460893',
            'ufCrm5_1678463894',
            'ufCrm5_1678663286',
            'ufCrm5_1678704685',
            'ufCrm5_1678704706',
            'ufCrm5_1678812492',
            'ufCrm5_1679504311',
            'ufCrm5_1679504348',
            'ufCrm5_1683551079',
            'ufCrm5_1685553666',
            'ufCrm5_1692734261',
            'ufCrm5_1694442084',
            'ufCrm5_1694442145',
            'ufCrm5_1701197639061',
            'ufCrm5_1707418382',
            'ufCrm5_1732891940',
            'ufCrm5_1738347181710',
            'ufCrm5_1738347216210',
            'ufCrm5_1738347285690',
            'ufCrm5_1738347675720',
            'ufCrm5_1738348757596',
            'ufCrm5_1748882135089',
            'ufCrm5_1748967951621',
            'ufCrm5_1750706922788',
            'ufCrm5_1751587901525',
            'ufCrm5_1751588044319',
            'ufCrm5_1751588101763',
            'ufCrm5_1759361292658',
            'assignedById',
            'isRecurring',
            'lastActivityBy',
            'lastActivityTime',
            'lastCommunicationTime',
            'lastCommunicationCallTime',
            'lastCommunicationEmailTime',
            'lastCommunicationImolTime',
            'lastCommunicationWebformTime',
            'parentId2',
            'utmSource',
            'utmMedium',
            'utmCampaign',
            'utmContent',
            'utmTerm'
            ]] 

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Erro na requisição à API Bitrix: {req_err}")
        sys.exit(1)

    for col in df_final.columns:
        if df_final[col].dtype == 'object':  # apenas colunas de texto
            max_len = df_final[col].astype(str).map(len).max()
            print(f" ⏩ Coluna '{col}' tem valor máximo de {max_len} caracteres")
    
    for col in df_final.columns:
        if df_final[col].dtype == 'object':  # só texto
            max_len = df_final[col].astype(str).map(len).max()
            if max_len > 16:
                print(f"⚠️ Coluna '{col}' tem valor com {max_len} caracteres (limite 16)")

    try: 

       fn_inserirRegistros(cnx.conn, df_final, "extract.bitrix_spa138_cadastro")
       run_procedure('extract.sp_merge_bitrix_cadastro()')
       print("Dados Inserido na Tabela")

    except Exception as ex:
       print("-> Erro no inserir dados na tabela!")
       print(f"Erro: {ex}")
       sys.exit(1)

get_bitrix_spa138_cadastro()