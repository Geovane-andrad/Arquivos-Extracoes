
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

def get_qprof_consulta_nfe():

  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_consulta_Nfe'"
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

      df_final = df[[
        'NUMERO_SEQUENCIAL_CONSULTA',
        'NUMERO_NFE',
        'DATA_CONSULTA',
        'CONTEUDO_CONSULTA',
        'DATA_EVENTO',
        'PROTOCOLO_EVENTO',
        'MENSAGEM_ERRO',
        'CODIGO_EVENTO',
        'CODIGO_USUARIO_ATUALIZACAO',
        'DATA_ATUALIZACAO'
      ]]

      df_final["CONTEUDO_CONSULTA"] = df_final["CONTEUDO_CONSULTA"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["PROTOCOLO_EVENTO"] = df_final["PROTOCOLO_EVENTO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["MENSAGEM_ERRO"] = df_final["MENSAGEM_ERRO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_consulta_Nfe")
      run_procedure('extract.sp_merger_qprof_consulta_nfe()')
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
  
get_qprof_consulta_nfe()