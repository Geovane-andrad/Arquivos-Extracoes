import pandas as pd
import sys
import os
from sys_funcaoInserirTabela import fn_inserirRegistros
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_mvp, run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirLog import fn_inserirLog

pid = f"'{os.getpid()}'"
script = f"'{os.path.basename(__file__)}'"
projeto = "'carga datalake'"
etapa = "'extração'"

def get_mvp_antecipacoes_paginada():

    try:
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_antecipacoes_paginada"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        if not carga_parametro:
            raise Exception("Parâmetro de carga vazio")

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, f"'{carga_parametro}'", 'null')

    except Exception as ex:
        print("Erro na parametrização:", ex)
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", f"'{str(ex)}'")
        sys.exit(1)

    try:
        valores = carga_parametro.split('*')

        url = valores[0]
        start_date = valores[1]
        finish_date = valores[2]

        parametro = {
            "start_date": start_date,
            "finish_date": finish_date,
            "filter_date_by": "updated_date",
            "page": 1
        }

        print(f"Parâmetros: {parametro}")

        requisicao_inicial = get_dados_mvp(url, parametro)

        if requisicao_inicial.status_code != 200:
            raise Exception(f"Erro inicial: {requisicao_inicial.status_code} - {requisicao_inicial.text}")

    except Exception as ex:
        print("Erro na requisição inicial:", ex)
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", f"'{str(ex)}'")
        sys.exit(1)

    try:
        resposta = requisicao_inicial.json()
        last_page = resposta.get("lastPage", 1)
        print(f"Total páginas: {last_page}")
    except Exception as ex:
        print("Erro ao ler JSON inicial:", ex)
        sys.exit(1)

    todas_paginas = []

    for pagina in range(1, last_page + 1):
        parametro["page"] = pagina

        try:
            req = get_dados_mvp(url, parametro)

            if req.status_code != 200:
                print(f"Erro página {pagina}: {req.status_code}")
                print(req.text)
                break

            dados = req.json()
            registros = dados.get("data", [])

            if not registros:
                print(f"Página {pagina} sem dados")
                break

            print(f"Página {pagina}/{last_page} - {len(registros)} registros")

            todas_paginas.extend(registros)

        except Exception as ex:
            print(f"Erro na página {pagina}:", ex)
            break

    if not todas_paginas:
        print("Nenhum dado retornado.")
        sys.exit(0)

    df = pd.DataFrame(todas_paginas)

    # garante colunas mesmo se faltar alguma
    colunas = [
        "id","merchants_id","document_number","social_reason","solicitation_key",
        "identifier","transaction_id","payable_id","nsu","authorization_code",
        "installment","amount","fee","cost_acquirer_anticipation","net_amount",
        "tax_applied","anticipation_days","status","timeframe","type",
        "approved_user_id","acquirer_id","approval_limit","transaction_date",
        "original_payment_date","payment_date","payment_status",
        "capture_partner","created_at","updated_at"
    ]

    for col in colunas:
        if col not in df.columns:
            df[col] = None

    df = df[colunas]

    # limpeza leve
    df["social_reason"] = df["social_reason"].astype(str).str.replace("'", "").str.replace('"', "")

    # datas inválidas
    for col in ["approval_limit","transaction_date","original_payment_date","created_at","updated_at"]:
        df[col] = df[col].replace("0000-00-00 00:00:00", None)

    try:
        fn_inserirRegistros(cnx.conn, df, "extract.mvp_antecipacoes")
        run_procedure('extract.sp_merger_mvp_antecipacoes()')

        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

    except Exception as ex:
        print("Erro ao inserir:", ex)
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", f"'{str(ex)}'")
        sys.exit(1)


get_mvp_antecipacoes_paginada()