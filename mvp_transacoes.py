
import pandas as pd
import json
import sys

from sys_funcaoInserirTabela import fn_inserirRegistros
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_mvp
from sys_funcoesBanco import run_procedure
import os
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirLog import fn_inserirLog
import sys_conexaoOdata as odatas


def get_mvp_transacoes():
    # Aqui começa o código para inserir os logs na tabala no banco de dados
    #_______________________________________________________________________________________________________________
    pid = "'"+str(os.getpid())+"'"
    script = "'"+str(os.path.basename(__file__))+"'"
    projeto = "'carga datalake'"
    etapa = "'extração'"

    try:
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_transacoes"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'"+carga_parametro+"'", 'null')

    except Exception as ex:
        print("\n-> Erro na parametrizacao!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)
    #_________________________________________________________________________________________________________________
    # encerra o código para inserir os logs

    try:

        if carga_parametro:
            valores = carga_parametro.split('*')
            
            url = valores[0]  # "API_Transacoes"
            start_date = valores[1]  # "2025-01-01"
            finish_date = valores[2]  # "2025-01-05"

            # Configura os parâmetros da API
            parametro = {
                "start_date": start_date,
                "finish_date": finish_date,
                "filter_date_by": "updated_date",
                "page": 1
            }

            print(f"Parâmetros configurados: {parametro}")


        # Requisição inicial para obter o número de páginas


        requisicao_inicial = get_dados_mvp(url,parametro)

        if requisicao_inicial.status_code != 200:
            print(f"Erro na requisição inicial: {requisicao_inicial.status_code}")
            print(requisicao_inicial.text)
            sys.exit(1)

    except Exception as ex:
        print("\n-> Erro no spilt de datas!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)


    try:
        resposta_inicial = requisicao_inicial.json()
        print("Resposta inicial completa:")
        #print(json.dumps(resposta_inicial, indent=4, ensure_ascii=False))  # Exibe toda a resposta
        last_page = resposta_inicial.get("transacoes", {}).get("lastPage", 1)  # Garante que `lastPage` seja obtido corretamente
        print(f"Número total de páginas: {last_page}")
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON na requisição inicial.")
        sys.exit(1)

    # Lista para armazenar todas as transações
    todas_paginas = []


    # Loop para processar todas as páginas
    for pagina in range(1,last_page + 1):
        parametro["page"] = pagina

        # Requisição para cada página
        requisicao = get_dados_mvp(url,parametro)

        if requisicao.status_code != 200:
            print(f"Erro na página {pagina}: {requisicao.status_code}")
            sys.exit(1)

        try:
            dados = requisicao.json()
            print(f"Resposta da página {pagina}:")
            #print(json.dumps(dados, indent=4, ensure_ascii=False))  # Exibe a resposta da página
            #print(pagina+"/"+last_page)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON na página {pagina}")
            sys.exit(1)

        # Verifica se há dados no campo "data"
        transacoes = dados.get("transacoes", {}).get("data", [])
        if not transacoes:
            print(f"Sem dados na página {pagina}. Continuando para a próxima...")
            continue

        print(f"Página {pagina} processada com {len(transacoes)} transações."," ",pagina,"/",last_page)
        print("*" * 50)

        # Adiciona as transações da página atual à lista geral
        todas_paginas.extend(transacoes)

    # Criação do DataFrame após o loop
    df = pd.DataFrame(todas_paginas)

    # Trata caracteres especiais e valores nulos
    df = df.applymap(
        lambda x: x.replace("'", "''") if isinstance(x, str) else x
    )

    colunas_selecionadas = ["id",
    "status",
    "status_capture",
    "acquirer_response_code",
    "acquirer_name",
    "acquirer_id",
    "authorization_code",
    "tef_nsu",
    "uuid",
    "nsu",
    "amount",
    "amount_operation",
    "fee_operation",
    "refunded_amount",
    "custo_mdr",
    "custo_adquirente",
    "valor_interchange",
    "valor_taxa_administracao",
    "installments",
    "merchant_id",
    "merchant_key",
    "merchant_ref_externa",
    "merchant_name",
    "merchant_document_number",
    "card_holder_name",
    "card_first_digits",
    "card_last_digits",
    "card_brand",
    "card_pin_mode",
    "payment_method",
    "capture_method",
    "capture_partner",
    "device_serial_number",
    "vl_comissao",
    "ecommerce",
    "conta_adquirente",
    "merchant_code_sitef",
    "pv",
    "logic_number",
    "valor_cancelado",
    "blocked_payables_count",
    "custo_adicional",
    "resolucao_captura",
    "resolucao_adquirente",
    "tipo_resolucao",
    "start_date",
    "finish_date",
    "confirmation_date",
    "payment_date",
    "status_capture_date",
    "created_at",
    "updated_at",
    "deleted_at"
    ]

    df_reduzido = df[colunas_selecionadas]

    df_reduzido["merchant_name"] = df_reduzido["merchant_name"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    df_reduzido["card_holder_name"] = df_reduzido["card_holder_name"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    print("Dados Consolidados:")

    try:
        df_reduzido["start_date"] = df_reduzido["start_date"].replace("0000-00-00 00:00:00", None)
        df_reduzido["finish_date"] = df_reduzido["finish_date"].replace("0000-00-00 00:00:00",None)
        df_reduzido["confirmation_date"] = df_reduzido["confirmation_date"].replace("0000-00-00 00:00:00", None)
        df_reduzido["payment_date"] = df_reduzido["payment_date"].replace("0000-00-00 00:00:00",None)
        df_reduzido["status_capture_date"] = df_reduzido["status_capture_date"].replace("0000-00-00 00:00:00",None)
        df_reduzido["created_at"] = df_reduzido["created_at"].replace("0000-00-00 00:00:00",None)
        df_reduzido["updated_at"] = df_reduzido["updated_at"].replace("0000-00-00 00:00:00",None)
        df_reduzido["deleted_at"] = df_reduzido["deleted_at"].replace("0000-00-00 00:00:00",None)

    except Exception as ex:
        print("\n-> Erro na tranformacao das colunas do dataframe!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)


    try:
        # Inserindo os registros no banco de dados 
        fn_inserirRegistros(cnx.conn,df_reduzido,"extract.mvp_transacoes")
        run_procedure('extract.sp_merger_mvp_transacoes()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

    except Exception as ex:
        print("\n-> Erro na procedure de merge!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

get_mvp_transacoes()