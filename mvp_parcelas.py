import pandas as pd
import json
import sys
import requests 
from sys_funcaoInserirTabela import fn_inserirRegistros
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_mvp
from sys_funcoesBanco import run_procedure
import os
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirLog import fn_inserirLog
import sys_conexaoOdata as odatas
import time

# Aqui começa o código para inserir os logs na tabala no banco de dados
#_______________________________________________________________________________________________________________
pid = "'"+str(os.getpid())+"'"
script = "'"+str(os.path.basename(__file__))+"'"
projeto = "'carga datalake'"
etapa = "'extração'"

def get_mvp_parcelas():

    try:
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_parcelas"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        if not carga_parametro:
            print("\n-> Nenhum novo período encontrado. Finalizando execução.")

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'"+carga_parametro+"'", 'null')

    except Exception as ex:
        print("\n-> Erro na parametrização!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    try:    
        valores = carga_parametro.split('*')

        if len(valores) < 3:
            print(f"\n-> Erro: Parâmetros insuficientes ({len(valores)} encontrados, esperado 4). Dados recebidos: {valores}")
            sys.exit()

        url = valores[0]  
        start_date = valores[1]  
        finish_date = valores[2]  
        filter_date_by = valores[3]

        parametro = {
            "start_date": start_date,
            "finish_date": finish_date,
            "filter_by": filter_date_by
        }

        print(f"Parâmetros configurados: {parametro}")

    except Exception as ex:
        print("\n-> Erro na parametrização!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    # ============================ REQUISIÇÃO À API ============================

    try:
        requisicao = get_dados_mvp(url, parametro)

        if requisicao.status_code != 200:
            print(f"Erro na requisição: {requisicao.status_code}")
            print(requisicao.text)
            sys.exit()

        try:
            dados = requisicao.json()

        except json.JSONDecodeError:
            print("Erro ao decodificar JSON")
            sys.exit(1)

        # ============================ PROCESSAMENTO DOS DADOS ============================

        parcelas = dados  

        df_parcelas = pd.DataFrame(parcelas)

        for col in ["estabelecimento", "cartao_nome"]:
            if col in df_parcelas.columns:
                df_parcelas[col] = df_parcelas[col].astype(str).str.replace("'", "").str.replace('"', "")

    except Exception as ex:
        print("\n-> Erro no processo de extração!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    colunas_selecionandas = [
        "recebivel_id",
        "transacao_id",
        "transacao_uuid",
        "merchants_id",
        "estabelecimento",
        "cpf_cnpj",
        "codigo_adquirente",
        "nome_adquirente",
        "nome_captura",
        "metodo_captura",
        "serial_number",
        "codigo_autorizacao",
        "codigo_moeda",
        "split_rule_id",
        "tef_nsu",
        "nsu",
        "valor_venda",
        "valor_venda_liquido",
        "cartao_nome",
        "cartao_inicial",
        "cartao_final",
        "bandeira",
        "forma_pagamento",
        "total_parcela",
        "parcela",
        "situacao_pagamento",
        "situacao_venda",
        "valor_bruto_parcela",
        "valor_liquido_parcela",
        "taxa_antecipacao_parcela",
        "interchange_fee_parcela",
        "taxa_cartao_parcela",
        "taxa_cartao_venda",
        "taxa_antecipacao_venda",
        "custo_cartao_adquirente",
        "custo_antecipacao_adquirente",
        "valor_pagamento_bandeira",
        "data_pagamento_bandeira",
        "data_pagamento",
        "data_original_pagamento",
        "data_transacao",
        "parcela_antecipada",
        "tipo_antecipacao_parcela",
        "taxa_proporcional_antecipacao_parcela",
        "data_antecipacao_parcela",
        "dias_antecipado_parcela",
        "created_at",
        "updated_at",
        "deleted_at" 
        ]
    
    df_parcelas_reduzido = df_parcelas[colunas_selecionandas]

    try:
        # Inserindo os registros no banco de dados 
        fn_inserirRegistros(cnx.conn, df_parcelas_reduzido, "extract.mvp_parcelas")
        run_procedure('extract.sp_merger_mvp_parcelas()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

        print(f"\n-> Período {start_date} a {finish_date} finalizado com sucesso. Iniciando próximo período...\n")

    except Exception as ex:
        print("\n-> Erro ao inserir registro!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)


get_mvp_parcelas()