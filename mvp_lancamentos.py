
import pandas as pd
import json
import sys
import os
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_mvp
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import run_procedure
from sys_funcaoInserirLog import fn_inserirLog
import re

pid = "'"+str(os.getpid())+"'"
script = "'"+str(os.path.basename(__file__))+"'"
projeto = "'carga datalake'"
etapa = "'extração'"

def get_mvp_lancamentos():

    try:

        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_lancamentos"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'"+carga_parametro+"'", 'null')

    except Exception as ex:
        print("\n-> Erro na parametrizacao!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    try:

        if carga_parametro:
            valores = carga_parametro.split('*') 
            
            url = valores[0]  # "API_Lancamentos"
            start_date = valores[1]  # "2025-01-01"
            finish_date = valores[2]  # "2025-01-05"

            # Configura os parâmetros da API
            parametro = {
                "start_date": start_date,
                "finish_date": finish_date,
                "filter_by": "updated_date",
                "page": 1
            }

            print(f"Parâmetros configurados: {parametro}")

            requisicao_inicial = get_dados_mvp(url, parametro)

            if requisicao_inicial.status_code != 200:
                print(f"Erro na requisição inicial: {requisicao_inicial.status_code}")
                exit()

    except Exception as ex:
        print("\n-> Erro no parametro de datas!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)
        

    try:
        resposta_inicial = requisicao_inicial.json()
        print("Resposta inicial completa:")
        last_page = resposta_inicial.get("operacoes", {}).get("lastPage", 1)  # Garante que `lastPage` seja obtido corretamente
        print(f"Número total de páginas: {last_page}")
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON na requisição inicial.")
        exit()

    todas_paginas = []

    for pagina in range(1,last_page + 1):
        parametro["page"] = pagina

        # Requisição para cada página
        requisicao = get_dados_mvp(url,parametro)

        if requisicao.status_code != 200:
            print(f"Erro na página {pagina}: {requisicao.status_code}")
            break

        try:
            dados = requisicao.json()
            print(f"Resposta da página {pagina}:")

        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON na página {pagina}")
            break

        Lancamentos = dados.get("operacoes", {}).get("data", [])

        if not Lancamentos:
            print(f"Sem dados na página {pagina}. Continuando para a próxima...")
            continue

        print(f"Página {pagina} processada com {len(Lancamentos)} operações. {pagina}/{last_page}")
        print("*" * 50)

        
        todas_paginas.extend(Lancamentos)
        

    # Criação do DataFrame após o loop
    df_Lancamentos = pd.DataFrame(todas_paginas)

    df = df_Lancamentos.applymap(
        lambda x: x.replace("'", "''") if isinstance(x, str) else x
    )

    df_Lancamentos["razao_social"] = df_Lancamentos["razao_social"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    df_Lancamentos["nome_distribuidor"] = df_Lancamentos["nome_distribuidor"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    df_Lancamentos["descricao"] = df_Lancamentos["descricao"].astype(str).apply(
    lambda x: re.sub(r"[\u00A0\u200B\u200C\u200D\uFEFF]", " ", x).replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    df_Lancamentos["approved_by"] = df_Lancamentos["approved_by"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    colunas_selecionadas = [
    "id",
    "uuid",
    "codigoEC",
    "cpf_cnpj",
    "razao_social",
    "codigo_distribuidor",
    "cpf_cnpj_distribuidor",
    "nome_distribuidor",
    "transacao_id",
    "nsu_lancamento",
    "nsu_transacao",
    "origem_lancamento",
    "parcela",
    "total_parcelas",
    "data_ajuste",
    "tipo_lancamento",
    "data_vencimento",
    "codigo_lancamento",
    "valor_total",
    "valor_liquido",
    "valor_pago",
    "descricao",
    "situacao",
    "approved_by",
    "approved_at",
    "created_by",
    "data_lancamento",
    "updated_at",
    "data_pagamento",
    "nsu"
    ]

    df_lancamento_reduzido = df_Lancamentos[colunas_selecionadas]

    print("Dados Consolidados:")

    try:
        df_lancamento_reduzido["data_ajuste"] = df_lancamento_reduzido["data_ajuste"].replace("0000-00-00 00:00:00", None)
        df_lancamento_reduzido["data_vencimento"] = df_lancamento_reduzido["data_vencimento"].replace("0000-00-00 00:00:00", None)
        df_lancamento_reduzido["data_lancamento"] = df_lancamento_reduzido["data_lancamento"].replace("0000-00-00 00:00:00", None)
        df_lancamento_reduzido["updated_at"] = df_lancamento_reduzido["updated_at"].replace("0000-00-00 00:00:00", None)

    except Exception as ex:
        print("\n-> Erro na tranformacao das colunas do dataframe!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    try:
        # Inserindo os registros no banco de dados 
        fn_inserirRegistros(cnx.conn,df_lancamento_reduzido,"extract.mvp_lancamentos")
        run_procedure('extract.sp_merger_mvp_lancamentos()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')
        
    except Exception as ex:
        print("\n-> Erro na procedure de merge!")
        erro_formatado = "'"+str(ex).replace("'", "")+"'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)
get_mvp_lancamentos()
