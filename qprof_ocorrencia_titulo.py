
import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys
import json
from datetime import datetime, timezone
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcaoInserirLog import fn_inserirLog
from sys_funcoesBanco import get_parametroCarga
from sys_funcoesBanco import run_procedure
import sys_conexaoOdata as odatas

def get_qprof_ocorrencia_titulo():

  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_ocorrenciaTitulo'"
      parametro_carga =  get_parametroCarga(nome_carga)

      fn_inserirLog(cnx.conn, 'parametrizar' , pid, script, projeto, etapa, "'"+parametro_carga+"'", 'null')
      
      df = odatas.get_dadosOdata(parametro_carga)
      print("Registros do odata: "+str(len(df)))

  except Exception as ex:
    print("")
    print("-> Erro na carga do odata!")
    fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
    print(ex)
    sys.exit(1)

  if len(df.index)>0:

    try:
      nulo = "null"
      df = df.where(pd.notnull(df), nulo)
      
      df["DESCRICAO"] = df["DESCRICAO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        )
      df["OBSERVACAO"] = df["OBSERVACAO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        ) 

      df_final = df[[
      'NUMERO_SEQUENCIAL_OCORRENCIA',
      'CODIGO_OCORRENCIA',
      'CODIGO_EMPRESA',
      'CODIGO_FILIAL',
      'NUMERO_SEQUENCIAL_TITULO',
      'DATA_OCORRENCIA',
      'CODIGO_PESSOA',
      'VALOR_TIPO',
      'DESCRICAO',
      'SITUACAO',
      'OBSERVACAO',
      'DATA_ACOMPANHAMENTO',
      'INDICADOR_CONFIRMA_BAIXA_TITULO',
      'CODIGO_USUARIO_CRIACAO',
      'DATA_CRIACAO',
      'CODIGO_USUARIO_ATUALIZACAO',
      'DATA_ATUALIZACAO'
      ]]
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_ocorrencia_titulo")
      run_procedure('extract.sp_merge_qprof_ocorrencia_titulo()')
      fn_inserirLog(cnx.conn, 'finalizar' , pid, script, projeto, etapa, "'x'", "'x'")

    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe para tabela!")
      print(f"Erro: {ex}")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

  else:
    fn_inserirLog(cnx.conn, 'dfVazio' , pid, script, projeto, etapa, "'"+parametro_carga+"'", 'null')
    print("")
    return print("-> Odata sem registros")

get_qprof_ocorrencia_titulo()