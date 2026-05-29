"""
importar_cerc_agenda.py
------------------------
ETL: SharePoint (CERC Agenda) → RDS AWS (db_datalake)
Padrão ETL Valorem: extract → sp_merge → sharepoint

Fonte  : SharePoint > TimereaCarto > Consulta_Cerc/Arquivos_para_consulta
         > CERC-AP005_*.csv
Destino: sharepoint.tb_ft_cerc_agenda (via procedure sp_merge_cerc_agenda)

Coluna 12 (ds_lista_pagamentos) mantida inteira na extract.
A divisão dessa coluna é feita na procedure de transform (próximo passo).

Uso com id_grupo_arquivo externo (compartilhado com B3 do mesmo dia):
    python importar_cerc_agenda.py --id-grupo <uuid>

Uso standalone (gera id_grupo_arquivo próprio):
    python importar_cerc_agenda.py

Variáveis no .env:
    ID_DIRETORIO    Tenant ID Azure
    ID_APLICATIVO   Client ID App Registration
    ID_SECRET_KEY   Client Secret
"""

import os
import re
import csv
import uuid
import io
import argparse
import requests
import pandas as pd
import sys_conexaoBanco as cnx
import sys_funcoesBanco as fnc
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── Credenciais SharePoint ────────────────────────────────────────────────────
TENANT_ID     = os.getenv("ID_DIRETORIO")
CLIENT_ID     = os.getenv("ID_APLICATIVO")
CLIENT_SECRET = os.getenv("ID_SECRET_KEY")
DRIVE_ID      = "b!HUuCPqZunUyTm3k2ZsjfNKCUjVqKpnJKnkjWrtjcYkmncmF44obKT5_N7CMMFJQ1"
FOLDER_PATH   = "Consulta_Cerc/Arquivos_para_consulta"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL  = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Mapeamento das colunas do CSV
COLUNAS = [
    "cd_referencia_externa",
    "nr_entidade_registradora",
    "nr_credenciadora",
    "nr_usuario_final_recebedor",
    "tp_arranjo_pagamento",
    "dt_liquidacao",
    "nr_titular_ur",
    "nr_constituicao_ur",
    "vl_constituido_total",
    "vl_constituido_antecipacao",
    "vl_bloqueado",
    "ds_lista_pagamentos",       # coluna 12 — mantida inteira
    "nm_carteira",
    "vl_livre",
    "vl_total_ur",
    "dt_ultima_atualizacao_ur",
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def limpar_decimal(valor):
    if valor is None or str(valor).strip() in ('', 'null', 'NULL'):
        return None
    try:
        return float(str(valor).strip())
    except ValueError:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 1 — SHAREPOINT: autenticação e listagem
# ══════════════════════════════════════════════════════════════════════════════

def get_access_token() -> str:
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def listar_arquivos_cerc(token: str) -> list[dict]:
    folder_encoded = FOLDER_PATH.replace(" ", "%20")
    url     = f"{GRAPH_BASE}/drives/{DRIVE_ID}/root:/{folder_encoded}:/children"
    headers = {"Authorization": f"Bearer {token}"}
    arquivos = []

    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("value", []):
            name = item.get("name", "")
            if name.upper().endswith(".CSV") and "CERC-AP005" in name:
                arquivos.append({
                    "name":         name,
                    "download_url": item["@microsoft.graph.downloadUrl"],
                    "size_kb":      round(item.get("size", 0) / 1024, 1),
                    "modified":     item.get("lastModifiedDateTime"),
                })
        url = data.get("@odata.nextLink")

    return sorted(arquivos, key=lambda x: x["name"])


def baixar_conteudo(download_url: str) -> bytes:
    resp = requests.get(download_url)
    resp.raise_for_status()
    return resp.content


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 2 — CONTROLE: arquivos já carregados
# ══════════════════════════════════════════════════════════════════════════════

def buscar_ja_carregados() -> set:
    cursor = cnx.conn.cursor()
    cursor.execute("SELECT DISTINCT arquivo_origem FROM sharepoint.tb_dm_cerc_ur")
    resultado = cursor.fetchall()
    cursor.close()
    return {row[0] for row in resultado}


def filtrar_novos(arquivos: list[dict], ja_carregados: set) -> list[dict]:
    return [a for a in arquivos if a["name"] not in ja_carregados]


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3 — EXTRACT: CSV → DataFrame
# ══════════════════════════════════════════════════════════════════════════════

def extrair_cerc(conteudo: bytes, nome_arquivo: str, id_grupo: str,
                 dt_carga: datetime, dt_mod) -> pd.DataFrame:
    texto  = conteudo.decode("utf-8")
    reader = csv.reader(io.StringIO(texto), delimiter=';', quotechar='"')
    rows   = []

    for linha in reader:
        if len(linha) < 16:
            continue

        rows.append({
            "id_registro":               str(uuid.uuid4()),
            "arquivo_origem":            nome_arquivo,
            "id_grupo_arquivo":          id_grupo,
            "cd_referencia_externa":     linha[0].strip(),
            "nr_entidade_registradora":  re.sub(r'[^0-9]', '', linha[1]),
            "nr_credenciadora":          re.sub(r'[^0-9]', '', linha[2]),
            "nr_usuario_final_recebedor":re.sub(r'[^0-9]', '', linha[3]),
            "tp_arranjo_pagamento":      linha[4].strip(),
            "dt_liquidacao":             linha[5].strip() or None,
            "nr_titular_ur":             re.sub(r'[^0-9]', '', linha[6]),
            "nr_constituicao_ur":        linha[7].strip(),
            "vl_constituido_total":      limpar_decimal(linha[8]),
            "vl_constituido_antecipacao":limpar_decimal(linha[9]),
            "vl_bloqueado":              limpar_decimal(linha[10]),
            "ds_lista_pagamentos":       linha[11].strip(),  # coluna 12 — mantida inteira
            "nm_carteira":               linha[12].strip(),
            "vl_livre":                  limpar_decimal(linha[13]),
            "vl_total_ur":               limpar_decimal(linha[14]),
            "dt_ultima_atualizacao_ur":  linha[15].strip() or None,
            "dt_carga":                  dt_carga,
            "dt_modificacao_arquivo":    dt_mod,
        })

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 4 — LOAD: DataFrame → extract.tb_ex_cerc_agenda
# ══════════════════════════════════════════════════════════════════════════════

def carregar_dataframe(df: pd.DataFrame, tabela: str):
    if df.empty:
        return
    cols     = list(df.columns)
    valores  = [tuple(row) for row in df.itertuples(index=False, name=None)]
    cols_str = ", ".join(f'"{c}"' for c in cols)
    sql      = f'INSERT INTO {tabela} ({cols_str}) VALUES %s'
    cursor   = cnx.conn.cursor()
    execute_values(cursor, sql, valores)
    cursor.close()


# ══════════════════════════════════════════════════════════════════════════════
# ORQUESTRADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def executar_etl(id_grupo_externo: str = None):
    print("=" * 60)
    print("🚀 ETL CERC — Agenda de Recebíveis")
    print("=" * 60)

    # ── 1. Autentica e lista arquivos ─────────────────────────────────────────
    print("\n🔐 Autenticando no SharePoint...")
    token    = get_access_token()
    arquivos = listar_arquivos_cerc(token)

    print(f"📋 SharePoint: {len(arquivos)} arquivo(s) CERC encontrado(s)")

    # ── 2. Filtra arquivos novos ──────────────────────────────────────────────
    print("🔍 Verificando arquivos já carregados...")
    ja_carregados  = buscar_ja_carregados()
    arquivos_novos = filtrar_novos(arquivos, ja_carregados)

    if not arquivos_novos:
        print("✅ Nenhum arquivo novo — banco já está atualizado.")
        return

    print(f"🆕 {len(arquivos_novos)} arquivo(s) novo(s) para carregar\n")

    # ── id_grupo_arquivo: externo (compartilhado com B3) ou novo ─────────────
    id_grupo = id_grupo_externo if id_grupo_externo else str(uuid.uuid4())
    dt_carga = datetime.now()

    if id_grupo_externo:
        print(f"🔑 id_grupo_arquivo (compartilhado): {id_grupo}")
    else:
        print(f"🔑 id_grupo_arquivo (novo): {id_grupo}")

    # ── 3. Extrai DataFrames ──────────────────────────────────────────────────
    dfs = []
    for arq in arquivos_novos:
        print(f"  ⬇️  {arq['name']} ({arq['size_kb']} KB)")
        try:
            conteudo = baixar_conteudo(arq["download_url"])
            dt_mod   = datetime.fromisoformat(
                arq["modified"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            df = extrair_cerc(conteudo, arq["name"], id_grupo, dt_carga, dt_mod)
            if not df.empty:
                dfs.append(df)
            print(f"     ✅ {len(df)} linhas extraídas")
        except Exception as e:
            print(f"     ❌ Erro: {e}")

    if not dfs:
        print("\n⚠️  Nenhum dado extraído.")
        return

    df_final = pd.concat(dfs, ignore_index=True)
    print(f"\n📊 Total: {len(df_final)} linhas")

    # ── 4. Carga no RDS ───────────────────────────────────────────────────────
    print("\n🔌 Carregando em extract.tb_ex_cerc_agenda...")
    try:
        carregar_dataframe(df_final, "extract.tb_ex_cerc_agenda")
        cnx.conn.commit()
        print(f"   ✅ {len(df_final)} linhas inseridas")

        print("\n⚙️  Executando sp_merge_cerc_agenda...")
        fnc.run_procedure("extract.sp_merge_cerc_agenda()")
        print("   ✅ Merge concluído — dados em sharepoint.tb_ft_cerc_agenda")

    except Exception as e:
        cnx.conn.rollback()
        print(f"\n❌ Erro na carga: {e}")
        raise

    print(f"\n{'='*60}")
    print(f"✅ ETL CERC concluído — {len(arquivos_novos)} arquivo(s) processado(s)")
    print(f"{'='*60}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--id-grupo",
        type=str,
        default=None,
        help="id_grupo_arquivo externo (compartilhado com B3 do mesmo dia)"
    )
    args = parser.parse_args()
    executar_etl(id_grupo_externo=args.id_grupo)
