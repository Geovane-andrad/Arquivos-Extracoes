"""
sys_conexaoBanco_homologacao.py
-------------------------------
Conexão com o banco de HOMOLOGAÇÃO (PostgreSQL via Docker local).
Segue o mesmo padrão do sys_conexaoBanco.py (produção).
"""

import psycopg2


user     = 'postgres'
host     = 'localhost'
port     = 5432
database = 'postgres'


try:
    conn = psycopg2.connect(
        database = database,
        user     = user,
        password = 'valorem123',
        host     = host,
        port     = port,
        client_encoding = 'UTF8',
    )
    status_banco = 1

except Exception as error:
    print("Oops! An exception has occured:", error)
    print("Exception TYPE:", type(error))
    status_banco = 0