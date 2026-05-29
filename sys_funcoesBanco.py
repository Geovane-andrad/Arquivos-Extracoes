
import sys_conexaoBanco as cnx
import pandas as pd
import re


def get_parametroCarga(nome_carga):
    cursor = cnx.conn.cursor()
    cursor.execute("select nm_origem||' '||ds_parametro as parametro from privated.tb_dm_cargas where nm_carga = "+nome_carga)
    result = cursor.fetchone()
    parametro = result[0]
    return parametro


def run_procedure(nm_procedure):
    cursor = cnx.conn.cursor() 
    cursor.execute("call "+nm_procedure)
    cnx.conn.commit() 


def get_jsonBitrixSPA_183(cd_identificador):
    cursor = cnx.conn.cursor()
    cursor.execute("select * from defender.fn_jsonbitrix_spa183("+str(cd_identificador)+")")
    result = cursor.fetchone()
    return str(result[1])


def get_codigosBitrixSPA_183():
    cursor = cnx.conn.cursor()
    cursor.execute("select defender.fn_codigosbitrix_spa183() as codigos")
    result = cursor.fetchone()
    if result[0] is not None:
        lista = re.split(';', result[0])
        return lista
    else:
        return result


def run_registra_envioGatilho(cd_identificador, tp_envio, fl_sucesso, ds_retorno):
    cursor = cnx.conn.cursor() 
    cursor.execute("call defender.sp_registra_alteracoes_gatilho("+str(cd_identificador)+", '"+tp_envio+"', '"+fl_sucesso+"', '"+ds_retorno+"')")
    cnx.conn.commit() 



def get_parametroCarga_mvp(nome_carga):
   
    try:
        cursor = cnx.conn.cursor() # Conexão com o banco
 
        # Consulta SQL para buscar origem, data_inicio e data_fim
        query = """
            SELECT nm_origem,
                   dt_inicio  AS data_inicio,
                   dt_fim AS data_fim,
                   filter_date_by
            FROM privated.tb_dm_cargas
            WHERE nm_carga = %s
        """
        cursor.execute(query, (nome_carga,))  # Substitui '%s' pelo valor de nome_carga
        result = cursor.fetchone()  # Busca o primeiro resultado
 
        cursor.close()  # Fecha o cursor
 
        if result:  # Se houver resultado, concatena os valores
            nm_origem, data_inicio, data_fim, filter_date_by = result
            return f"{nm_origem}*{data_inicio}*{data_fim}*{filter_date_by}"  # Ex.: "API_Transacoes 2025-01-01 2025-01-05"
        else:
            raise ValueError(f"Nenhum registro encontrado para a carga '{nome_carga}'.")
    except Exception as e:
        print(f"Erro: {e}")
        return None

def get_parametroCarga_gsurf(nome_carga):

    try:
        cursor = cnx.conn.cursor()
 
        # Consulta SQL para buscar origem
        query = """
            SELECT nm_origem
            FROM privated.tb_dm_cargas
            WHERE nm_carga = %s
        """
        cursor.execute(query, (nome_carga,)) 
        result = cursor.fetchone()
        cursor.close() 

        if result:  # Se houver resultado
                nm_origem = result[0]
                return nm_origem
        else:
                raise ValueError(f"Nenhum registro encontrado para a carga '{nome_carga}'.")
        
    except Exception as e:
        print(f"❌ Erro ao buscar parâmetro de carga: {e}")
        return None

    
def get_parametroCarga_bitrix(nome_carga):

    try:
        cursor = cnx.conn.cursor()
 
        # Consulta SQL para buscar origem
        query = """
            SELECT nm_origem
            FROM privated.tb_dm_cargas
            WHERE nm_carga = %s
        """
        cursor.execute(query, (nome_carga,)) 
        result = cursor.fetchone()
        cursor.close() 

        if result:  # Se houver resultado
                nm_origem = result[0]
                print(f"✔️ Origem encontrada para '{nome_carga}': {nm_origem}")
                return nm_origem
        else:
                raise ValueError(f"Nenhum registro encontrado para a carga '{nome_carga}'.")
        
    except Exception as e:
        print(f"❌ Erro ao buscar parâmetro de carga: {e}")
        return None