import pandas as pd
import requests as r
from sys_funcaoInserirTabela import fn_inserirRegistros
from sys_funcoesBanco import get_parametroCarga_gsurf, run_procedure
from sys_conexaoOdata import get_dados_gsurf
from sys_funcaoInserirLog import fn_inserirLog
import sys_conexaoBanco as cnx


def get_dispositivos_gsurf():
    projeto = 'carga datalake'
    etapa = 'extração'
    script = "'gsurf_dispositivos'"
    pid = "'airflow'"

    try:
        fn_inserirLog(cnx.conn, 'iniciar', pid, script, f"'{projeto}'", f"'{etapa}'", "'x'", 'null')

        nome_carga = "gsurf_dispositivos"
        carga_parametro = get_parametroCarga_gsurf(nome_carga)

        if not carga_parametro:
            raise ValueError("Parâmetro de carga não encontrado!")

        fn_inserirLog(cnx.conn, 'parametrizar', pid, script, f"'{projeto}'", f"'{etapa}'", f"'{carga_parametro}'", 'null')

        url = carga_parametro.strip()
        token = get_dados_gsurf()
        headers = {"Authorization": f"Bearer {token}"}

        dados_filtrados = []

        print("🔄 Iniciando requisição paginada da API GSurf...")

        pagina = 1
        limite = 100
        total_registros = 0

        while True:
            endpoint = f"{url}?page={pagina}&limit={limite}"
            print(f"🌐 Requisitando: {endpoint}")

            resposta = r.get(endpoint, headers=headers)
            resposta.raise_for_status()

            dados_pagina = resposta.json()
            terminais = dados_pagina.get("terminals", [])

            qtd = len(terminais)
            print(f"📥 Página {pagina}: {qtd} registros")

            if qtd == 0:
                print("🛑 Nenhum registro retornado. Finalizando paginação.")
                break

            for item in terminais:
                terminal_info = {
                    "cnpj": item.get("merchant", {}).get("cnpj"),
                    "description": item.get("terminal_model", {}).get("description"),
                    "serial_number": item.get("serial_number"),
                    "terminal_code": item.get("terminal_code"),
                    "iccid": item.get("iccid"),
                    "status": item.get("status"),
                    "creation_date": item.get("creation_date"),
                    "status_date": item.get("status_date")
                }
                dados_filtrados.append(terminal_info)

            total_registros += qtd

            # Se veio menos que o limite, provavelmente acabou
            if qtd < limite:
                print("✅ Última página identificada.")
                break

            pagina += 1

        print(f"📊 Total de registros coletados: {total_registros}")

        df = pd.DataFrame(dados_filtrados)

        if df.empty:
            raise ValueError("Nenhum dado retornado da API GSurf.")

        # trava de segurança para evitar sobrescrever a tabela com carga incompleta
        if len(df) < 1000:
            raise ValueError(f"Quantidade anormal de registros retornados ({len(df)}). Carga abortada para evitar sobrescrita indevida.")

        fn_inserirRegistros(cnx.conn, df, "extract.tb_dm_gsurf_dispositivos")
        run_procedure("extract.sp_merger_gsurf_dispositivos()")

        fn_inserirLog(cnx.conn, 'finalizar', pid, script, f"'{projeto}'", f"'{etapa}'", "'x'", 'null')
        print("✅ Carga finalizada com sucesso!")

    except Exception as ex:
        erro_formatado = "'" + str(ex).replace("'", "") + "'"
        print(f"❌ Erro durante a execução: {ex}")
        fn_inserirLog(cnx.conn, 'error', pid, script, f"'{projeto}'", f"'{etapa}'", "'x'", erro_formatado)
        raise


get_dispositivos_gsurf()