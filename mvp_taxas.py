import pandas as pd
import os
from sys_funcoesBanco import get_parametroCarga_mvp, run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirTabela import fn_inserirRegistros
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys_conexaoBanco as cnx
from sys_funcaoInserirLog import fn_inserirLog
import sys

def get_mvp_taxas():
    pid = "'"+str(os.getpid())+"'"
    script = "'"+str(os.path.basename(__file__))+"'"
    projeto = "'carga datalake'"
    etapa = "'extração'"

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
                print(f"⚠️  Falha ao buscar página {pagina}: HTTP {resp.status_code}")
                sys.exit(1)

        ids = [e["codigoCliente"] for e in estabelecimentos if "codigoCliente" in e]
        print(f"✅ IDs extraídos: {len(ids)} merchants.")

        nome_carga_taxas = "mvp_acordo_taxas"
        carga_parametro_taxas = get_parametroCarga_mvp(nome_carga_taxas)
        if not carga_parametro_taxas:
            raise ValueError("Parâmetros da carga de taxas não encontrados.")
            

        url_taxas = carga_parametro_taxas.split('*')[0]

        def extrair_taxas_com_paginacao(merchant_id):
            todas_taxas = []
            try:
                parametro = {"merchant_id": merchant_id, "page": 1}
                resp = get_dados_mvp(url_taxas, parametro)
                if resp.status_code != 200:
                    return []

                json_resp = resp.json()
                last_page = json_resp.get("lastPage", 1)
                todas_taxas.extend(json_resp.get("data", []))

                for p in range(2, last_page + 1):
                    parametro["page"] = p
                    resp = get_dados_mvp(url_taxas, parametro)
                    if resp.status_code == 200:
                        todas_taxas.extend(resp.json().get("data", []))

                for t in todas_taxas:
                    t["merchants_id"] = merchant_id

                return todas_taxas

            except Exception as e:
                print(f"❌ Erro no merchant_id {merchant_id}: {e}")
                return []

        print("🚀 Extraindo taxas com controle de página por merchant_id...")
        with ThreadPoolExecutor(max_workers=1) as executor:
            futuros = [executor.submit(extrair_taxas_com_paginacao, mid) for mid in ids]
            todas_taxas = [r for f in as_completed(futuros) for r in f.result()]

        df = pd.DataFrame(todas_taxas)
        if df.empty:
            raise ValueError("Nenhuma taxa coletada.")
        
        #arquivo_saida = "taxas_api_taxas.xlsx"
        #df.to_excel(arquivo_saida, index=False)

        fn_inserirRegistros(cnx.conn, df, "extract.mvp_taxas")
        run_procedure('extract.sp_merger_mvp_taxas()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')
        print("✅ Processo finalizado com sucesso.")

    except Exception as e:
        erro_formatado = "'" + str(e).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)
        
