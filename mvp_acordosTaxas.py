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

try:
    # Log de início (opcional)
    fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

    nome_carga = "mvp_acordosTaxas"
    carga_parametro = get_parametroCarga_mvp(nome_carga)

    # Log de parametrização (opcional)
    fn_inserirLog(cnx.conn, 'parametrizar', pid, script, projeto, etapa, "'" + carga_parametro + "'", 'null')

except Exception as ex:
    print("\n-> Erro na parametrizacao!")
    erro_formatado = "'" + str(ex).replace("'", "") + "'"
    fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
    print(ex)
    sys.exit()

try:
    if carga_parametro:
        valores = carga_parametro.split()
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
            sys.exit()

except Exception as ex:
    print("\n-> Erro no split de datas!")
    erro_formatado = "'" + str(ex).replace("'", "") + "'"
    fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
    print(ex)
    sys.exit()

try:
    resposta_inicial = requisicao_inicial.json()
    print("Resposta inicial completa:")
    last_page = resposta_inicial.get("lastPage", 1)  # Garante que `lastPage` seja obtido corretamente
    print(f"Número total de páginas: {last_page}")

except json.JSONDecodeError:
    print("Erro ao decodificar JSON na requisição inicial.")
    sys.exit()

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
    acordosTaxas = dados.get("data", [])  #agora os dados se transformaram em lista
    if not acordosTaxas:
        print(f"Sem dados na página {pagina}. Continuando para a próxima...")
        continue

    print(f"Página {pagina} processada com {len(acordosTaxas)} acordos de taxas. ", pagina, "/", last_page)
    print("*" * 50)

    todas_paginas.extend(acordosTaxas)

# Cria o DataFrame com todas as páginas
df_acordosTaxas = pd.DataFrame(todas_paginas)

# Trata caracteres especiais e valores nulos
df_acordosTaxas_corrigido = df_acordosTaxas.applymap(
    lambda x: x.replace("'", "''") if isinstance(x, str) else x
)

colunas_validas = [
    'id',
'merchants_id',
'rates_id',
'codigoAdquirente',
'MCC',
'mdr_ecommerce',
'mdr_presencial',
'antecipacao_spot',
'antecipacao_rav',
'spot_online',
'rav_online',
'valor_min_transacao',
'custo_transacao',
'custo_transacao_presencial',
'custo_transacao_ecommerce',
'tipo',
'dias_pgto',
'codigoBandeira',
'nomeBandeira',
'produto',
'created_at',
'updated_at'
]

df_acordosTaxas_col_valido = df_acordosTaxas_corrigido[colunas_validas]

print("Dados consolidados")

try:
    # Inserindo os registros no banco de dados
    fn_inserirRegistros(cnx.conn, df_acordosTaxas_col_valido, "extract.mvp_acordostaxas")
    run_procedure('extract.sp_merger_mvp_acordostaxas()')
    fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')

except Exception as ex:
    print("\n-> Erro ao inserir informações do banco!")
    erro_formatado = "'" + str(ex).replace("'", "") + "'"
    fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
    print(ex)
    sys.exit()
