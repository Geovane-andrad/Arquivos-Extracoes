

import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys
from datetime import datetime, timezone

def get_qprof_hostoricoTitulo():


  from sys_funcaoInserirTabela import fn_inserirRegistros
  from sys_funcaoInserirLog import fn_inserirLog
  from sys_funcoesBanco import get_parametroCarga
  from sys_funcoesBanco import run_procedure
  import sys_conexaoOdata as odatas
  #from sys_funcoesTratamento import limpar_html, remove_quotes


  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_historicoTitulos'"
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
      df["OBSERVAÇÃO"] = df["OBSERVAÇÃO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
        ) 

      df_final = df[[
        'CODIGO_EMPRESA',
        'CODIGO_FILIAL',
        'SEQUENCIAL_TITULO',
        'CODIGO_SEQUENCIAL',
        'DATA',
        'DESCRICAO',
        'TIPO_OCORRENCIA',
        'OBSERVAÇÃO',
        'DATA_ATUALIZACAO',
        'CODIGO_USUARIO_ATUALIZACAO'
        ]]

    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)


    try: 
      
      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_historico_titulo") 
      run_procedure('extract.sp_merge_qprof_historico_titulo()')
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