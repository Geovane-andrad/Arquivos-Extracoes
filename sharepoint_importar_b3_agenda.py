"""
sharepoint_b3_etl_completo.py
------------------------------
ETL completo B3: SharePoint → RDS AWS (db_datalake)
Processa dois tipos de arquivo na mesma execução:
  - AGENDA-BATCH   → extract.b3_* → transform.tb_dm/ft_*_b3
  - DCONCILIACAO   → extract.b3_contrato → transform.tb_ft_contrato_b3

Cada execução gera um id_grupo_arquivo único (UUID), compartilhado
por todos os arquivos do lote — permite rastrear fotos diárias da agenda.

Variáveis no .env:
    ID_DIRETORIO    Tenant ID Azure
    ID_APLICATIVO   Client ID App Registration
    ID_SECRET_KEY   Client Secret
    SP_FOLDER_PATH  Consulta_B3/Arquivos_para_consulta
"""

import os
import json
import uuid
import csv
import io
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
FOLDER_PATH   = os.getenv("SP_FOLDER_PATH", "Consulta_B3/Arquivos_para_consulta")
DRIVE_ID      = "b!HUuCPqZunUyTm3k2ZsjfNKCUjVqKpnJKnkjWrtjcYkmncmF44obKT5_N7CMMFJQ1"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL  = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def limpar_cnpj(valor):
    if valor is None:
        return None
    return ''.join(filter(str.isdigit, str(valor))) or None

def limpar_decimal(valor):
    if valor is None or str(valor).strip() in ('', 'null', 'NULL'):
        return None
    try:
        return float(str(valor).strip())
    except ValueError:
        return None

def limpar_data(valor):
    if valor is None or str(valor).strip() in ('', 'null', 'NULL'):
        return None
    return str(valor).strip()

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


def listar_todos_arquivos_rcc(token: str) -> dict[str, list[dict]]:
    folder_encoded = FOLDER_PATH.replace(" ", "%20")
    url     = f"{GRAPH_BASE}/drives/{DRIVE_ID}/root:/{folder_encoded}:/children"
    headers = {"Authorization": f"Bearer {token}"}
    agenda   = []
    contrato = []

    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("value", []):
            name = item.get("name", "")
            if not name.upper().endswith(".RCC"):
                continue
            arq = {
                "name":         name,
                "download_url": item["@microsoft.graph.downloadUrl"],
                "size_kb":      round(item.get("size", 0) / 1024, 1),
                "modified":     item.get("lastModifiedDateTime"),
            }
            if "_AGENDA-BATCH" in name:
                agenda.append(arq)
            elif "DCONCILIACAO" in name:
                contrato.append(arq)
        url = data.get("@odata.nextLink")

    return {
        "agenda":   sorted(agenda,   key=lambda x: x["name"]),
        "contrato": sorted(contrato, key=lambda x: x["name"]),
    }


def baixar_conteudo(download_url: str) -> bytes:
    resp = requests.get(download_url)
    resp.raise_for_status()
    return resp.content


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 2 — CONTROLE: arquivos já carregados (verifica na transform)
# ══════════════════════════════════════════════════════════════════════════════

def buscar_ja_carregados(tabela_transform: str, coluna: str = "cd_arquivo_origem") -> set:
    cursor = cnx.conn.cursor()
    cursor.execute(f"SELECT DISTINCT {coluna} FROM {tabela_transform}")
    resultado = cursor.fetchall()
    cursor.close()
    return {row[0] for row in resultado}


def filtrar_novos(arquivos: list[dict], ja_carregados: set) -> list[dict]:
    return [a for a in arquivos if a["name"] not in ja_carregados]


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3A — EXTRACT AGENDA-BATCH: JSON → DataFrames
# ══════════════════════════════════════════════════════════════════════════════

def extrair_agenda(dados: dict, nome_arquivo: str, id_grupo: str, dt_carga: datetime, dt_mod) -> dict[str, pd.DataFrame]:
    controle       = dados.get("dadosControle", {})
    dataCriacao    = controle.get("dataCriacao")
    dataReferencia = controle.get("dataReferencia")
    anuencias      = dados.get("anuencia", [])

    rows = {k: [] for k in ["anuencia", "unidade_recebivel", "valores", "liquidacao", "domicilio_bancario"]}

    for anuencia in anuencias:
        rows["anuencia"].append({
            "id":                     str(uuid.uuid4()),
            "arquivo_origem":         nome_arquivo,
            "id_grupo_arquivo":       id_grupo,
            "dataCriacao":            dataCriacao,
            "dataReferencia":         dataReferencia,
            "idAnuencia":             anuencia.get("idAnuencia"),
            "dataFimAnuencia":        anuencia.get("dataFimAnuencia"),
            "cnpjSolicitante":        anuencia.get("cnpjSolicitante"),
            "cnpjFinanciador":        anuencia.get("cnpjFinanciador"),
            "dt_carga":               dt_carga,
            "dt_modificacao_arquivo": dt_mod,
        })

    for ur in dados.get("unidadesRecebiveis", []):
        id_ur = str(uuid.uuid4())

        rows["unidade_recebivel"].append({
            "id":                     id_ur,
            "arquivo_origem":         nome_arquivo,
            "id_grupo_arquivo":       id_grupo,
            "cpfCnpjOriginador":      ur.get("cpfCnpjOriginador"),
            "arranjo":                ur.get("arranjo"),
            "cnpjCredenciadora":      ur.get("cnpjCredenciadora"),
            "cnpjRegistradora":       ur.get("cnpjRegistradora"),
            "dataPrevistaLiquidacao": ur.get("dataPrevistaLiquidacao"),
            "dt_carga":               dt_carga,
            "dt_modificacao_arquivo": dt_mod,
        })

        valores = ur.get("valores", {})
        rows["valores"].append({
            "id":                            str(uuid.uuid4()),
            "idUnidadeRecebivel":            id_ur,
            "id_grupo_arquivo":              id_grupo,
            "valorConstituidoTotal":         valores.get("valorConstituidoTotal"),
            "valorConstituidoPreContratado": valores.get("valorConstituidoPreContratado"),
            "valorComprometidoTotal":        valores.get("valorComprometidoTotal"),
            "valorTotalLiquidadoDia":        valores.get("valorTotalLiquidadoDia"),
            "valorLivreTotal":               valores.get("valorLivreTotal"),
            "dt_carga":                      dt_carga,
            "dt_modificacao_arquivo":        dt_mod,
        })

        for liq in ur.get("liquidacoes", []):
            id_liquidacao = str(uuid.uuid4())
            efeito        = liq.get("efeitoContrato", {}) or {}

            rows["liquidacao"].append({
                "id":                     id_liquidacao,
                "idUnidadeRecebivel":     id_ur,
                "idAnuencia":             anuencias[0].get("idAnuencia") if anuencias else None,
                "id_grupo_arquivo":       id_grupo,
                "tipoObrigacao":          liq.get("tipoObrigacao"),
                "indicadorOrdemEfeito":   liq.get("indicadorOrdemEfeito"),
                "dataEfetivaLiquidacao":  liq.get("dataEfetivaLiquidacao"),
                "cpfCnpjTitularContrato": efeito.get("cpfCnpjTitularContrato"),
                "idEfeitoContrato":       efeito.get("idEfeitoContrato"),
                "saldoDevedorOuLimite":   efeito.get("saldoDevedorOuLimite"),
                "valorASerMantido":       efeito.get("valorASerMantido"),
                "regraReparticao":        efeito.get("regraReparticao"),
                "tipoEfeito":             efeito.get("tipoEfeito"),
                "tipoOnus":               efeito.get("tipoOnus"),
                "dataVencimentoEfeito":   efeito.get("dataVencimentoEfeito"),
                "regraDivisao":           efeito.get("regraDivisao"),
                "dt_carga":               dt_carga,
                "dt_modificacao_arquivo": dt_mod,
            })

            for dom in liq.get("domicilios", []):
                rows["domicilio_bancario"].append({
                    "id":                      str(uuid.uuid4()),
                    "idLiquidacao":            id_liquidacao,
                    "id_grupo_arquivo":        id_grupo,
                    "valorLiquidacao":         dom.get("valorLiquidacao"),
                    "valorEfeitoSolicitado":   dom.get("valorEfeitoSolicitado"),
                    "valorEfeitoComprometido": dom.get("valorEfeitoComprometido"),
                    "valorEfeitoAConstituir":  dom.get("valorEfeitoAConstituir"),
                    "tipoConta":               dom.get("tipoConta"),
                    "agencia":                 dom.get("agencia"),
                    "conta":                   dom.get("conta"),
                    "digitoConta":             dom.get("digitoConta"),
                    "ispb":                    dom.get("ispb"),
                    "tipoDocumento":           dom.get("tipoDocumento"),
                    "documentoTitularConta":   dom.get("documentoTitularConta"),
                    "dt_carga":                dt_carga,
                    "dt_modificacao_arquivo":  dt_mod,
                })

    return {k: pd.DataFrame(v) for k, v in rows.items()}


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3B — EXTRACT DCONCILIACAO: CSV → DataFrame
# ══════════════════════════════════════════════════════════════════════════════

def extrair_contrato(conteudo: bytes, nome_arquivo: str, id_grupo: str, dt_carga: datetime, dt_mod) -> pd.DataFrame:
    reader = csv.DictReader(io.StringIO(conteudo.decode("utf-8")), delimiter=';')
    rows   = []

    for linha in reader:
        rows.append({
            "id_contrato":                     str(uuid.uuid4()),
            "arquivo_origem":                  nome_arquivo,
            "id_grupo_arquivo":                id_grupo,
            "cd_externo_contrato":             linha.get("codigoExternoContrato"),
            "cd_identificador_contrato":       linha.get("identificadorContrato"),
            "ds_situacao_contrato":            linha.get("descricaoSituacaoContrato"),
            "nr_cnpj_participante":            limpar_cnpj(linha.get("cnpjParticipante")),
            "nr_cnpj_detentor":                limpar_cnpj(linha.get("cnpjDetentor")),
            "nm_participante":                 linha.get("nomeParticipante"),
            "nr_cnpj_contratante_divida":      limpar_cnpj(linha.get("documentoContratanteDivida")),
            "dt_registro_contrato":            limpar_data(linha.get("dataRegistroContrato")),
            "dt_referencia_contrato":          limpar_data(linha.get("dataReferenciaContrato")),
            "dt_vencimento":                   limpar_data(linha.get("dataVencimento")),
            "ds_tipo_efeito_contrato":         linha.get("descricaoTipoEfeitoContrato"),
            "ds_regra_divisao":                linha.get("descricaoRegraDivisao"),
            "vl_saldo_devedor_ou_limite":      limpar_decimal(linha.get("valorSaldoDevedorOuLimite")),
            "vl_minimo_mantido":               limpar_decimal(linha.get("valorMinimoMantido")),
            "cd_externo_definicao":            linha.get("codigoExternoDefinicao"),
            "id_efeito_contrato":              linha.get("idEfeitoContrato"),
            "nr_cnpj_usuario_final_recebedor": limpar_cnpj(linha.get("documentoUsuarioFinalRecebedor")),
            "nr_cnpj_credenciadora":           limpar_cnpj(linha.get("cnpjCredenciadora")),
            "cd_arranjo_pagamento":            linha.get("codigoArranjoPagamento"),
            "dt_liquidacao":                   limpar_data(linha.get("dataLiquidacao")),
            "dt_efetiva_liquidacao":           limpar_data(linha.get("dataEfetivaLiquidacao")),
            "ds_liquidacao_ur":                linha.get("descricaoLiquidacaoUR"),
            "cd_indicador_ordem":              linha.get("indicadorOrdemComprometimento"),
            "ds_situacao_constituicao":        linha.get("descricaoSituacaoConstituicao"),
            "vl_constituido_total":            limpar_decimal(linha.get("valorConstituidoTotal")),
            "vl_efeito_solicitado":            limpar_decimal(linha.get("valorEfeitoSolicitado")),
            "pc_efeito_solicitado":            limpar_decimal(linha.get("percentualEfeitoSolicitado")),
            "vl_efeito_comprometido":          limpar_decimal(linha.get("valorEfeitoComprometido")),
            "vl_efeito_a_comprometer":         limpar_decimal(linha.get("valorEfeitoAComprometer")),
            "vl_efeito_solicitado_total":      limpar_decimal(linha.get("valorEfeitoSolicitadoTotal")),
            "vl_efeito_comprometido_total":    limpar_decimal(linha.get("valorEfeitoComprometidoTotal")),
            "vl_efeito_a_comprometer_total":   limpar_decimal(linha.get("valorEfeitoAComprometerTotal")),
            "vl_saldo_comprometimento":        limpar_decimal(linha.get("valorSaldoComprometimento")),
            "pc_saldo_comprometimento":        limpar_decimal(linha.get("percentualSaldoComprometimento")),
            "dt_carga":                        dt_carga,
            "dt_modificacao_arquivo":          dt_mod,
        })

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 4 — LOAD: DataFrames → extract.* no RDS
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
    print("🚀 ETL B3 — AGENDA-BATCH + DCONCILIACAO-CONTRATO")
    print("=" * 60)

    # ── 1. Autentica e lista todos os arquivos ────────────────────────────────
    print("\n🔐 Autenticando no SharePoint...")
    token = get_access_token()
    todos = listar_todos_arquivos_rcc(token)

    print(f"📋 SharePoint: {len(todos['agenda'])} AGENDA-BATCH | {len(todos['contrato'])} DCONCILIACAO")

    # ── 2. Filtra arquivos novos ──────────────────────────────────────────────
    print("\n🔍 Verificando arquivos já carregados...")
    ja_agenda   = buscar_ja_carregados("sharepoint.tb_dm_anuencia_b3")
    ja_contrato = buscar_ja_carregados("sharepoint.tb_ft_contrato_b3")

    novos_agenda   = filtrar_novos(todos["agenda"],   ja_agenda)
    novos_contrato = filtrar_novos(todos["contrato"], ja_contrato)

    print(f"🆕 Novos: {len(novos_agenda)} AGENDA-BATCH | {len(novos_contrato)} DCONCILIACAO")

    if not novos_agenda and not novos_contrato:
        print("\n✅ Nenhum arquivo novo — banco já está atualizado.")
        return

    # ── ID do grupo — externo (compartilhado com CERC/BMP) ou gerado aqui ────
    id_grupo = id_grupo_externo if id_grupo_externo else str(uuid.uuid4())
    dt_carga = datetime.now()

    if id_grupo_externo:
        print(f"\n🔑 id_grupo_arquivo (compartilhado): {id_grupo}")
    else:
        print(f"\n🔑 id_grupo_arquivo (novo): {id_grupo}")

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO A — AGENDA-BATCH
    # ══════════════════════════════════════════════════════════════════════════
    if novos_agenda:
        print(f"\n{'─'*60}")
        print(f"📂 Processando {len(novos_agenda)} arquivo(s) AGENDA-BATCH...")

        acumulado = {k: [] for k in ["anuencia", "unidade_recebivel", "valores", "liquidacao", "domicilio_bancario"]}

        for arq in novos_agenda:
            print(f"  ⬇️  {arq['name']} ({arq['size_kb']} KB)")
            try:
                dados  = json.loads(baixar_conteudo(arq["download_url"]).decode("utf-8"))
                dt_mod = converter_modified(arq["modified"])
                dfs    = extrair_agenda(dados, arq["name"], id_grupo, dt_carga, dt_mod)
                for entidade, df in dfs.items():
                    if not df.empty:
                        acumulado[entidade].append(df)
                print(f"     ✅ Extraído")
            except Exception as e:
                print(f"     ❌ Erro: {e}")

        dfs_agenda = {k: pd.concat(v, ignore_index=True) if v else pd.DataFrame() for k, v in acumulado.items()}

        mapa_agenda = {
            "anuencia":           "extract.b3_anuencia",
            "unidade_recebivel":  "extract.b3_unidade_recebivel",
            "valores":            "extract.b3_valores",
            "liquidacao":         "extract.b3_liquidacao",
            "domicilio_bancario": "extract.b3_domicilio_bancario",
        }
        try:
            for entidade, tabela in mapa_agenda.items():
                df = dfs_agenda[entidade]
                if not df.empty:
                    carregar_dataframe(df, tabela)
                    print(f"     ✅ {tabela}: {len(df)} linhas")
            cnx.conn.commit()

            print("\n  ⚙️  sp_merge_consulta_agenda_registradora_b3...")
            fnc.run_procedure("extract.sp_merge_consulta_agenda_registradora_b3()")
            print("     ✅ Merge concluído")
        except Exception as e:
            cnx.conn.rollback()
            print(f"\n  ❌ Erro AGENDA-BATCH: {e}")
            raise

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO B — DCONCILIACAO-CONTRATO
    # ══════════════════════════════════════════════════════════════════════════
    if novos_contrato:
        print(f"\n{'─'*60}")
        print(f"📂 Processando {len(novos_contrato)} arquivo(s) DCONCILIACAO-CONTRATO...")

        dfs_contrato = []
        for arq in novos_contrato:
            print(f"  ⬇️  {arq['name']} ({arq['size_kb']} KB)")
            try:
                conteudo = baixar_conteudo(arq["download_url"])
                dt_mod   = converter_modified(arq["modified"])
                df       = extrair_contrato(conteudo, arq["name"], id_grupo, dt_carga, dt_mod)
                if not df.empty:
                    dfs_contrato.append(df)
                print(f"     ✅ Extraído: {len(df)} linhas")
            except Exception as e:
                print(f"     ❌ Erro: {e}")

        if dfs_contrato:
            df_final = pd.concat(dfs_contrato, ignore_index=True)
            try:
                carregar_dataframe(df_final, "extract.b3_contrato")
                cnx.conn.commit()
                print(f"\n  ✅ extract.b3_contrato: {len(df_final)} linhas inseridas")

                print("\n  ⚙️  sp_merge_consulta_agenda_registradora_b3_contrato...")
                fnc.run_procedure("extract.sp_merge_consulta_agenda_registradora_b3_contrato()")
                print("     ✅ Merge concluído")
            except Exception as e:
                cnx.conn.rollback()
                print(f"\n  ❌ Erro DCONCILIACAO: {e}")
                raise

    print(f"\n{'='*60}")
    print(f"✅ ETL concluído — grupo: {id_grupo}")
    print(f"   {len(novos_agenda)} AGENDA-BATCH | {len(novos_contrato)} DCONCILIACAO")
    print(f"{'='*60}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    executar_etl()