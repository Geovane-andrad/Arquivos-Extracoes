from dotenv import load_dotenv
import os, requests
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

TENANT = os.getenv("ID_DIRETORIO")
CLIENT = os.getenv("ID_APLICATIVO")
SECRET = os.getenv("ID_SECRET_KEY")

print(f"TENANT: {TENANT}")

token = requests.post(
    f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token",
    data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT,
        "client_secret": SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }
).json()["access_token"]

print("✅ Token obtido!\n")

site_id = "3e824b1d-6ea6-4c9d-939b-793666c8df34,5a8d94a0-a68a-4a72-9e48-d6aed8dc6249"

r = requests.get(
    f"https://graph.microsoft.com/v1.0/sites/valorem365.sharepoint.com,{site_id}/drives",
    headers={"Authorization": f"Bearer {token}"}
).json()

print("📂 Bibliotecas encontradas:")
for d in r.get("value", []):
    print(f"  Nome: {d['name']}  |  ID: {d['id']}")
