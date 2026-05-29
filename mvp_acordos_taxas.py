import pandas as pd
from sys_funcoesBanco import get_parametroCarga_mvp, run_procedure
from sys_conexaoOdata import get_dados_mvp
from sys_funcaoInserirTabela import fn_inserirRegistros
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys_conexaoBanco as cnx
from sys_funcaoInserirLog import fn_inserirLog
import os


def get_mvp_acordo_taxas():

    pid = "'"+str(os.getpid())+"'"
    script = "'"+str(os.path.basename(__file__))+"'"
    projeto = "'carga datalake'"
    etapa = "'extração'"

    try:
        print("🔍 1 - Consultando estabelecimentos e extraindo planos...")
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
            if resp.status_code != 200:
                print(f"⚠️  Erro na página {pagina}: {resp.status_code}")
                continue
            estabelecimentos.extend(resp.json().get("data", []))

        planos_ids = list(set([
            est.get("planoId")
            for est in estabelecimentos
            if est.get("planoId") not in [None, 0]
        ]))

        print(f"✅ Planos únicos extraídos: {len(planos_ids)}")

        nome_carga_taxas = "mvp_acordo_taxas"
        carga_parametro_taxas = get_parametroCarga_mvp(nome_carga_taxas)
        if not carga_parametro_taxas:
            raise ValueError("Parâmetros da carga de taxas não encontrados.")

        url_taxas = carga_parametro_taxas.split('*')[0]

        def consultar_taxas_por_plano(rate_id):
            try:
                parametro = {"merchant_id": 0, "rate_id": rate_id}
                print(f"➡️ Requisição de plano: rate_id = {rate_id}")
                resp = get_dados_mvp(url_taxas, parametro)
                if resp.status_code != 200:
                    print(f"⚠️  Plano {rate_id} retornou status {resp.status_code}")
                    return []
                taxas = resp.json().get("data", [])
                for t in taxas:
                    t["merchants_id"] = 0
                return taxas
            except Exception as e:
                print(f"❌ Erro plano {rate_id}: {e}")
                return []

        print("🚀 Extraindo taxas dos planos de taxas...")
        todas_taxas = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futuros = [executor.submit(consultar_taxas_por_plano, rid) for rid in planos_ids]
            for futuro in as_completed(futuros):
                todas_taxas.extend(futuro.result())

        df_taxas = pd.DataFrame(todas_taxas)
        if df_taxas.empty:
            raise ValueError("Nenhuma taxa de plano coletada.") 

        #arquivo_saida = "taxas.xlsx"
        #df_taxas.to_excel(arquivo_saida, index=False)   
        fn_inserirRegistros(cnx.conn, df_taxas, "extract.mvp_acordo_taxas")
        run_procedure('extract.sp_merger_mvp_acordo_taxas()')
        fn_inserirLog(cnx.conn, 'finalizar', pid, script, projeto, etapa, "'x'", 'null')
        print("✅ Processo finalizado com sucesso.")

    except Exception as e:
        erro_formatado = "'" + str(e).replace("'", "") + "'"
        fn_inserirLog(cnx.conn, 'error', pid, script, projeto, etapa, "'x'", erro_formatado)
        print(f"❌ Erro inesperado: {e}")
        raise