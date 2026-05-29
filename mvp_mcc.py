import sys
import os
import pandas as pd
from sys_funcoesBanco import get_parametroCarga_mvp, run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirTabela import fn_inserirRegistros
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys_conexaoBanco as cnx
from sys_funcaoInserirLog import fn_inserirLog

pid = f"'{os.getpid()}'"
script = f"'{os.path.basename(__file__)}'"
projeto = "'carga datalake'"
etapa = "'extração'"


def get_mvp_mcc():
    try:
        print("🔍 1 - Consultando estabelecimentos e extraindo IDs...")
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, projeto, etapa, "'x'", 'null')

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

        nome_carga_mcc = "mvp_mcc"
        carga_parametro_mcc = get_parametroCarga_mvp(nome_carga_mcc)
        if not carga_parametro_mcc:
            raise ValueError("Parâmetros da carga de MCC não encontrados.")

        url_mcc = carga_parametro_mcc.split('*')[0]

        def extrair_mcc_com_paginacao(mid):
            mccs = []
            try:
                param = {"mid": mid, "page": 1}
                resp = get_dados_mvp(url_mcc, param)
                if resp.status_code != 200:
                    print(f"⚠️ MID {mid} falhou na página 1 (status {resp.status_code})")
                    return []

                json_data = resp.json()
                last_page = json_data.get("lastPage", 1)
                mccs.extend(json_data.get("data", []))

                for p in range(2, last_page + 1):
                    param["page"] = p
                    resp = get_dados_mvp(url_mcc, param)
                    if resp.status_code == 200:
                        mccs.extend(resp.json().get("data", []))

                for m in mccs:
                    m["mid"] = mid

                return mccs

            except Exception as e:
                print(f"❌ Erro ao processar MID {mid}: {e}")
                return []

        print("🚀 2 - Extraindo MCCs por estabelecimento...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            futuros = [executor.submit(extrair_mcc_com_paginacao, mid) for mid in ids]
            todos_mcc = []
            total = len(futuros)
            for idx, f in enumerate(as_completed(futuros), start=1):
                todos_mcc.extend(f.result())
                print(f"\rProcessando MCCs: {idx}/{total} ({(idx/total)*100:.1f}%)", end="")
        print() 

        df_mcc = pd.DataFrame(todos_mcc)
        if df_mcc.empty:
            raise ValueError("Nenhum MCC coletado.")

        print(f"✅ MCCs coletados: {len(df_mcc)} registros.")
        fn_inserirRegistros(cnx.conn, df_mcc, "extract.mvp_mcc")
        run_procedure('extract.sp_merger_mvp_mcc()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')
        print("✅ Processo finalizado com sucesso.")

    except Exception as e:
        erro_formatado = "'" + str(e).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(f"❌ Erro inesperado: {e}")
        raise

get_mvp_mcc()