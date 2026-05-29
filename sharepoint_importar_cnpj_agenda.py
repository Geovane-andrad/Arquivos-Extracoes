

import os
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET
import requests
import pandas as pd
import sys_conexaoBanco as cnx
import sys_funcoesBanco as fnc
from io import BytesIO
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
ARQUIVO_PATH  = "CNPJ_cadastrado_para_consulta_de_agenda/CNPJ_CADASTRADO_PARA_CONSULTA_DE_AGENDA.xlsx"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL  = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Namespace OOXML usado nos XMLs internos do .xlsx
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 1 — SHAREPOINT: autenticação e download
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


def baixar_excel(token: str) -> bytes:
    arquivo_encoded = ARQUIVO_PATH.replace(" ", "%20")
    url  = f"{GRAPH_BASE}/drives/{DRIVE_ID}/root:/{arquivo_encoded}:/content"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.content


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 2 — EXTRACT: .xlsx → DataFrame  (sem openpyxl)
# ══════════════════════════════════════════════════════════════════════════════

def _ler_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    """Lê xl/sharedStrings.xml e devolve lista indexada de strings."""
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    tree = ET.parse(zf.open("xl/sharedStrings.xml"))
    strings = []
    for si in tree.getroot().findall(f".//{NS}si"):
        # Texto pode estar em <t> direto ou em múltiplos <r><t>
        partes = [t.text or "" for t in si.findall(f".//{NS}t")]
        strings.append("".join(partes))
    return strings


def _cell_value(cell, shared: list[str]) -> str:
    """Extrai o valor de uma célula, resolvendo shared strings."""
    v_el = cell.find(f"{NS}v")
    if v_el is None or v_el.text is None:
        return ""
    t = cell.get("t", "")          # tipo da célula
    if t == "s":                    # shared string
        return shared[int(v_el.text)]
    if t == "inlineStr":
        is_el = cell.find(f"{NS}is/{NS}t")
        return is_el.text if is_el is not None else ""
    return v_el.text


def ler_xlsx_sem_openpyxl(conteudo: bytes) -> pd.DataFrame:
    """
    Descompacta o .xlsx como ZIP e lê a primeira aba (sheet1.xml)
    usando xml.etree.ElementTree da stdlib — zero dependências extras.
    Retorna DataFrame com os mesmos nomes de coluna do cabeçalho da planilha.
    """
    zf     = zipfile.ZipFile(BytesIO(conteudo))
    shared = _ler_shared_strings(zf)

    tree = ET.parse(zf.open("xl/worksheets/sheet1.xml"))
    rows_data = []

    for row in tree.getroot().findall(f".//{NS}row"):
        cells = row.findall(f"{NS}c")
        rows_data.append([_cell_value(c, shared) for c in cells])

    if not rows_data:
        return pd.DataFrame()

    header = rows_data[0]
    return pd.DataFrame(rows_data[1:], columns=header)


def limpar_cnpj(valor) -> str | None:
    if valor is None or str(valor).strip() == '':
        return None
    return re.sub(r'[^0-9]', '', str(valor)) or None


def extrair_cnpjs(conteudo: bytes, dt_carga: datetime) -> pd.DataFrame:
    df = ler_xlsx_sem_openpyxl(conteudo)[["cd_cnpj", "nm_empresa"]].copy()
    df = df.astype(str)

    df["cd_cnpj"]   = df["cd_cnpj"].apply(limpar_cnpj)
    df["nm_empresa"] = df["nm_empresa"].str.strip().str.upper()

    # Remove null bytes e caracteres de controle (evita erro SQLSTATE 22P05)
    df["nm_empresa"] = df["nm_empresa"].str.replace(r'[\x00-\x1f\x7f-\x9f]', '', regex=True)
    df["cd_cnpj"]    = df["cd_cnpj"].str.replace(r'[\x00-\x1f\x7f-\x9f]', '', regex=True)

    df["id_registro"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["dt_carga"]    = dt_carga

    df = df[df["cd_cnpj"].notna()].reset_index(drop=True)

    return df[["id_registro", "cd_cnpj", "nm_empresa", "dt_carga"]]


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3 — LOAD: DataFrame → extract.tb_ex_cnpj_agenda
# ══════════════════════════════════════════════════════════════════════════════

def carregar(df: pd.DataFrame):
    cols     = list(df.columns)
    valores  = [tuple(row) for row in df.itertuples(index=False, name=None)]
    cols_str = ", ".join(f'"{c}"' for c in cols)
    sql      = f'INSERT INTO extract.tb_ex_cnpj_agenda ({cols_str}) VALUES %s'
    cursor   = cnx.conn.cursor()
    execute_values(cursor, sql, valores)
    cursor.close()


# ══════════════════════════════════════════════════════════════════════════════
# ORQUESTRADOR
# ══════════════════════════════════════════════════════════════════════════════

def executar_etl():
    print("=" * 55)
    print("🚀 ETL — CNPJ Cadastrado para Consulta de Agenda")
    print("=" * 55)

    print("\n🔐 Autenticando no SharePoint...")
    token = get_access_token()

    print("⬇️  Baixando CNPJ_CADASTRADO_PARA_CONSULTA_DE_AGENDA.xlsx...")
    conteudo = baixar_excel(token)

    dt_carga = datetime.now()
    df = extrair_cnpjs(conteudo, dt_carga)

    print(f"📋 {len(df)} CNPJs encontrados após limpeza\n")

    try:
        carregar(df)
        cnx.conn.commit()
        print(f"\n✅ extract.tb_ex_cnpj_agenda: {len(df)} registros inseridos")

        print("\n⚙️  Executando sp_merge_cnpj_agenda...")
        fnc.run_procedure("extract.sp_merge_cnpj_agenda()")
        print("✅ Merge concluído — dados disponíveis em sharepoint.tb_dm_cnpj")

    except Exception as e:
        cnx.conn.rollback()
        print(f"\n❌ Erro na carga: {e}")
        raise

    print("=" * 55)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    executar_etl()