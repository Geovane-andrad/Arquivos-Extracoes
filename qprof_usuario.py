
import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys
import json
from datetime import datetime, timezone

def get_qprof_usuario():


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
      
      nome_carga = "'qprof_usuario'"
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
        'CODIGO_USUARIO',
        'CODIGO_CENTRO_CONTROLE',
        'CODIGO_GRUPO_USUARIO',
        'CODIGO_USUARIO_CADASTROU',
        'CODIGO_USUARIO_SUBSTITUTO',
        'CODIGO_USUARIO_SUPERVISOR',
        'INDICADOR_USUARIO_FUNCIONARIO',
        'CARGO',
        'INDICADOR_AGENTE',
        'INDICADOR_RESPONSAVEL',
        'INDICADOR_ADVOGADO',
        'INDICADOR_COB_EXTERNA',
        'INDICADOR_POS_VENDA',
        'INDICADOR_EXPORTA_EXCEL',
        'INDICADOR_USUARIO_CEDENTE',
        'INDICADOR_CARTEIRA_SEGMENTADA',
        'EMAIL_INTERNO',
        'CODIGO_SETOR',
        'SITUACAO_USUARIO',
        'CODIGO_PESSOA_CEDENTE',
        'CODIGO_EVENTO_COMISSAO',
        'REGISTRO_OAB',
        'DESCRICAO_DIRETRIZ_OPER_AGENTE',
        'DESCRICAO_INF_PAG_AGENTE',
        'CODIGO_USUARIO_SERASA',
        'CODIGO_USUARIO_BOA_VISTA',
        'CODIGO_PESSOA_COB_EXTERNA',
        'CODIGO_PESSOA_ESCRITORIO_ADV',
        'CODIGO_USUARIO_ATUALIZACAO',
        'DATA_ATUALIZACAO'
      ]]
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_usuario")
      run_procedure('extract.sp_merge_qprof_usuario()')
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
  
get_qprof_usuario()