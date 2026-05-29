from dotenv import load_dotenv
import os, requests
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

TENANT = os.getenv("ID_DIRETORIO")
CLIENT = os.getenv("ID_APLICATIVO")
SECRET = os.getenv("ID_SECRET_KEY")

token = requests.post(
    f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token",
    data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT,
        "client_secret": SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }
).json()["access_token"]

DRIVE_ID = "b!HUuCPqZunUyTm3k2ZsjfNKCUjVqKpnJKnkjWrtjcYkmncmF44obKT5_N7CMMFJQ1"
headers  = {"Authorization": f"Bearer {token}"}

# Lista raiz do drive
print("📂 Raiz do drive (Documents):")
r = requests.get(
    f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root/children",
    headers=headers
).json()
for item in r.get("value", []):
    print(f"  [{item.get('folder') and 'PASTA' or 'FILE'}] {item['name']}")

# Tenta acessar Consulta_B3 diretamente
print("\n📂 Tentando entrar em 'Arquivos_para_consulta':")
r2 = requests.get(
    f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root:/Consulta_BMP/Arquivos_para_consulta:/children",
    headers=headers
)
if r2.status_code == 200:
    for item in r2.json().get("value", []):
        print(f"  [{item.get('folder') and 'PASTA' or 'FILE'}] {item['name']}")
else:
    print(f"  ❌ Erro {r2.status_code}: {r2.json().get('error', {}).get('message')}")
