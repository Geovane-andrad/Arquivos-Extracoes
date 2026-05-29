import sys_conexaoBanco as cnx
import pandas as pd
import re

def get_parametroCarga_bitrix(nome_carga):

    try:
        cursor = cnx.conn.cursor()

        query = """
            SELECT nm_origem
            FROM privated.tb_dm_cargas
            WHERE nm_carga = %s
        """
        cursor.execute(query, (nome_carga,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            nm_origem = result[0]
            print(f"✔️ Origem encontrada para '{nome_carga}': {nm_origem}")
            return nm_origem
        else:
            raise ValueError(f"Nenhum registro encontrado para a carga '{nome_carga}'.")

    except Exception as e:
        print(f"❌ Erro ao buscar parâmetro de carga: {e}")
        return None


# ✅ chamada correta
get_parametroCarga_bitrix('bitrix_spa183_monitoramento')
