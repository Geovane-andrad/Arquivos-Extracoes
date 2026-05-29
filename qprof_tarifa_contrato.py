
import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys
import json

def get_qprof_tarifa_contrato():


  from sys_funcaoInserirTabela import fn_inserirRegistros
  from sys_funcoesBanco import get_parametroCarga
  from sys_funcoesBanco import run_procedure
  import sys_conexaoOdata as odatas

  try:
      
      nome_carga = "'qprof_tarifa_contrato'"
      parametro_carga =  get_parametroCarga(nome_carga)
      
      df = odatas.get_dadosOdata(parametro_carga)
      print("Registros do odata: "+str(len(df)))

  except Exception as ex:
    print("")
    print("-> Erro na carga do odata!")
    print(ex)
    sys.exit(1)

  if len(df.index)>0:

    try:
      nulo = "null"
      df = df.where(pd.notnull(df), nulo)

      df_final = df[[
        'CODIGO_EMPRESA',
        'CODIGO_FILIAL',
        'CODIGO_FUNCAO',
        'CODIGO_PESSOA',
        'TIPO_CONTRATO',
        'NUMERO_CONTRATO',
        'CODIGO_TARIFA',
        'CODIGO_EVENTO',
        'CODIGO_TIPO_TITULO',
        'CODIGO_USUARIO',
        'DATA_ATUALIZACAO',
        'PERCENTUAL_TARIFA',
        'VALOR_TARIFA',
        'VALOR_TITULO_ATE',
        'VALOR_TITULO_DE'
      ]]
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, 'extract."tarifaContrato"')
      run_procedure('extract.sp_merge_qprof_tarifa_contrato()')


    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe para tabela!")
      print(f"Erro: {ex}")
      sys.exit(1)

  else:
    print("")
    return print("-> Odata sem registros")
  