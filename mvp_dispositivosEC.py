import json
import sys
import os
import requests as r
import pandas as pd
import sys_conexaoOdata as odatas
import sys_conexaoBanco as cnx
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import get_parametroCarga_mvp
from sys_funcoesBanco import run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirLog import fn_inserirLog

# Variáveis para log (opcional)
pid = "'" + str(os.getpid()) + "'"
script = "'" + str(os.path.basename(__file__)) + "'"
projeto = "'carga datalake'"
etapa = "'extração'"

def get_dispositivos_ec_mvp():

    try:
        # Log de início (opcional)
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_dispositivos_ec"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

        # Log de parametrização (opcional)
        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'" + carga_parametro + "'", 'null')

    except Exception as ex:
        print("\n-> Erro na parametrizacao!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    try:
        if carga_parametro:
            valores = carga_parametro.split('*')
            url = valores[0]  # URL da API

            # Configura os parâmetros da API
            parametro = {
                "filter_date_by": "updated_date",
                "page": 1
            }
            print(f"Parâmetros configurados: {parametro}")

            # Requisição inicial para obter o número de páginas
            requisicao_inicial = get_dados_mvp(url, parametro)

            if requisicao_inicial.status_code != 200:
                print(f"Erro na requisição inicial: {requisicao_inicial.status_code}")
                sys.exit(1)

    except Exception as ex:
        print("\n-> Erro no split de datas!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)

    try:
        resposta_inicial = requisicao_inicial.json()
        print("Resposta inicial completa:")
        last_page = resposta_inicial.get("lastPage", 1)  # Garante que `lastPage` seja obtido corretamente
        print(f"Número total de páginas: {last_page}")

    except json.JSONDecodeError:
        print("Erro ao decodificar JSON na requisição inicial.")
        sys.exit(1)

    # Lista para armazenar todas as páginas
    todas_paginas = []

    # Loop para processar todas as páginas
    for pagina in range(1, last_page + 1):
        parametro["page"] = pagina

        # Requisição para cada página
        requisicao = get_dados_mvp(url, parametro)

        if requisicao.status_code != 200:
            print(f"Erro na página {pagina}: {requisicao.status_code}")
            break

        try:
            dados = requisicao.json()
            print(f"Resposta da página {pagina}:")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON na página {pagina}")
            break

        # Verifica se há dados no campo "data"
        Dispositivos_EC = dados.get("data", [])  # Agora estabelecimentos é uma lista
        if not Dispositivos_EC:
            print(f"Sem dados na página {pagina}. Continuando para a próxima...")
            continue

        print(f"Página {pagina} processada com {len(Dispositivos_EC)} estabelecimentos. ", pagina, "/", last_page)
        print("*" * 50)

        todas_paginas.extend(Dispositivos_EC)

    # Cria o DataFrame com todas as páginas
    df_Dispositivos_ec = pd.DataFrame(todas_paginas)

    # Trata caracteres especiais e valores nulos
    df_Dispositivos_ec = df_Dispositivos_ec.applymap(
        lambda x: x.replace("'", "''") if isinstance(x, str) else x
    )

    colunas_validas = [
    'id',
    'numero_logico',
    'codigo_ec',
    'razao_social',
    'cpf_cnpj',
    'codigo_captura',
    'finalidade',
    'modelo',
    'valor',
    'taxa_adesao',
    'carencia',
    'isencao_debito',
    'isencao_credito',
    'data_ativacao',
    'data_finalizacao',
    'departamento_id',
    'tipo_tecnologia',
    'numero_dispositivo',
    'sim_card',
    'plano',
    'data_vinculo_plano',
    'descricao',
    'situacao',
    'termo_tef',
    'tid',
    'codigo_otp',
    'created_at',
    'updated_at',
    'blokko_id'
    ]

    df_Dispositivos_ec_col_validas = df_Dispositivos_ec[colunas_validas]

    # Trata campos de texto para evitar problemas com aspas
    df_Dispositivos_ec_col_validas["razao_social"] = df_Dispositivos_ec_col_validas["razao_social"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    df_Dispositivos_ec_col_validas["descricao"] = df_Dispositivos_ec_col_validas["descricao"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    # Lista de colunas que devem ser datetime
    colunas_data = [
        "data_ativacao",
        "data_finalizacao",
        "data_vinculo_plano",
        "created_at",
        "updated_at"
    ]

    # Converte as colunas para datetime e substitui valores inválidos por NaT
    for coluna in colunas_data:
        df_Dispositivos_ec_col_validas[coluna] = pd.to_datetime(
            df_Dispositivos_ec_col_validas[coluna], 
            errors='coerce'
        )

    # Converte valores NaT para NULL e formata corretamente para PostgreSQL
    for coluna in colunas_data:
        df_Dispositivos_ec_col_validas[coluna] = df_Dispositivos_ec_col_validas[coluna].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
        )

    try:
        # Inserindo os registros no banco de dados
        fn_inserirRegistros(cnx.conn, df_Dispositivos_ec_col_validas, "extract.mvp_dispositivos_ec")
        run_procedure('extract.sp_merger_mvp_dispositivos_ec()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

    except Exception as ex:
        print("\n-> Erro ao inserir informações do banco!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)
