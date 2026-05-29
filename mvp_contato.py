import sys
import os
import pandas as pd
from sys_funcoesBanco import get_parametroCarga_mvp, run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirTabela import fn_inserirRegistros
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys_conexaoBanco as cnx
from sys_funcaoInserirLog import fn_inserirLog



def get_mvp_contatos():
    try:
        print("🔍 1 - Consultando estabelecimentos e extraindo IDs...")

        nome_carga_estabs = "mvp_estabelecimentos"
        carga_parametro_estabs = get_parametroCarga_mvp(nome_carga_estabs)
        if not carga_parametro_estabs:
            raise ValueError("Parâmetros da carga de estabelecimentos não encontrados.")

        url_estabs = carga_parametro_estabs.split('*')[0]
        parametro = {"filter_date_by": "updated_date", "page": 1}
        resposta_inicial = get_dados_mvp(url_estabs, parametro)

        if resposta_inicial.status_code != 200:
            raise ValueError(f"Erro HTTP {resposta_inicial.status_code} na requisição inicial dos estabelecimentos.")

        estabelecimentos = []
        last_page = resposta_inicial.json().get("lastPage", 1)
        for pagina in range(1, last_page + 1):
            parametro["page"] = pagina
            resp = get_dados_mvp(url_estabs, parametro)
            if resp.status_code == 200:
                estabelecimentos.extend(resp.json().get("data", []))
            else:
                print(f"⚠️ Falha ao buscar página {pagina}: HTTP {resp.status_code}")

        ids = [e["codigoCliente"] for e in estabelecimentos if "codigoCliente" in e]
        print(f"✅ IDs extraídos: {len(ids)} merchants.")

        nome_carga_contato = "mvp_contatos"
        carga_parametro_contato = get_parametroCarga_mvp(nome_carga_contato)
        if not carga_parametro_contato:
            raise ValueError("Parâmetros da carga de contatos não encontrados.")

        url_contatos = carga_parametro_contato.split('*')[0]

        def extrair_contatos_com_paginacao(mid):
            contatos = []
            try:
                param = {"mid": mid, "page": 1}
                resp = get_dados_mvp(url_contatos, param)
                if resp.status_code != 200:
                    print(f"⚠️ MID {mid} falhou na página 1 (status {resp.status_code})")
                    return []

                json_data = resp.json()
                last_page = json_data.get("lastPage", 1)
                contatos.extend(json_data.get("data", []))

                for p in range(2, last_page + 1):
                    param["page"] = p
                    resp = get_dados_mvp(url_contatos, param)
                    if resp.status_code == 200:
                        contatos.extend(resp.json().get("data", []))

                for m in contatos:
                    m["mid"] = mid

                return contatos

            except Exception as e:
                print(f"❌ Erro ao processar MID {mid}: {e}")
                return []

        print("🚀 2 - Extraindo contatos por estabelecimento...")
        with ThreadPoolExecutor(max_workers=1) as executor:
            futuros = [executor.submit(extrair_contatos_com_paginacao, mid) for mid in ids]
            todos_cantatos = []
            total = len(futuros)
            for idx, f in enumerate(as_completed(futuros), start=1):
                todos_cantatos.extend(f.result())
                print(f"\rProcessando contatos: {idx}/{total} ({(idx/total)*100:.1f}%)", end="")
        print() 

        df_contato = pd.DataFrame(todos_cantatos)
        if df_contato.empty:
            raise ValueError("Nenhum contato coletado.")

        print(f"✅ Contatos coletados: {len(df_contato)} registros.")
        print("✅ Processo finalizado com sucesso.")

        df_contato.to_csv("Contatos_v2.csv", index=False)

    except Exception as e:
        erro_formatado = "'" + str(e).replace("'", "") + "'"
        print(f"❌ Erro inesperado: {e}")
        raise

get_mvp_contatos()