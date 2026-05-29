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


def get_mvp_enderecos():
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

        nome_carga_endereco = "mvp_enderecos"
        carga_parametro_endereco = get_parametroCarga_mvp(nome_carga_endereco)
        if not carga_parametro_endereco:
            raise ValueError("Parâmetros da carga de endereço não encontrados.")

        url_endereco = carga_parametro_endereco.split('*')[0]

        def extrair_endereco_com_paginacao(mid):
            enderecos = []
            try:
                param = {"mid": mid, "page": 1}
                resp = get_dados_mvp(url_endereco, param)
                if resp.status_code != 200:
                    print(f"⚠️ MID {mid} falhou na página 1 (status {resp.status_code})")
                    return []

                json_data = resp.json()
                last_page = json_data.get("lastPage", 1)
                enderecos.extend(json_data.get("data", []))

                for p in range(2, last_page + 1):
                    param["page"] = p
                    resp = get_dados_mvp(url_endereco, param)
                    if resp.status_code == 200:
                        enderecos.extend(resp.json().get("data", []))

                for m in enderecos:
                    m["merchants_id"] = mid

                return enderecos

            except Exception as e:
                print(f"❌ Erro ao processar MID {mid}: {e}")
                return []

        print("🚀 2 - Extraindo endereços por estabelecimento...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            futuros = [executor.submit(extrair_endereco_com_paginacao, mid) for mid in ids]
            todos_enderecos = []
            total = len(futuros)
            for idx, f in enumerate(as_completed(futuros), start=1):
                todos_enderecos.extend(f.result())
                print(f"\rProcessando Endereços: {idx}/{total} ({(idx/total)*100:.1f}%)", end="")
        print() 

        df_endereco = pd.DataFrame(todos_enderecos)
        if df_endereco.empty:
            raise ValueError("Nenhum MCC coletado.")

        print(f"✅ Endereços coletados: {len(df_endereco)} registros.")
        fn_inserirRegistros(cnx.conn, df_endereco, "extract.mvp_enderecos")
        #run_procedure('extract.sp_merger_mvp_enderecos()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')
        print("✅ Processo finalizado com sucesso.")

    except Exception as e:
        erro_formatado = "'" + str(e).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(f"❌ Erro inesperado: {e}")
        raise

get_mvp_enderecos()