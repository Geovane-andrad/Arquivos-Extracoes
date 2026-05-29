import sys_conexaoBanco as cnx
import pandas as pd


def get_extrair_informacao():
    try:
        dt_inicio = '2025-11-01'
        dt_fim = '2026-02-01'  # dia seguinte para garantir inclusão total do dia 31

        query = """
            
        select * from sharepoint.mv_agente_b3
        
        """

        with cnx.conn.cursor() as cursor:
            cursor.execute(query, (dt_inicio, dt_fim))

            # pega nomes das colunas automaticamente
            colunas = [desc[0].lower() for desc in cursor.description]

            # carrega todos os dados
            result = cursor.fetchall()

        if not result:
            raise ValueError("Nenhum registro encontrado para a carga.")

        df = pd.DataFrame(result, columns=colunas)

        print(f"✔️ {len(df)} registros extraídos com sucesso")

        df.to_excel(
            "vw_bmp_agenda_empresa.xlsx",
            index=False
        )

        return df

    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        return None


# Executar função
get_extrair_informacao()