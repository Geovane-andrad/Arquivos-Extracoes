import pandas as pd
import sys_conexaoBanco as cnx
from sys_funcoesBanco import get_parametroCarga_bitrix
import requests


def get_automacao_update_card_bitrix():

    nome_carga = 'update_card_bitrix'
    parametro_carga = get_parametroCarga_bitrix(nome_carga)

    # 1. EXTRAÇÃO
    sql = """
    select * from load.mv_ft_atualiza_card_bitrix where id_empresa_bitrix is not null
    """

    df = pd.read_sql(sql, cnx.conn)
    print(f"🔎 Total de empresas para atualizar: {len(df)}")

    # 2. MAPEAMENTO FIXO (BD → BITRIX)
    MAPEAMENTO_CAMPOS = {
        "nm_grupo": "UF_CRM_1767019254",
        "vl_medio_operado_grupo": "UF_CRM_1760656854320",
        "pc_utilizacao_limite": "UF_CRM_1760656871758",
        "dt_ultima_operacao": "UF_CRM_1760656887400",
        "vl_faturamento_mensal": "UF_CRM_1760656950686",
        "ds_comite": "UF_CRM_1760707460513",
        "nm_consultor": "UF_CRM_1760656986776",
        "id_analista_carteira_bitrix": "UF_CRM_1760709323",
        "fl_top_10": "UF_CRM_1760916831063",
         "prioridade": "UF_CRM_1778090835094"
    }

    # 3. TRANSFORMAÇÃO (linha → payload Bitrix)
    def montar_fields_bitrix(linha, mapeamento):
        fields = {}

        for coluna_bd, campo_bitrix in mapeamento.items():
            valor = linha[coluna_bd]

            if pd.isna(valor):
                continue

            # Formatação de data
            if hasattr(valor, "strftime"):
                valor = valor.strftime("%d/%m/%Y")

            fields[campo_bitrix] = str(valor)

        return fields

    # 4. LOOP FINAL (pronto para enviar à API)
    sucesso, falha = 0, 0  # Inicializando contadores

    if not df.empty:
        for _, linha in df.iterrows():

            company_id = int(linha["id_empresa_bitrix"])
            fields_bitrix = montar_fields_bitrix(linha, MAPEAMENTO_CAMPOS)

            payload = {
                "ID": company_id,
                "fields": fields_bitrix
            }

            try:
                response = requests.post(
                    parametro_carga,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                retorno = response.json()

                if "error" in retorno:
                    print(f"❌ Erro Bitrix | Empresa {company_id} | {retorno['error_description']}")
                    falha += 1
                else:
                    print(f"✅ Empresa {company_id} atualizada com sucesso")
                    sucesso += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ Falha de comunicação com Bitrix | Empresa {company_id} | {e}")
                falha += 1

        # Resumo final
        print("\n🏁 Resumo da atualização:")
        print(f"✅ Sucesso: {sucesso}")
        print(f"❌ Falha: {falha}")
        print(f"📊 Total processadas: {sucesso + falha}")

    else:
        print("🏁 Nenhuma empresa encontrada para atualização. Finalizando o script.")

# DEPOIS
if __name__ == "__main__":
    get_automacao_update_card_bitrix()