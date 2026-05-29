
import pandas as pd
import os
import sys_conexaoBanco as cnx
import sys
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcaoInserirLog import fn_inserirLog
from sys_funcoesBanco import get_parametroCarga
from sys_funcoesBanco import run_procedure
import sys_conexaoOdata as odatas

def qprof_contrato_modalidade_grupo_rotulo():

  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_contrato_modalidade_grupo_rotulo'"
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
        'CODIGO_EMPRESA',
        'CODIGO_FILIAL',
        'CODIGO_PESSOA',
        'TIPO_CONTRATO',
        'NUMERO_CONTRATO',
        'CODIGO_GRUPO_ROTULO',
        'TAXA_DESAGIO',
        'LIMITE_OPERACAO',
        'CODIGO_USUARIO_ATUALIZACAO',
        'DATA_ATUALIZACAO'  
      ]]
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_contrato_modalidade_grupo_rotulo")
      #run_procedure('extract.sp_merge_qprof_contrato_modalidade_grupo_rotulo()')
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
  
qprof_contrato_modalidade_grupo_rotulo()