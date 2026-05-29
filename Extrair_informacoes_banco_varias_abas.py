import sys_conexaoBanco as cnx
import pandas as pd


def executar_query(query):
    with cnx.conn.cursor() as cursor:
        cursor.execute(query)

        colunas = [desc[0].lower() for desc in cursor.description]
        result = cursor.fetchall()

    return pd.DataFrame(result, columns=colunas)


def get_extrair_informacao():
    try:

        query_movingpay = """
        select * 
        FROM movingpay.tb_dm_mvp_dispositivos_ec 
        where fl_situacao = '1'
        """

        query_gsurf = """
        select * 
        FROM movingpay.tb_dm_gsurf_dispositivos 
        where fl_situacao = '1'
        """

        query_diferentes = """
        select * 
        FROM movingpay.tb_dm_mvp_dispositivos_ec 
        where fl_situacao <> '1'
        """

        df_movingpay = executar_query(query_movingpay)
        df_gsurf = executar_query(query_gsurf)
        df_diferentes = executar_query(query_diferentes)

        print(f"✔️ Movingpay: {len(df_movingpay)} registros")
        print(f"✔️ Gsurf: {len(df_gsurf)} registros")
        print(f"✔️ Diferentes: {len(df_diferentes)} registros")

        with pd.ExcelWriter("Relatorio_Dispositivos.xlsx", engine="xlsxwriter") as writer:
            df_movingpay.to_excel(writer, sheet_name="Movingpay", index=False)
            df_gsurf.to_excel(writer, sheet_name="Gsurf", index=False)
            df_diferentes.to_excel(writer, sheet_name="Diferentes", index=False)

        print("📊 Arquivo Excel gerado com 3 abas.")

        return df_movingpay, df_gsurf, df_diferentes

    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        return None


# Executar
get_extrair_informacao()