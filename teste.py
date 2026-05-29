import requests
import pandas as pd

def extrair_antecipacoes():

    url = "https://api.movingpay.com.br/api/v3/relatorios/antecipacoes"

    chave = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE2NTMsImN1c3RvbWVyc19pZCI6ODIsImhhc2giOiJlMGM3MzFiZC1jMjBiLTRkZDEtYjNmNC0zY2ZlYTg5YmVmMDciLCJpYXQiOjE3NzgwMDQ5OTcsImV4cCI6MTc4NTc4MDk5N30.u6oWs5J_Se1UcMahZ1ODkQiD6-wjYU_NYOeCp0KgKjg"

    headers = {
        "CUSTOMER": str(82),
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json"
    }

    params = {
        "start_date": "2026-04-08 00:00:00",
        "finish_date": "2026-04-12 23:59:59",
        "filter_date_by": "updated_date",
        "page": 1
    }

    todas_paginas = []

    while True:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print("Erro:", response.status_code)
            print(response.text)
            return

        dados = response.json()
        registros = dados.get("data", [])

        if not registros:
            break

        todas_paginas.extend(registros)

        last_page = dados.get("lastPage", 1)

        print(f"Página {params['page']} de {last_page}")

        if params["page"] >= last_page:
            break

        params["page"] += 1

    df = pd.DataFrame(todas_paginas)

    if df.empty:
        print("Nenhum dado encontrado.")
        return

    # 👉 SEM FILTRO (traz tudo)
    nome_arquivo = "antecipacoes_2026_04_01_a_20.xlsx"
    df.to_excel(nome_arquivo, index=False)

    print(f"Arquivo gerado: {nome_arquivo}")


extrair_antecipacoes()