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
import datetime
import pytz


pid = "'" + str(os.getpid()) + "'"
script = "'" + str(os.path.basename(__file__)) + "'"
projeto = "'carga datalake'"
etapa = "'extração'"


def get_mvp_antecipacoes():
    try:
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')
        nome_carga = "mvp_antecipacoes"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'" + carga_parametro + "'", 'null')

    except Exception as ex:
        print("\n-> Erro na parametrizacao!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        sys.exit(1)

    try:
        if carga_parametro:
            valores = carga_parametro.split('*')
            url = valores[0]
            start_date = valores[1]
            finish_date = valores[2]
            filter_date_by = valores[3]

            parametro = {
                "start_date": start_date,
                "finish_date": finish_date,
                "filter_date_by": filter_date_by,
                "limit": 50,
                "direction": "next"
            }

            print(f"Parâmetros configurados: {parametro}")

    except Exception as ex:
        print("\n-> Erro ao interpretar os parâmetros de carga!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        sys.exit(1)

    cursor = None
    todas_paginas = []

    while True:
        if cursor:
            parametro["cursor"] = cursor
        else:
            parametro.pop("cursor", None)

        requisicao = get_dados_mvp(url, parametro)

        if requisicao.status_code != 200:
            print(f"Erro na requisição: {requisicao.status_code}")
            print(f"Resposta: {requisicao.text}")
            sys.exit(1)

        try:
            resposta = requisicao.json()
        except json.JSONDecodeError:
            print("Erro ao decodificar JSON")
            sys.exit(1)

        dados = resposta.get("data", [])
        if not dados:
            print("Sem dados retornados, encerrando extração.")
            sys.exit(1)

        total_extraidos = len(todas_paginas) + len(dados)

        print(f"Total de registros acumulado: {total_extraidos}")

        # Data/hora do log

#        fuso_horario = pytz.timezone("America/Sao_Paulo")
#        now = datetime.datetime.now(fuso_horario)
#        print(f"""
#        [ETL - EXTRAÇÃO] {now}
#        → Registros extraídos nesta página: {len(dados)}
#        → Total acumulado até agora: {total_extraidos}
#        → Próximo cursor: {resposta.get("next_cursor")}
#        ------------------------------------------------------------
#        """)

        # Atualiza dados e cursor
        todas_paginas.extend(dados)
        cursor = resposta.get("next_cursor")

        if not cursor:
            print("Última página alcançada.")
            break

    # Criação do DataFrame
    df = pd.DataFrame(todas_paginas)

    # Trata caracteres especiais e valores nulos
    df = df.applymap(lambda x: x.replace("'", "''") if isinstance(x, str) else x)

    df["social_reason"] = df["social_reason"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    colunas_selecionadas = [
        "id",
        "merchants_id",
        "document_number",
        "social_reason",
        "solicitation_key",
        "identifier",
        "transaction_id",
        "payable_id",
        "nsu",
        "authorization_code",
        "installment",
        "amount",
        "fee",
        "cost_acquirer_anticipation",
        "net_amount",
        "tax_applied",
        "anticipation_days",
        "status",
        "timeframe",
        "type",
        "approved_user_id",
        "acquirer_id",
        "approval_limit",
        "transaction_date",
        "original_payment_date",
        "payment_date",
        "payment_status",
        "capture_partner",
        "created_at",
        "updated_at"
    ]

    df_antecipacoes_reduzido = df[colunas_selecionadas]

    try:
        df_antecipacoes_reduzido["approval_limit"] = df_antecipacoes_reduzido["approval_limit"].replace("0000-00-00 00:00:00", None)
        df_antecipacoes_reduzido["transaction_date"] = df_antecipacoes_reduzido["transaction_date"].replace("0000-00-00 00:00:00", None)
        df_antecipacoes_reduzido["original_payment_date"] = df_antecipacoes_reduzido["original_payment_date"].replace("0000-00-00 00:00:00", None)
        df_antecipacoes_reduzido["created_at"] = df_antecipacoes_reduzido["created_at"].replace("0000-00-00 00:00:00", None)
        df_antecipacoes_reduzido["updated_at"] = df_antecipacoes_reduzido["updated_at"].replace("0000-00-00 00:00:00", None)

    except Exception as ex:
        print("\n-> Erro na transformação das colunas do dataframe!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        sys.exit(1)

    try:
        # Inserindo os registros no banco de dados
        fn_inserirRegistros(cnx.conn, df_antecipacoes_reduzido, "extract.mvp_antecipacoes")
        run_procedure('extract.sp_merger_mvp_antecipacoes()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

    except Exception as ex:
        print("\n-> Erro na procedure de merge!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        sys.exit(1)

get_mvp_antecipacoes()