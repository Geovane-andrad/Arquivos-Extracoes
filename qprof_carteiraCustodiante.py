

import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys


def get_qprof_carteiraCustodiante():


  from sys_funcaoInserirTabela import fn_inserirRegistros
  from sys_funcaoInserirLog import fn_inserirLog
  from sys_funcoesBanco import get_parametroCarga
  from sys_funcoesBanco import run_procedure
  import sys_conexaoOdata as odatas


  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')

      
      nome_carga = "'qprof_carteiraCustodiante'"
      parametro_carga =  get_parametroCarga(nome_carga)

      fn_inserirLog(cnx.conn, 'parametrizar' , pid, script, projeto, etapa, "'"+parametro_carga+"'", 'null')
      
      df_odata = odatas.get_dadosOdata(parametro_carga)
      
      print("Registros do odata: "+str(len(df_odata)))
      print("0")
      print(df_odata)
      df_filtrado = df_odata[(df_odata['INDICADOR_STATUS_PROCESSAMENTO'] == 'F')]

      ##df = df_filtrado.dropna(subset = ['CODIGO_INTEGRACAO_CUSTODIANTE'], how='all', inplace=True)
      ##df  = df_filtrado[df_filtrado['CODIGO_INTEGRACAO_CUSTODIANTE'].notna()]
      df=df_filtrado 

      print(df)


  except Exception as ex:
    print("")
    print("-> Erro na carga do odata!")
    fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
    print(ex)
    sys.exit(1)

  if len(df)!=0:

    try:

 
        df['DADOS_ARQUIVO']=df['DADOS_ARQUIVO'].astype(str)
        df['NOME_ARQUIVO']=df['NOME_ARQUIVO'].astype(str)
        df['DATA_ATUALIZACAO']=df['DATA_ATUALIZACAO'].astype(str)
        df['DATA_REFERENCIA']=df['DATA_REFERENCIA'].astype(str)
        df['CODIGO_CUSTODIANTE']=df['CODIGO_CUSTODIANTE'].astype(int)
        df['DATA_IMPORTACAO']=df['DATA_IMPORTACAO'].astype(str)
        df['DATA_INICIO_PROCESSAMENTO']=df['DATA_INICIO_PROCESSAMENTO'].astype(str)
        df['DATA_FIM_PROCESSAMENTO']=df['DATA_FIM_PROCESSAMENTO'].astype(str)
        df['INDICADOR_STATUS_PROCESSAMENTO']=df['INDICADOR_STATUS_PROCESSAMENTO'].astype(str)
        df['DESCRICAO_ERRO']=df['DESCRICAO_ERRO'].astype(str)


        ## --------------------------------- criando tabela final que irá receber os registros
        colunas= [
          '"CODIGO_EMPRESA"',
          '"CODIGO_FILIAL"',
          '"SEQUENCIAL_ARQUIVO"',
          '"nomeFundo"',
          '"docFundo"',
          '"dataFundo"',
          ## sumiu nomedestor e docgestor a partir de janeiro de 2025
          '"nomeGestor"',
          '"docGestor"',
          '"nomeOriginador"',
          '"docOriginador"',
          '"nomeCedente"',
          '"docCedente"',
          '"nomeSacado"',
          '"docSacado"',
          '"seuNumero"',
          '"numeroDocumento"',
          '"tipoRecebivel"',
          '"valorNominal"',
          '"valorPresente"',
          '"valorAquisicao"',
          '"valorPdd"',
          '"faixaPdd"',
          '"dataReferencia"',
          '"dataVencimentoOriginal"',
          '"dataVencimentoAjustada"',
          '"dataEmissao"',
          '"dataAquisicao"',  
          '"prazo"',
          '"prazoAnual"',
          '"situacaoRecebivel"',
          '"taxaCessao"',
          '"taxaRecebivel"',
          '"coobrigacao"'
          ]

        df_final = pd.DataFrame(columns=colunas)


          ## --------------------------------- loop para add valores na tabela finalc

        df = df.reset_index() 
        lista = []

        df.insert(0, "TABELA","")
        df['TABELA']= df['TABELA'].tolist()


        for index, row in df.iterrows():
            
            raw_bytes = base64.b64decode(df['DADOS_ARQUIVO'][index])

            try:
               # Tente primeiro com UTF-8
                data = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                    # Se falhar, tenta Latin-1 (resolve o \xfa = ú)
                data = raw_bytes.decode('latin1')

            lista = [line.split(";") for line in data.splitlines()]  # melhor que split("\\n")
            
            df.loc[index, 'TABELA'] = [lista[1:]]  # armazena a lista (sem header)
            
            df_temp = pd.DataFrame.from_records(lista[1:], columns=colunas[3:])
            df_temp.insert(loc=0, column='"CODIGO_EMPRESA"', value=df['CODIGO_EMPRESA'][index])
            df_temp.insert(loc=1, column='"CODIGO_FILIAL"', value=df['CODIGO_FILIAL'][index])
            df_temp.insert(loc=2, column='"SEQUENCIAL_ARQUIVO"', value=df['SEQUENCIAL_ARQUIVO'][index])

            colunas_para_codificar = ['"NOME_CLIENTE"', '"DESCRICAO_PRODUTO"']

            for col in colunas_para_codificar:
                if col in df_temp.columns:
                    df_temp[col] = df_temp[col].apply(lambda x: base64.b64encode(str(x).encode('utf-8')).decode('utf-8'))

            
            df_final = pd.concat([df_final, df_temp], ignore_index=True)

    
    except Exception as ex:
      print("")
      print("-> Erro no tratamento do dataframe! 1")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      print(ex)
      sys.exit(1)

    print("")
    print("-> Odata processado corretamente!")


    try:

      ## em colunas de valores, troca vírgula por ponto
      df_final['"valorNominal"'] = df_final['"valorNominal"'].str.replace('.','').str.replace(',','.')
      df_final['"valorPresente"'] = df_final['"valorPresente"'].str.replace('.','').str.replace(',','.')
      df_final['"valorAquisicao"'] = df_final['"valorAquisicao"'].str.replace('.','').str.replace(',','.')
      df_final['"valorPdd"'] = df_final['"valorPdd"'].str.replace('.','').str.replace(',','.')
      df_final['"taxaCessao"'] = df_final['"taxaCessao"'].str.replace('.','').str.replace(',','.')
      df_final['"taxaRecebivel"'] = df_final['"taxaRecebivel"'].str.replace('.','').str.replace(',','.')
      df_final['"seuNumero"'] = df_final['"seuNumero"'].str.replace(',','.')

      ## ajusta modelo de data de dd/mm/aaaa para aaaa-mm-dd 
      df_final['"dataFundo"'] = pd.to_datetime(df_final['"dataReferencia"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
      df_final['"dataReferencia"'] = pd.to_datetime(df_final['"dataReferencia"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
      df_final['"dataVencimentoOriginal"'] = pd.to_datetime(df_final['"dataVencimentoOriginal"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
      df_final['"dataVencimentoAjustada"'] = pd.to_datetime(df_final['"dataVencimentoAjustada"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
      df_final['"dataEmissao"'] = pd.to_datetime(df_final['"dataEmissao"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
      df_final['"dataAquisicao"'] = pd.to_datetime(df_final['"dataAquisicao"'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')

      df_final['"nomeFundo"'] = df_final['"nomeFundo"'].str.replace("'","")

      ## coloca valores NaN para nulos, permitindo incluir tuplas no banco de dados 
      df_final = df_final.where(pd.notnull(df_final), None)

    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe! 2")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 
      
      ## função que insere dataframe no banco de dados (conexao, dataframe_origem, tabela_destino) 
      fn_inserirRegistros(cnx.conn, df_final, 'extract."qprof_carteiraCustodiante"') 
      print(df_final)

      run_procedure('extract."sp_merge_qprof_carteiraCustodiante"()')
      ## funcao inserir log
      fn_inserirLog(cnx.conn, 'finalizar' , pid, script, projeto, etapa, "'x'", "'x'")

    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe para tabela!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)
    
  else:
    fn_inserirLog(cnx.conn, 'dfVazio' , pid, script, projeto, etapa, "'"+parametro_carga+"'", 'null')
    print("")
    return print("-> Odata sem registros")
get_qprof_carteiraCustodiante()

