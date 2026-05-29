import pandas as pd
from sys_funcaoInserirTabela import fn_inserirRegistros
import sys_conexaoBanco as cnx

caminho_arquivo = "Comissão Distribuidores.xlsx"
df = pd.read_excel(caminho_arquivo)

# Formatar a coluna 'Data' para timestamp
df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')

# Extrair cd_distribuidor e nm_distribuidor
df['cd_distribuidor'] = df['Distribuidor'].str.extract(r'\[(\d+)\]')
df['nm_distribuidor'] = df['Distribuidor'].str.replace(r'\[\d+\]\s*', '', regex=True)

# Renomear as colunas para corresponder ao banco
df = df.rename(columns={
    'Data': 'dt_comissao',
    'Comissão': 'pc_comissao'
})

# Selecionar apenas as colunas necessárias
df_final = df[[
    'dt_comissao',
    'cd_distribuidor',
    'nm_distribuidor',
    'pc_comissao'
]]

print(df_final.head())
fn_inserirRegistros(cnx.conn, df_final, "movingpay.tb_dm_comissao")