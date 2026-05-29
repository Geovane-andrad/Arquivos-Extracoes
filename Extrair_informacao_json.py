"""
gerar_json_agente_b3.py
-----------------------
Lê sharepoint.mv_agente_b3 e serializa UM arquivo JSON por CNPJ.

O JSON gerado é o artefato consumido pelo agente ConsultorDeAgenda_IA
sem tocar no banco em tempo de resposta.

Saída: ./output_json_b3/{nr_cnpj_empresa}.json

Variável de ambiente opcional:
    JSON_OUTPUT_DIR   caminho da pasta de saída (default: ./output_json_b3)
"""

import os
import json
import decimal
import datetime
import sys_conexaoBanco as cnx
from pathlib import Path

# ── Configuração ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(os.getenv("JSON_OUTPUT_DIR", "./output_json_b3"))

# Colunas JSONB — chegam como dict/list ou como string dependendo do driver
COLUNAS_JSONB = {"registradoras", "arranjos", "credenciadoras", "credores", "liquidacoes"}

QUERY = "SELECT * FROM sharepoint.mv_agente_b3"


# ── Serializer: converte tipos que json padrão não aceita ─────────────────────
class SerializadorValorem(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_jsonb(valor):
    """JSONB pode chegar como dict/list (psycopg2 com adapter) ou como string."""
    if valor is None:
        return []
    if isinstance(valor, (dict, list)):
        return valor
    try:
        return json.loads(valor)
    except (json.JSONDecodeError, TypeError):
        return []


def _linha_para_dict(row: tuple, colunas: list[str]) -> dict:
    """Converte uma linha do cursor em dict com JSONB parseado e tipos serializáveis."""
    registro = {}
    for col, val in zip(colunas, row):
        if col in COLUNAS_JSONB:
            registro[col] = _parse_jsonb(val)
        elif isinstance(val, decimal.Decimal):
            registro[col] = float(val)
        elif isinstance(val, (datetime.date, datetime.datetime)):
            registro[col] = val.isoformat()
        else:
            registro[col] = val
    return registro


# ── Camada 1 — Extração da materialized view ──────────────────────────────────
def extrair_mvw() -> list[dict]:
    print("🔍 Consultando sharepoint.mv_agente_b3...")

    with cnx.conn.cursor() as cursor:
        cursor.execute(QUERY)
        colunas  = [desc[0].lower() for desc in cursor.description]
        rows     = cursor.fetchall()

    if not rows:
        raise ValueError("Nenhum registro encontrado na materialized view.")

    registros = [_linha_para_dict(row, colunas) for row in rows]
    print(f"✔️  {len(registros)} CNPJ(s) extraído(s)")
    return registros


# ── Camada 2 — Serialização: um arquivo por CNPJ ──────────────────────────────
def salvar_jsons(registros: list[dict], output_dir: Path) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    salvos = 0
    erros  = 0

    for reg in registros:
        cnpj = str(reg.get("nr_cnpj_empresa", "")).strip()
        if not cnpj:
            print("  ⚠️  Registro sem nr_cnpj_empresa — ignorado")
            erros += 1
            continue

        caminho = output_dir / f"{cnpj}.json"
        try:
            # Salva o JSON — etapa crítica, separada do log
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(reg, f, cls=SerializadorValorem, ensure_ascii=False, indent=2)
            salvos += 1

            # Log informativo — None tratado com fallback para não quebrar formatação
            vl_agenda  = reg.get("vl_agenda")
            pc_tomado  = reg.get("pc_tomado")
            dt_ref     = reg.get("dt_referencia", "-")
            agenda_str = f"R$ {vl_agenda:,.2f}" if vl_agenda is not None else "R$ -"
            tomado_str = f"{pc_tomado:.1f}%"    if pc_tomado is not None else "-%"
            print(f"  📄 {cnpj}.json — agenda: {agenda_str} | tomado: {tomado_str} | ref: {dt_ref}")

        except Exception as e:
            print(f"  ❌ Erro ao salvar {cnpj}.json: {e}")
            erros += 1

    return salvos, erros


# ── Orquestrador ──────────────────────────────────────────────────────────────
def gerar_json_agente_b3(output_dir: Path = OUTPUT_DIR):
    print("=" * 55)
    print("🚀 Gerador de JSON — Agente B3")
    print("=" * 55)
    print(f"📁 Destino: {output_dir.resolve()}\n")

    try:
        registros        = extrair_mvw()
        salvos, erros    = salvar_jsons(registros, output_dir)

        print(f"\n{'=' * 55}")
        print(f"✅ {salvos} arquivo(s) gerado(s) em {output_dir}")
        if erros:
            print(f"⚠️  {erros} erro(s) durante a serialização")
        print("=" * 55)

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        raise


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    gerar_json_agente_b3()
