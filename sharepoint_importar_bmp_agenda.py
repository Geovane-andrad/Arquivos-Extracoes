"""
importar_bmp_agenda.py
----------------------
ETL: SharePoint (BMP Agenda) → RDS AWS (db_datalake)
Padrão ETL Valorem (SharePoint): extract → sp_merge → sharepoint

Fonte  : SharePoint > TimereaCarto > Consulta_BMP/Arquivos_para_consulta
         > part-00000-*-c<ddmmaaaa>.csv
Destino: sharepoint.tb_dm_bmp_ur + sharepoint.tb_ft_bmp_pagamento
         (via procedure extract.sp_merge_bmp_agenda)

A coluna 15 (_listaUR) é mantida inteira na extract. A divisão dessa coluna
(16 campos por item, itens separados por '|') é feita na procedure de merge.
O 16º campo (UUID do efeito) é preservado no banco (id_efeito_contrato).
A regra de beneficiário final (campo 8 com fallback p/ campo 1, espelhando o
modelo Power BI) também é aplicada na procedure, não aqui.

Uso com id_grupo_arquivo externo (compartilhado com B3/CERC do mesmo dia):
    python importar_bmp_agenda.py --id-grupo <uuid>

Uso standalone (gera id_grupo_arquivo próprio):
    python importar_bmp_agenda.py

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
FOLDER_PATH   = "Consulta_BMP/Arquivos_para_consulta"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL  = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Colunas do CSV (15) — grafia LITERAL do arquivo
COLUNAS_CSV = [
    "Entidade_Registradora",
    "Inst_Credenciadora_ou_Subcredenciadora",
    "Usuario_Final_Recebedor",
    "Arranjo_de_Pagamento",
    "Data_de_Liquidacao",
    "Titular_da_Unidade_de_Recebivel",
    "Constituicao_da_Unidade_de_Recebivel",
    "Valor_Constituido",
    "Valor_Constituido_antecipacao_pre_contratado",
    "Valor_Bloqueado",
    "Carteira",
    "Valor_Livre",
    "Valor_Total_UR",
    "Data_hora_ultima_atualizacao_da_UR",
    "_listaUR",                  # coluna 15 — mantida inteira
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def limpar_decimal(valor):
    """BMP usa vírgula como separador decimal (ex: '470,20')."""
    if valor is None or str(valor).strip() in ('', 'null', 'NULL'):
        return None
    try:
        return float(str(valor).strip().replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def normalizar_datetime(valor):
    """
    BMP entrega datetime com vírgula no milissegundo: '2026-04-08T00:02:11,959Z'.
    Converte para ISO com ponto, que o PostgreSQL aceita no cast ::timestamp.
    Data simples ('2026-04-08') passa intacta.
    """
    if valor is None or str(valor).strip() in ('', 'null', 'NULL'):
        return None
    return str(valor).strip().replace(',', '.')


def converter_modified(dt_str: str):
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)


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


def listar_arquivos_bmp(token: str) -> list[dict]:
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
            # arquivos BMP: part-00000-...-c<ddmmaaaa>.csv
            if name.lower().endswith(".csv") and name.lower().startswith("part-"):
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
    cursor.execute("SELECT DISTINCT arquivo_origem FROM sharepoint.tb_dm_bmp_ur")
    resultado = cursor.fetchall()
    cursor.close()
    return {row[0] for row in resultado}


def filtrar_novos(arquivos: list[dict], ja_carregados: set) -> list[dict]:
    return [a for a in arquivos if a["name"] not in ja_carregados]


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3 — EXTRACT: CSV → DataFrame
# ══════════════════════════════════════════════════════════════════════════════

def extrair_bmp(conteudo: bytes, nome_arquivo: str, id_grupo: str,
                dt_carga: datetime, dt_mod) -> pd.DataFrame:
    texto  = conteudo.decode("utf-8")
    reader = csv.reader(io.StringIO(texto), delimiter=';', quotechar='"')
    rows   = []

    header = next(reader, None)  # descarta cabeçalho

    for linha in reader:
        if len(linha) < 15:
            continue

        rows.append({
            "id_registro":               str(uuid.uuid4()),
            "id_grupo_arquivo":          id_grupo,
            "arquivo_origem":            nome_arquivo,
            "Entidade_Registradora":                        re.sub(r'[^0-9]', '', linha[0]) or None,
            "Inst_Credenciadora_ou_Subcredenciadora":       re.sub(r'[^0-9]', '', linha[1]) or None,
            "Usuario_Final_Recebedor":                      re.sub(r'[^0-9]', '', linha[2]) or None,
            "Arranjo_de_Pagamento":                         linha[3].strip() or None,
            "Data_de_Liquidacao":                           normalizar_datetime(linha[4]),
            "Titular_da_Unidade_de_Recebivel":              re.sub(r'[^0-9]', '', linha[5]) or None,
            "Constituicao_da_Unidade_de_Recebivel":         linha[6].strip() or None,
            "Valor_Constituido":                            limpar_decimal(linha[7]),
            "Valor_Constituido_antecipacao_pre_contratado": limpar_decimal(linha[8]),
            "Valor_Bloqueado":                              limpar_decimal(linha[9]),
            "Carteira":                                     linha[10].strip() or None,
            "Valor_Livre":                                  limpar_decimal(linha[11]),
            "Valor_Total_UR":                               limpar_decimal(linha[12]),
            "Data_hora_ultima_atualizacao_da_UR":           normalizar_datetime(linha[13]),
            "_listaUR":                                     linha[14].strip(),   # coluna 15 — inteira
            "dt_carga":                  dt_carga,
            "dt_modificacao_arquivo":    dt_mod,
        })

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 4 — LOAD: DataFrame → extract.tb_ex_bmp_agenda
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
    print("🚀 ETL BMP — Agenda de Recebíveis")
    print("=" * 60)

    # ── 1. Autentica e lista arquivos ─────────────────────────────────────────
    print("\n🔐 Autenticando no SharePoint...")
    token    = get_access_token()
    arquivos = listar_arquivos_bmp(token)

    print(f"📋 SharePoint: {len(arquivos)} arquivo(s) BMP encontrado(s)")

    # ── 2. Filtra arquivos novos ──────────────────────────────────────────────
    print("🔍 Verificando arquivos já carregados...")
    ja_carregados  = buscar_ja_carregados()
    arquivos_novos = filtrar_novos(arquivos, ja_carregados)

    if not arquivos_novos:
        print("✅ Nenhum arquivo novo — banco já está atualizado.")
        return

    print(f"🆕 {len(arquivos_novos)} arquivo(s) novo(s) para carregar\n")

    # ── id_grupo_arquivo: externo (compartilhado) ou novo ─────────────────────
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
            dt_mod   = converter_modified(arq["modified"])
            df = extrair_bmp(conteudo, arq["name"], id_grupo, dt_carga, dt_mod)
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
    print("\n🔌 Carregando em extract.bmp_agenda...")
    try:
        carregar_dataframe(df_final, "extract.bmp_agenda")
        cnx.conn.commit()
        print(f"   ✅ {len(df_final)} linhas inseridas")

        print("\n⚙️  Executando sp_merge_bmp_agenda...")
        fnc.run_procedure("extract.sp_merge_bmp_agenda()")
        print("   ✅ Merge concluído — dados em sharepoint.tb_dm_bmp_ur + tb_ft_bmp_pagamento")

    except Exception as e:
        cnx.conn.rollback()
        print(f"\n❌ Erro na carga: {e}")
        raise

    print(f"\n{'='*60}")
    print(f"✅ ETL BMP concluído — {len(arquivos_novos)} arquivo(s) processado(s)")
    print(f"{'='*60}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--id-grupo",
        type=str,
        default=None,
        help="id_grupo_arquivo externo (compartilhado com B3/CERC do mesmo dia)"
    )
    args = parser.parse_args()
    executar_etl(id_grupo_externo=args.id_grupo)