
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

def get_qprof_endereco_pessoa():

  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_endereco_pessoa'"
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
        'CODIGO_PESSOA',
        'TIPO_ENDERECO',
        'ENDERECO_PESSOA',
        'ENDERECO_NUMERO',
        'ENDERECO_BAIRRO',
        'ENDERECO_CIDADE',
        'ENDERECO_UF',
        'ENDERECO_CEP',
        'ENDERECO_COMPLEMENTO',
        'TELEFONE_1_DDD',
        'TELEFONE_1',
        'TELEFONE_2_DDD',
        'TELEFONE_2',
        'CELULAR_DDD',
        'CELULAR',
        'TELEFONE_0800',
        'FAX_DDD',
        'FAX',
        'INDICADOR_FAX_NOTURNO',
        'EMAIL',
        'INDICADOR_EMAIL_ERRADO',
        'OBS_EMAIL_ERRADO',
        'INDICADOR_TELEFONE_INF_ERRADO',
        'DATA_TELEFONE_INF_ERRADO',
        'CODIGO_USUARIO_TELEFONE_INF_ERRADO',
        'OBSERVACAO_TELEFONE_INF_ERRADO',
        'TELEFONE_DDD_INF_CEDENTE',
        'TELEFONE_INF_CEDENTE',
        'EMAIL_INF_CEDENTE',
        'DATA_INF_EMAIL',
        'CODIGO_USUARIO_INF_EMAIL',
        'DATA_TELEFONE_INF_CORRIGIDO',
        'CODIGO_USUARIO_TELEFONE_INF_CORRIGIDO',
        'DATA_ULT_ALTERACAO',
        'CODIGO_USUARIO_ULT_ALTERACAO',
        'CODIGO_USUARIO_ATUALIZACAO_END_OPERACAO',
        'DATA_ALTUALIZACAO_END_OPERACAO',
        'CODIGO_USUARIO_ATUALIZACAO',
        'DATA_ATUALIZACAO'
      ]]

      df_final["ENDERECO_PESSOA"] = df_final["ENDERECO_PESSOA"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["ENDERECO_BAIRRO"] = df_final["ENDERECO_BAIRRO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["ENDERECO_CIDADE"] = df_final["ENDERECO_CIDADE"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["EMAIL"] = df_final["EMAIL"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )

      df_final["ENDERECO_COMPLEMENTO"] = df_final["ENDERECO_COMPLEMENTO"].astype(str).apply(
        lambda x: x.replace("'", "").replace('"', "") if isinstance(x, str) else x
      )
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, 'extract."qprof_enderecoPessoa"')
      run_procedure('extract.sp_merge_qprof_endereco_pessoa()')
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
    
get_qprof_endereco_pessoa()