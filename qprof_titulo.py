

import pandas as pd
import base64
import os
import sys_conexaoBanco as cnx
import sys
from datetime import datetime, timezone

def get_qprof_titulo():


  from sys_funcaoInserirTabela import fn_inserirRegistros
  from sys_funcaoInserirLog import fn_inserirLog
  from sys_funcoesBanco import get_parametroCarga
  from sys_funcoesBanco import run_procedure
  import sys_conexaoOdata as odatas
  from sys_funcoesTratamento import limpar_html, remove_quotes


  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_titulo'"
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

      ## em colunas de valores, troca vírgula por ponto
      df["VALOR_IOF"] = df["VALOR_IOF"].astype(str).str.replace(',','.')
      df["VALOR_IOF_ADICIONAL"] = df["VALOR_IOF_ADICIONAL"].astype(str).str.replace(',','.')
      df["VALOR_FACE"] = df["VALOR_FACE"].astype(str).str.replace(',','.')
      df["VALOR_DESAGIO"] = df["VALOR_DESAGIO"].astype(str).str.replace(',','.')
      df["VALOR_DESAGIO_ORIGINAL"] = df["VALOR_DESAGIO_ORIGINAL"].astype(str).str.replace(',','.')
      df["VALOR_AQUISICAO"] = df["VALOR_AQUISICAO"].astype(str).str.replace(',','.')
      ##df["VALOR_BASE_PDD"] = df["VALOR_BASE_PDD"].astype(str).str.replace(',','.')
      df["VALOR_BAIXADO"] = df["VALOR_BAIXADO"].astype(str).str.replace(',','.')
      df["VALOR_ADVALOREM"] = df["VALOR_ADVALOREM"].astype(str).str.replace(',','.')
      df["VALOR_DESCONTO"] = df["VALOR_DESCONTO"].astype(str).str.replace(',','.')
      df["VALOR_BAIXA_BANCO"] = df["VALOR_BAIXA_BANCO"].astype(str).str.replace(',','.')
      df["VALOR_DESCONTO_BANCO"] = df["VALOR_DESCONTO_BANCO"].astype(str).str.replace(',','.')
      df["VALOR_ABATIMENTO"] = df["VALOR_ABATIMENTO"].astype(str).str.replace(',','.')
      df["VALOR_JURO_RECOMPRA"] = df["VALOR_JURO_RECOMPRA"].astype(str).str.replace(',','.')
      df["VALOR_JURO_BANCO"] = df["VALOR_JURO_BANCO"].astype(str).str.replace(',','.')
      df["VALOR_MORA_ANTECIPADA"] = df["VALOR_MORA_ANTECIPADA"].astype(str).str.replace(',','.')
      df["VALOR_CESSAO"] = df["VALOR_CESSAO"].astype(str).str.replace(',','.')
      df["VALOR_MULTA"] = df["VALOR_MULTA"].astype(str).str.replace(',','.')
      df["VALOR_CORRIGIDO_VENCIDO"] = df["VALOR_CORRIGIDO_VENCIDO"].astype(str).str.replace(',','.')
      df["VALOR_TARIFA"] = df["VALOR_TARIFA"].astype(str).str.replace(',','.')
      df["VALOR_LIQUIDO"] = df["VALOR_LIQUIDO"].astype(str).str.replace(',','.')
      df["VALOR_DESCONTO_INDEVIDO_CEDENTE"] = df["VALOR_DESCONTO_INDEVIDO_CEDENTE"].astype(str).str.replace(',','.')
      df["VALOR_DESCONTO_INDEVIDO_BANCO"] = df["VALOR_DESCONTO_INDEVIDO_BANCO"].astype(str).str.replace(',','.')
      df["VALOR_OUTRO_CREDITO"] = df["VALOR_OUTRO_CREDITO"].astype(str).str.replace(',','.')
      df["VALOR_PRECO_UNITARIO"] = df["VALOR_PRECO_UNITARIO"].astype(str).str.replace(',','.')
      df["VALOR_DEDUCAO"] = df["VALOR_DEDUCAO"].astype(str).str.replace(',','.')
      df["VALOR_JUROS_FACTRING"] = df["VALOR_JUROS_FACTRING"].astype(str).str.replace(',','.')
      df["VALOR_JUROS_FUNDO"] = df["VALOR_JUROS_FUNDO"].astype(str).str.replace(',','.')
      df["VALOR_BRUTO"] = df["VALOR_BRUTO"].astype(str).str.replace(',','.')
      df["VALOR_DESCONTO_PONTUAL"] = df["VALOR_DESCONTO_PONTUAL"].astype(str).str.replace(',','.')
      df["VALOR_ABERTO"] = df["VALOR_ABERTO"].astype(str).str.replace(',','.')
      df["PERCENTUAL_MORA_BANCARIA"] = df["PERCENTUAL_MORA_BANCARIA"].astype(str).str.replace(',','.')
      df["PERCENTUAL_MORA_RECOMPRA"] = df["PERCENTUAL_MORA_RECOMPRA"].astype(str).str.replace(',','.')

      df['NUMERO_TITULO'] = df["NUMERO_TITULO"].astype(str).str.replace("'","")
      df['NUMERO_CONTROLE_REMESSA_CEDENTE'] = df["NUMERO_CONTROLE_REMESSA_CEDENTE"].astype(str).str.replace("'","")
      df['OBSERVACAO_CUSTODIA_CHEQUE'] = df["OBSERVACAO_CUSTODIA_CHEQUE"].astype(str).str.replace("'","")
      df['OBERVACAO_MERCADORIA_PROBLEMA'] = df["OBERVACAO_MERCADORIA_PROBLEMA"].astype(str).str.replace("'","")
      df['NOME_TRANSPORTADORA'] = df["NOME_TRANSPORTADORA"].astype(str).str.replace("'","")
      df['NUMERO_NFE'] = df["NUMERO_NFE"].astype(str).str.replace("'","")
      df['CODIGO_CFOP'] = df["CODIGO_CFOP"].astype(str).str.replace("'","")
      df['OBSERVACAO'] = df["OBSERVACAO"].astype(str).str.replace("'","")
      df['CODIGO_CMC7_CHEQUE'] = df["CODIGO_CMC7_CHEQUE"].astype(str).str.replace("'","")
      df['OBSERVACAO_SAIDA_MERCADORIA'] = df["OBSERVACAO_SAIDA_MERCADORIA"].astype(str).str.replace("'","")
      df['OBSERVACAO_ENTREGA_MERCADORIA'] = df["OBSERVACAO_ENTREGA_MERCADORIA"].astype(str).str.replace("'","")
      df['OBSERVACAO_MERCADORIA'] = df["OBSERVACAO_MERCADORIA"].astype(str).str.replace("'","")

      df['OBSERVACAO_CUSTODIA_CHEQUE'] = df['OBSERVACAO_CUSTODIA_CHEQUE'].apply(limpar_html)
      df = remove_quotes(df, 'OBSERVACAO_CUSTODIA_CHEQUE')
      df['OBERVACAO_MERCADORIA_PROBLEMA'] = df['OBERVACAO_MERCADORIA_PROBLEMA'].apply(limpar_html)
      df = remove_quotes(df, 'OBERVACAO_MERCADORIA_PROBLEMA')
      df['NOME_TRANSPORTADORA'] = df['NOME_TRANSPORTADORA'].apply(limpar_html)
      df = remove_quotes(df, 'NOME_TRANSPORTADORA')
      df['OBSERVACAO'] = df['OBSERVACAO'].apply(limpar_html)
      df = remove_quotes(df, 'OBSERVACAO')
      df['OBSERVACAO_SAIDA_MERCADORIA'] = df['OBSERVACAO_SAIDA_MERCADORIA'].apply(limpar_html)
      df = remove_quotes(df, 'OBSERVACAO_SAIDA_MERCADORIA')
      df['OBSERVACAO_ENTREGA_MERCADORIA'] = df['OBSERVACAO_ENTREGA_MERCADORIA'].apply(limpar_html)
      df = remove_quotes(df, 'OBSERVACAO_ENTREGA_MERCADORIA')
      df['OBSERVACAO_MERCADORIA'] = df['OBSERVACAO_MERCADORIA'].apply(limpar_html)
      df = remove_quotes(df, 'OBSERVACAO_MERCADORIA')

      ## coloca valores NaN para nulos, permitindo incluir tuplas no banco de dados 
      
      ##df = df.where(pd.notnull(df), "null")
      nulo = "null"
      df = df.where(pd.notnull(df), nulo)
      
      ##df.fillna(value="null", inplace=True)
      df_final = df[
        [
        'CODIGO_EMPRESA', 
        'CODIGO_FILIAL', 
        'NUMERO_SEQUENCIAL_TITULO', 
        'CODIGO_CEDENTE', 
        'CODIGO_SACADO', 
        'CODIGO_BANCO_CARTEIRA', 
        'CODIGO_AGENCIA_CARTEIRA', 
        'CODIGO_CONTA_CORRENTE_CARTEIRA', 
        'CODIGO_CARTEIRA', 
        'CODIGO_VARIACAO_CARTEIRA', 
        'CODIGO_BANCO_COBRADOR', 
        'CODIGO_AGENCIA_COBRADOR', 
        'CODIGO_BANCO_PAGO', 
        'CODIGO_AGENCIA_PAGO', 
        'NUMERO_CONFISSAO_DIVIDA', 
        'CODIGO_ESPECIE_DOCUMENTO', 
        'NUMERO_BORDERO', 
        'NUMERO_ADITIVO', 
        'NUMERO_OPERACAO', 
        'NUMERO_LOTE', 
        'SEQUENCIA_LOTE', 
        'TIPO_COBRANCA', 
        'NUMERO_TITULO', 
        'TIPO_TITULO', 
        'CODIGO_SITUACAO_TITULO', 
        'CODIGO_ROTULO', 
        'DIAS_ATRASO', 
        'DIAS_UTEIS', 
        'DIAS_CORRIDOS', 
        'DIAS_CALCULO_IOF', 
        'DIAS_CALCULO_DESAGIO', 
        'VALOR_IOF', 
        'VALOR_IOF_ADICIONAL', 
        'VALOR_FACE', 
        'VALOR_DESAGIO', 
        'VALOR_DESAGIO_ORIGINAL', 
        'VALOR_AQUISICAO', 
        'VALOR_BAIXADO', 
        'VALOR_ADVALOREM', 
        'VALOR_DESCONTO', 
        'VALOR_BAIXA_BANCO', 
        'VALOR_DESCONTO_BANCO', 
        'VALOR_ABATIMENTO', 
        'VALOR_JURO_RECOMPRA', 
        'VALOR_JURO_BANCO', 
        'VALOR_MORA_ANTECIPADA', 
        'VALOR_CESSAO', 
        'VALOR_MULTA', 
        'VALOR_CORRIGIDO_VENCIDO', 
        'VALOR_TARIFA', 
        'VALOR_LIQUIDO', 
        'VALOR_DESCONTO_INDEVIDO_CEDENTE', 
        'VALOR_DESCONTO_INDEVIDO_BANCO', 
        'VALOR_OUTRO_CREDITO', 
        'VALOR_PRESENTE', 
        'VALOR_PRECO_UNITARIO', 
        'VALOR_DEDUCAO', 
        'VALOR_JUROS_FACTRING', 
        'VALOR_JUROS_FUNDO', 
        'VALOR_BRUTO', 
        'VALOR_DESCONTO_PONTUAL', 
        'DATA_LIMITE_DESCONTO_PONTUAL', 
        'DATA_EMISSAO', 
        'DATA_PAGAMENTO', 
        'DATA_BAIXA', 
        'DATA_ATUALIZACAO_BAIXA', 
        'DATA_EFETIVACAO', 
        'DATA_VENCIMENTO_ORIGINAL', 
        'DATA_VENCIMENTO_REAL', 
        'DATA_ATUALIZACAO_EFETIVACAO', 
        'CODIGO_ESTAGIO_TITULO', 
        'INDICADOR_ORIGEM_CONFISSAO_DIVIDA', 
        'INDICADOR_ENVIA_CARTA_SACADO', 
        'NUMERO_LOCALIDADE', 
        'DATA_ULTIMA_OCORRENCIA_CARTORIO', 
        'SITUACAO_PROTESTO', 
        'SITUACAO_RECOMPRA', 
        'NUMERO_CONTROLE_REMESSA_CEDENTE', 
        'NUMERO_BANCARIO', 
        'DIAS_ATRASO_RECOMPRA', 
        'INDICADOR_ENVIADO_REMESSA', 
        'INDICADOR_ENVIO_AR_SACADO', 
        'INDICADOR_GERA_AR_SACADO', 
        'INDICADOR_GERA_CARTA_CONFIRMA_SACADO', 
        'INDICADOR_CARTA_CONFIRMA_ENVIA_EMAIL', 
        'INDICADOR_PROTESTAR_AUTOMATICO', 
        'DIAS_PROTESTAR_AUTOMATICO', 
        'NUMERO_TITULO_CUSTODIANTE', 
        'DATA_ENTREGA_CANHOTO', 
        'CODIGO_INTEGRACAO', 
        'INDICADOR_ENVIA_BOLETO_EMAIL_SACADO', 
        'INDICADOR_ENVIA_PEFIN', 
        'CODIGO_LOTE_DESCONTO', 
        'CODIGO_PESSOA_ENDOSSANTE', 
        'OBSERVACAO_CUSTODIA_CHEQUE', 
        'INDICADOR_MERCADORIA_EXPEDIDA', 
        'INDICADOR_MERCADORIA_ENTREGUE', 
        'INDICADOR_MERCADORIA_TRANSPORTE', 
        'INDICADOR_MERCADORIA_PROBLEMA', 
        'DATA_MERCADORIA_PROBLEMA', 
        'DATA_MERCADORIA_EMBARQUE', 
        'OBERVACAO_MERCADORIA_PROBLEMA', 
        'CODIGO_MOTIVO_CONTROLADORIA_PROBLEMA', 
        'CODIGO_MOTIVO_CONTROLADORIA_ENTREGUE', 
        'CODIGO_MOTIVO_CONTROLADORIA_DEVOLVIDA', 
        'CODIGO_MOTIVO_CONTROLADORIA_ADICIONAL', 
        'INDICADOR_REJEITADO_CONFERENCIA', 
        'CODIGO_USUARIO_CONFERENCIA', 
        'INDICADOR_REJEITADO_ANALISE', 
        'CODIGO_USUARIO_ANALISE', 
        'DATA_REJEICAO_NEGOCIACAO', 
        'INDICADOR_REJEITADO_CONTROLADORIA_PEDIDO', 
        'CODIGO_USUARIO_CONTROLADORIA_PEDIDO', 
        'DATA_CONTROLADORIA_PEDIDO', 
        'DATA_CONTROLADORIA_ENTREGA', 
        'INDICADOR_CONTROLADORIA_EXPEDICAO', 
        'INDICADOR_CONTROLADORIA_ENTREGA', 
        'INDICADOR_CANHOTO_ENTREGUE', 
        'NOME_TRANSPORTADORA', 
        'TELEFONE_DDD_TRANSPORTADORA', 
        'TELEFONE_TRANSPORTADORA', 
        'DATA_PREVISAO_EXPEDICAO_MERCADORIA', 
        'DATA_PREVISAO_ENTREGA_MERCADORIA', 
        'NUMERO_SEQUENCIAL_TITULO_RENEGOCIADO', 
        'DATA_REEMBOLSO_DESCONTO', 
        'NUMERO_NFE', 
        'INDICADOR_UTILIZA_DDA', 
        'NUMERO_NOTA_FISCAL', 
        'SERIE_NOTA_FISCAL', 
        'DIGITO_NOTA_FISCAL', 
        'CODIGO_CFOP', 
        'INDICADOR_SUBSTITUIDO_AMOSTRAGEM', 
        'INDICADOR_REATIVADO_CUSTODIANTE', 
        'PERCENTUAL_MULTA_VENC_TITULO', 
        'INDICADOR_INSTRUMENTO_PROTESTO', 
        'DATA_COBRANCA_TAR_MANUTENCAO', 
        'INDICADOR_NOTA_CONSULTADA', 
        'NUMERO_BANCARIO_ORIGINAL', 
        'CODIGO_STATUS_CHECAGEM', 
        'NUMERO_SCORE', 
        'INDICADOR_SOLICITADO_CANHOTO_EMAIL', 
        'CODIGO_BANDEIRA_CARTAO', 
        'NUMERO_PARCELA', 
        'INDICADOR_STATUS_CHECAGEM_MANUAL', 
        'DATA_EMISSAO_CANHOTO', 
        'INDICADOR_OPERACAO_PRECALCULADA', 
        'OBSERVACAO', 
        'INDICADOR_PROTESTADO_CARTORIO', 
        'INDICADOR_TITULO_EFETIVADO', 
        'DATA_PRORROGACAO', 
        'VALOR_ABERTO', 
        'SEQUENCIAL_TITULO_ATUAL', 
        'INDICADOR_RECOMPRADO', 
        'INDICADOR_SERASA', 
        'INDICADOR_MORA_BANCARIA', 
        'PERCENTUAL_MORA_BANCARIA', 
        'INDICADOR_CUSTODIADO_CHEQUE', 
        'TIPO_COMPENSACAO_CHEQUE', 
        'CODIGO_CMC7_CHEQUE', 
        'CODIGO_CAMARA_COMPENSACAO', 
        'CODIGO_PAIS_CHEQUE', 
        'SIGLA_UNIDADE_FEDERATIVA_CHEQUE', 
        'INDICADOR_MERCADORIA_DEVOLVIDA', 
        'NUMERO_CONHECIMENTO_CARGA', 
        'CODIGO_CAPA_REDIGITACAO_ARQUIVAMENTO', 
        'CODIGO_USUARIO_REDIGITACAO_ARQUIVAMENTO', 
        'DATA_CAPA_REDIGITACAO_ARQUIVAMENTO_', 
        'INDICADOR_COBRA_CONSULTA_CEDENTE', 
        'INDICADOR_COBRA_CONSULTA_SERASA', 
        'INDICADOR_COBRA_CONSULTA_EQUIFAX', 
        'PERCENTUAL_MORA_RECOMPRA', 
        'OBSERVACAO_SAIDA_MERCADORIA', 
        'OBSERVACAO_ENTREGA_MERCADORIA', 
        'OBSERVACAO_MERCADORIA', 
        'DATA_DEVOLUCAO_MERCADORIA', 
        'CODIGO_USUARIO_ATUALIZACAO', 
        'DATA_ATUALIZACAO' 
        ]
        ]
      

    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)


    try: 
      
      ## função que insere dataframe no banco de dados (conexao, dataframe_origem, tabela_destino) 
      fn_inserirRegistros(cnx.conn, df_final, 'extract."qprof_titulo"') 
      run_procedure('extract."sp_merge_qprof_titulo"()')
      ##print(df_final)

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
    ##print(df)
    return print("-> Odata sem registros")
  
get_qprof_titulo()