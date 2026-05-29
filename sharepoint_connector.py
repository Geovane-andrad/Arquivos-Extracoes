"""
sharepoint_connector.py
-----------------------
Conecta ao SharePoint via Microsoft Graph API usando credenciais
de App Registration (client credentials flow — sem interação do usuário).

Credenciais necessárias no .env:
    SP_TENANT_ID      = b57d456b-79...   (ID do diretório)
    SP_CLIENT_ID      = 0699c893-2...    (ID do aplicativo)
    SP_CLIENT_SECRET  = pT18Q~...        (Value do Secret)
    SP_SITE_URL       = https://valorem365.sharepoint.com/sites/TimereaCarto
    SP_FOLDER_PATH    = Shared Documents/Consulta_B3/Arquivos_para_consulta
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Configurações ──────────────────────────────────────────────────────────────
TENANT_ID     = os.getenv("ID_DIRETORIO")
CLIENT_ID     = os.getenv("ID_APLICATIVO")
CLIENT_SECRET = os.getenv("ID_SECRET_KEY")
SITE_URL      = os.getenv("SP_SITE_URL",    "https://valorem365.sharepoint.com/sites/TimereaCarto")
FOLDER_PATH   = os.getenv("SP_FOLDER_PATH", "Shared Documents/Consulta_B3/Arquivos_para_consulta")

GRAPH_BASE    = "https://graph.microsoft.com/v1.0"
TOKEN_URL     = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"


# ── Autenticação ───────────────────────────────────────────────────────────────
def get_access_token() -> str:
    """Obtém token OAuth2 via client_credentials."""
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


# ── Localiza o Site ID no Graph ────────────────────────────────────────────────
def get_site_id(token: str) -> str:
    """Resolve o site SharePoint para o ID interno do Graph API."""
    # Extrai hostname e caminho relativo da URL do site
    # ex: valorem365.sharepoint.com  /sites/TimereaCarto
    from urllib.parse import urlparse
    parsed   = urlparse(SITE_URL)
    hostname = parsed.hostname                          # valorem365.sharepoint.com
    site_rel = parsed.path.lstrip("/")                 # sites/TimereaCarto

    url  = f"{GRAPH_BASE}/sites/{hostname}:/{site_rel}"
    resp = requests.get(url, headers=_headers(token))
    resp.raise_for_status()
    return resp.json()["id"]


# ── Lista arquivos da pasta ────────────────────────────────────────────────────
def listar_arquivos_rcc(token: str, site_id: str, filtro: str = "_AGENDA-BATCH") -> list[dict]:
    """
    Retorna lista de dicts com {name, download_url} para arquivos .RCC
    que contenham `filtro` no nome, dentro de FOLDER_PATH.
    """
    # Codifica o caminho da pasta para a Graph API
    folder_encoded = FOLDER_PATH.replace(" ", "%20")
    url = f"{GRAPH_BASE}/sites/{site_id}/drive/root:/{folder_encoded}:/children"

    arquivos = []
    while url:
        resp = requests.get(url, headers=_headers(token))
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("value", []):
            name = item.get("name", "")
            if name.upper().endswith(".RCC") and filtro in name:
                arquivos.append({
                    "name":         name,
                    "download_url": item["@microsoft.graph.downloadUrl"],
                    "size":         item.get("size", 0),
                    "modified":     item.get("lastModifiedDateTime"),
                })

        # Paginação (caso haja mais de 200 itens)
        url = data.get("@odata.nextLink")

    return sorted(arquivos, key=lambda x: x["name"])


# ── Baixa conteúdo de um arquivo em memória ───────────────────────────────────
def baixar_arquivo(download_url: str) -> bytes:
    """Baixa o conteúdo do arquivo direto em memória (sem salvar em disco)."""
    resp = requests.get(download_url)
    resp.raise_for_status()
    return resp.content
