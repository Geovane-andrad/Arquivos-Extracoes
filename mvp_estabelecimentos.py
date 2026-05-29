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
import re



def get_estabelecimentos_mvp():

    #Variáveis para log (opcional)
    pid = "'" + str(os.getpid()) + "'"
    script = "'" + str(os.path.basename(__file__)) + "'"
    projeto = "'carga datalake'"
    etapa = "'extração'"

    try:
        # Log de início (opcional)
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

        nome_carga = "mvp_estabelecimentos"
        carga_parametro = get_parametroCarga_mvp(nome_carga)

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
                # print(requisicao_inicial.text)
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
        estabelecimentos = dados.get("data", [])  # Agora estabelecimentos é uma lista
        if not estabelecimentos:
            print(f"Sem dados na página {pagina}. Continuando para a próxima...")
            continue

        print(f"Página {pagina} processada com {len(estabelecimentos)} estabelecimentos. ", pagina, "/", last_page)
        print("*" * 50)

        todas_paginas.extend(estabelecimentos)

    # Cria o DataFrame com todas as páginas
    df_estabelecimentos = pd.DataFrame(todas_paginas)

    # Mapeamento de colunas para padronizar os nomes
    mapeamento_colunas = {
        'codigoCliente': 'codigocliente',
        'referenciaExterna': 'referenciaexterna',
        'recipient_id': 'recipient_id',
        'planoId': 'planoid',
        'planoNome': 'planonome',
        'codigoVendedor': 'codigovendedor',
        'nomeVendedor': 'nomevendedor',
        'grupoEconomicoId': 'grupoeconomicoid',
        'grupoEconomicoNome': 'grupoeconomiconome',
        'cpfCnpj': 'cpfcnpj',
        'dataFundacao': 'datafundacao',
        'razaoSocial': 'razaosocial',
        'tipoEmpresa': 'tipoempresa',
        'nomeFantasia': 'nomefantasia',
        'contatoPrincipal': 'contatoprincipal',
        'urlEcommerce': 'urlecommerce',
        'horarioFuncionamento': 'horariofuncionamento',
        'localizadoShopping': 'localizadoshopping',
        'faturamentoMensal': 'faturamentomensal',
        'sincronizarData': 'sincronizardata',
        'sincronizarEDI': 'sincronizaredi',
        'bloquearLiquidacao': 'bloquearliquidacao',
        'transferenciaAutomatica': 'transferenciaautomatica',
        'transferenciaValorMinimo': 'transferenciavalorminimo',
        'transferenciaPeriodicidade': 'transferenciaperiodicidade',
        'divisaoTransferenciaEntreContasBancarias': 'divisaotransferenciaentrecontasbancarias',
        'antecipacaoRecebiveis': 'antecipacaorecebiveis',
        'percentualAntecipacao': 'percentualantecipacao',
        'tipoAntecipacao': 'tipoantecipacao',
        'periodoCarencia': 'periodocarencia',
        'ordemAntecipacao': 'ordemantecipacao',
        'dataAntecipacao': 'dataantecipacao',
        'AntecipacaoAppEC': 'antecipacaoappec',
        'anteciparApos': 'anteciparapos',
        'jurosCompostoAntecipacao': 'juroscompostoantecipacao',
        'dataInicioVigorJurosComposto': 'datainiciovigorjuroscomposto',
        'valorPatrimonio': 'valorpatrimonio',
        'inscricaoEstadual': 'inscricaoestadual',
        'inscricaoFazenda': 'inscricaofazenda',
        'sincronizacao': 'sincronizacao',
        'informeRegistradora': 'informeregistradora',
        'descricao': 'descricao',
        'analista_relacionamento': 'analista_relacionamento',
        'unidade_negocio_id': 'unidade_negocio_id',
        'unidade_negocio_nome': 'unidade_negocio_nome',
        'modeloCobrancaChargeback': 'modelocobrancachargeback',
        'modeloCobrancaCancelamento': 'modelocobrancacancelamento',
        'situacao': 'situacao',
        'motivoDescredenciamento': 'motivodescredenciamento',
        'dataDescredenciamento': 'datadescredenciamento',
        'created_at': 'created_at',
        'updated_at': 'updated_at'
    }

    # Renomeia as colunas do DataFrame
    df_estabelecimentos_renomeado = df_estabelecimentos.rename(columns=mapeamento_colunas)

    # Trata caracteres especiais e valores nulos
    df_estabelecimentos_corrigido = df_estabelecimentos_renomeado.applymap(
        lambda x: x.replace("'", "''") if isinstance(x, str) else x
    )

    # Lista de colunas válidas na tabela do PostgreSQL
    colunas_validas = [
        'codigocliente', 'referenciaexterna', 'recipient_id', 'planoid', 'planonome',
        'codigovendedor', 'nomevendedor', 'grupoeconomicoid', 'grupoeconomiconome',
        'cpfcnpj', 'datafundacao', 'razaosocial', 'tipoempresa', 'nomefantasia',
        'contatoprincipal', 'urlecommerce', 'horariofuncionamento', 'localizadoshopping',
        'faturamentomensal', 'sincronizardata', 'sincronizaredi', 'bloquearliquidacao',
        'transferenciaautomatica', 'transferenciavalorminimo', 'transferenciaperiodicidade',
        'divisaotransferenciaentrecontasbancarias', 'antecipacaorecebiveis',
        'percentualantecipacao', 'tipoantecipacao', 'periodocarencia', 'ordemantecipacao',
        'dataantecipacao', 'antecipacaoappec', 'anteciparapos', 'juroscompostoantecipacao',
        'datainiciovigorjuroscomposto', 'valorpatrimonio', 'inscricaoestadual',
        'inscricaofazenda', 'sincronizacao', 'informeregistradora', 'descricao',
        'analista_relacionamento', 'unidade_negocio_id', 'unidade_negocio_nome',
        'modelocobrancachargeback', 'modelocobrancacancelamento', 'situacao',
        'motivodescredenciamento', 'datadescredenciamento', 'created_at', 'updated_at'
    ]

    # Filtra apenas as colunas válidas
    df_estabelecimentos_col_valido = df_estabelecimentos_corrigido[colunas_validas]

    # Trata campos de texto para evitar problemas com aspas
    df_estabelecimentos_col_valido["descricao"] = df_estabelecimentos_col_valido["descricao"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )
    df_estabelecimentos_col_valido["motivodescredenciamento"] = df_estabelecimentos_col_valido["motivodescredenciamento"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )
    df_estabelecimentos_col_valido["nomefantasia"] = df_estabelecimentos_col_valido["nomefantasia"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )
    df_estabelecimentos_col_valido["razaosocial"] = df_estabelecimentos_col_valido["razaosocial"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
    )

    def limpar_faturamento(valor):
        if pd.isna(valor):
            return 0.0
        # Remove tudo que não for dígito
        valor_numerico = re.sub(r"[^\d]", "", str(valor))
        if not valor_numerico:
            return 0.0
        # Interpreta as duas últimas casas como centavos
        valor_float = int(valor_numerico) / 100
        return round(valor_float, 2)

    df_estabelecimentos_col_valido["faturamentomensal"] = (
        df_estabelecimentos_col_valido["faturamentomensal"]
        .apply(limpar_faturamento)
    )

    print("Dados consolidados")

    try:
        # Inserindo os registros no banco de dados
        fn_inserirRegistros(cnx.conn, df_estabelecimentos_col_valido, "extract.mvp_estabelecimentos")
        run_procedure('extract.sp_merger_mvp_estabelecimentos()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

    except Exception as ex:
        print("\n-> Erro ao inserir informações do banco!")
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(ex)
        sys.exit(1)
get_estabelecimentos_mvp