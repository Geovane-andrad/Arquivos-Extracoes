
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

def get_qprof_usuario_sistema():

  pid = "'"+str(os.getpid())+"'"
  script = "'"+str(os.path.basename(__file__))+"'"
  projeto = "'carga datalake'"
  etapa = "'extração'"

  try:
      
      fn_inserirLog(cnx.conn, 'iniciar' , pid, script, projeto, etapa, "'x'", 'null')
      
      nome_carga = "'qprof_usuario_sistema'"
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
        'CODIGO_USUARIO',
        'NOME_USUARIO',
        'DATA_ADMISSAO',
        'TELEFONE_DDD',
        'TELEFONE',
        'CELULAR_DDD',
        'CELULAR',
        'DATA_CADASTRO',
        'HORA_INICIO_TRABALHO',
        'HORA_FIM_TRABALHO',
        'RAMAL',
        'EMAIL_PARTICULAR_USUARIO',
        'DATA_AFASTAMENTO',
        'DATA_INICIO_FERIAS',
        'DATA_FIM_FERIAS',
        'INICIAIS_NOME',
        'NOME_COMPLETO',
        'CODIGO_FILIAL_PADRAO',
        'CODIGO_EMPRESA_PADRAO',
        'INDICADOR_RECEBE_NOTIF_QUICKSOFT',
        'INDICADOR_ACESSA_EXTRATOR',
        'INDICADOR_PARTICIPA_ATENDIMENTO_TEL',
        'TIPO_USUARIO_HELP_DESK',
        'INDICADOR_PERMITE_LOGAR_FIM_SEMANA',
        'INDICADOR_RESTR_LOCAL_ACESSO_IP',
        'QUANTIDADE_CONSULTA_TEMP_SERASA',
        'VALIDADE_LIMITE_CONULTAS_TEMP_SERASA',
        'CODIGO_USUARIO_SERASA_GERAL',
        'QUANTIDADE_CONSULTA_SERASA',
        'INDICADOR_CONSULTA_SER_CONCENTRE',
        'INDICADOR_CONSULTA_SER_CONCENTRE_PADRAO',
        'INDICADOR_CONSULTA_SER_CRED_BUREAU',
        'INDICADOR_CONSULTA_SER_CRED_BUREAU_PADRAO',
        'INDICADOR_CONSULTA_SER_QUADRO_SOCIAL',
        'INDICADOR_CONSULTA_SER_PARTICIPACOES',
        'INDICADOR_CONSULTA_SER_RISK_SCORING',
        'INDICADOR_CONSUlTA_SER_RISK_SCORING_PADRAO',
        'INDICADOR_CONSULTA_SER_RISCO_CREDITO',
        'INDICADOR_CONSULTA_SER_RISCO_CREDITO_PADRAO',
        'INDICADOR_CONSULTA_SER_GASTO_ESTIMADO',
        'INDICADOR_CONSULTA_SER_GASTO_ESTIMADO_PADRAO',
        'INDICADOR_CONSULTA_SER_ALER_IDENT_PJ',
        'INDICADOR_CONSULTA_SER_ALER_IDENT_PJ_PADRAO',
        'INDICADOR_CONSULTA_SER_CAD_POSITIVO_PJ',
        'INDICADOR_CONSULTA_SER_CAD_POSITIVO_PJ_PADRAO',
        'INDICADOR_CONSULTA_SER_ENDER_TEL_ALTERNATIVO',
        'INDICADOR_CONSULTA_SER_ENDER_TEL_ALTERNATIVO_PADRAO',
        'INDICADOR_CONSULTA_SER_SITUACAO_FISCAL',
        'INDICADOR_CONSULTA_SER_SITUACAO_FISCAL_PADRAO',
        'INDICADOR_CONSULTA_SER_ALER_CADASTRAL',
        'INDICADOR_CONSULTA_SER_ALER_CADASTRAL_PADRAO',
        'INDICADOR_CONSULTA_SER_ALER_CADASTRAL_SOC_ADM',
        'INDICADOR_CONSULTA_SER_ALER_CADASTRAL_SOC_ADM_PADRAO',
        'INDICADOR_CONSULTA_SER_VENDAS_CARTAO',
        'INDICADOR_CONSULTA_SER_VENDAS_CARTAO_PADRAO',
        'INDICADOR_CONSULTA_SER_RECUP_DIVIDA',
        'INDICADOR_CONSULTA_SER_RECUP_DIVIDA_PADRAO',
        'INDICADOR_CONSULTA_SER_RECOM_CREDITO',
        'INDICADOR_CONSULTA_SER_RECOM_CREDITO_PADRAO',
        'INDICADOR_CONSULTA_SER_REL_MERCADO_SETOR',
        'INDICADOR_CONSULTA_SER_REL_MERCADO_SETOR_PADRAO',
        'INDICADOR_CONSULTA_SER_PAG_EMPRESAS',
        'INDICADOR_CONSULTA_SER_PAG_EMPRESAS_PADRAO',
        'INDICADOR_CONSULTA_SER_SPC_SOC_ADM',
        'INDICADOR_CONSULTA_SER_SPC_COC_ADM_PADRAO',
        'INDICADOR_CONSULTA_SER_CLAS_RISCO_CRED_SETOR',
        'INDICADOR_CONSULTA_SER_CLAS_RISCO_CRED_SETOR_PADRAO',
        'INDICADOR_CONSULTA_SER_PERFIL_FINANCEIRO',
        'INDICADOR_CONSULTA_SER_PERFIL_FINANCEIRO_PADRAO',
        'INDICADOR_CONSULTA_SER_RISK_SCORING_PF',
        'INDICADOR_CONSULTA_SER_RISK_SCORING_PF_PADRAO',
        'INDICADOR_CONSULTA_SER_RISK_SCORING_PJ',
        'INDICADOR_CONSULTA_SER_RISK_SCORING_PJ_PADRAO',
        'INDICADOR_CONSULTA_SER_SPC',
        'INDICADOR_CONSULTA_SER_SPC_PADRAO',
        'INDICADOR_CONSULTA_SER_AUT_CREDITO_PF',
        'INDICADOR_CONSULTA_SER_AUT_CREDITO_PF_PADRAO',
        'INDICADOR_CONSULTA_SER_QUADRO_SOCIAL_PADRAO',
        'INDICADOR_CONSULTA_SER_PARTICIPACOES_PADRAO',
        'INDICADOR_CONSULTA_SER_FAT_PRESUMIDO',
        'INDICADOR_CONSULTA_SER_FAT_PRESUMIDO_PADRAO',
        'INDICADOR_CONSULTA_SER_LIMITE_CRED_PJ',
        'INDICADOR_CONSULTA_SER_LIMITE_CRED_PJ_PADRAO',
        'INDICADOR_CONSULTA_SER_ALERT_SCORING',
        'INDICADOR_CONSULTA_SER_ALERT_SCORING_PADRAO',
        'INDICADOR_CONSULTA_SER_AUT_CREDITO_PJ',
        'INDICADOR_CONSULTA_SER_AUT_CREDITO_PJ_PADRAO',
        'INDICADOR_CONSULTA_SER_DETALHADA',
        'INDICADOR_CONSULTA_SER_DETALHADA_PADRAO',
        'INDICADOR_CONSULTA_SER_ANOTACOES_SPC',
        'INDICADOR_CONSULTA_SER_ANOTACOES_SPC_PADRAO',
        'INDICADOR_CONSULTA_SER_NOVO_QUADRO_SOCIAL',
        'INDICADOR_CONSULTA_SER_NOVO_QUADRO_SOCIAL_PADRAO',
        'INDICADOR_CONSULTA_SER_INDICE_REL_MERCADO',
        'INDICADOR_CONSULTA_SER_INDICE_REL_MERCADO_PADRAO',
        'INDICADOR_CONSULTA_BOA_VISTA',
        'CODIGO_USUARIO_BOA_VISTA_GERAL',
        'QUANTIDADE_CONSULTA_BOA_VISTA',
        'INDICADOR_CONSULTA_BOA_SCORE_EMPRESARIAL',
        'INDICADOR_CONSULTA_BOA_SCORE_EMPRESARIAL_PADRAO',
        'INDICADOR_CONSULTA_BOA_SCORE_ATACADISTA',
        'INDICADOR_CONSULTA_BOA_SCORE_ATACADISTA_PADRAO',
        'INDICADOR_CONSULTA_BOA_FAT_PRESUMIDO',
        'INDICADOR_CONSULTA_BOA_FAT_PRESUMIDO_PADRAO',
        'INDICADOR_CONSULTA_BOA_EXTRA_PENDENCIA',
        'INDICADOR_CONSULTA_BOA_EXTRA_PENDENCIA_PADRAO',
        'INDICADOR_CONSULTA_BOA_EXTRA_PROTESTO',
        'INDICADOR_CONSULTA_BOA_EXTRA_PROTESTO_PADRAO',
        'INDICADOR_CONSULTA_BOA_SCORE_PF',
        'INDICADOR_CONSULTA_BOA_SCORE_PF_PADRAO',
        'INDICADOR_CONSULTA_BOA_EXTRA_ACOES_PF',
        'INDICADOR_CONSULTA_BOA_EXTRA_ACOES_PF_PADRAO',
        'INDICADOR_CONSULTA_BOA_EXTRA_INFORM_PF',
        'INDICADOR_CONSULTA_BOA_EXTRA_INFORM_PF_PADRAO',
        'CODIGO_USUARIO_ATUALIZACAO',
        'DATA_ATUALIZACAO',
        'SITUACAO_USUARIO'
      ]]
      
    except Exception as ex:
      print("")
      print("-> Erro no processamento do dataframe!")
      fn_inserirLog(cnx.conn, 'error' , pid, script, projeto, etapa, "'x'", ex)
      sys.exit(1)

    try: 

      fn_inserirRegistros(cnx.conn, df_final, "extract.qprof_usuario_sistema")
      run_procedure('extract.sp_merge_qprof_usuario_sistema()')
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
  