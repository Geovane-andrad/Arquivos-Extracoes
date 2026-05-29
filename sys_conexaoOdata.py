
import requests
import json
import pandas as pd


def get_dadosOdata(parametro):

    requisicao = requests.get(str(parametro), auth=('60175C9775FE2E73B818EFF51885B17A', '60175C9775FE2E73B818EFF51885B17A'), timeout=2000)
    conteudo = json.loads(requisicao.content)
    df = pd.json_normalize(conteudo['value'])
    return df


def get_dadosOdata_old(parametro):

    requisicao = requests.get(str(parametro), auth=('482B8C8CC1B2B09EA9780515D38B4DBC', '482B8C8CC1B2B09EA9780515D38B4DBC'))
    conteudo = json.loads(requisicao.content)
    df = pd.json_normalize(conteudo['value'])
    return df



def get_dados_mvp(url, parametro):
    
    chave = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE2NTMsImN1c3RvbWVyc19pZCI6ODIsImhhc2giOiJlMGM3MzFiZC1jMjBiLTRkZDEtYjNmNC0zY2ZlYTg5YmVmMDciLCJpYXQiOjE3NzgwMDQ5OTcsImV4cCI6MTc4NTc4MDk5N30.u6oWs5J_Se1UcMahZ1ODkQiD6-wjYU_NYOeCp0KgKjg"

    # Cabeçalho e parâmetros
    cabecalho = {
        "CUSTOMER": str(82),
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json"
    }
 
 
    return requests.get(url, headers=cabecalho, params=parametro)

def get_dados_gsurf():
    auth_url = ("https://api.gsurfnet.com/gmac-v1/oauth2/token")
    username = ("dc270f92-285b-46f5-8555-13a693b11a32")
    password = ("Vq0Y1PMi3iyJa1EquQy90D1I2NmG1a10")
    response = requests.post(auth_url, auth=(username, password))

    if response.status_code != 200:
        print(f"Erro ao obter token:{response.status_code} - {response.text}")
        return None
    
    token = response.json().get("access_token")

    if token:
        print("✔️ Token obtido com sucesso.")
        print(f"Token: {token}")
        return token
    else:
        print("❌ Não foi possível extrair o token.")
        return None
    


def get_dadosOdata_serasa(parametro):

    requisicao = requests.get(str(parametro), auth=('60175C9775FE2E73B818EFF51885B17A', '60175C9775FE2E73B818EFF51885B17A'), timeout=2000)
    conteudo = json.loads(requisicao.content)

    for item in conteudo["value"]:
        serasa_info = item.pop("SERASA_CONSULTA", {})
        for chave, valor in serasa_info.items():
            item[chave] = valor  # insere os campos no mesmo nível

    df = pd.json_normalize(conteudo['value'])
    return df


#--------------------------------------------------------------- Novos -------------------------------------------------------------#


def get_token_mvp():
    import requests

    token_url = "https://sso.movingpay.com.br/realms/prd-movingpay/protocol/openid-connect/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": "b2b-28533398000140-owner",
        "client_secret": "D5s2hERIOloJpQQDNNXO7a1uVLyJrAHT"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    cert_path = r"C:\Certificado mTLS\certificate-prod (1).pem"

    response = requests.post(
        token_url,
        data=payload,
        headers=headers,
        cert=cert_path  # 👈 AQUI está o ponto crítico
    )

    print(f"client_id: '{payload['client_id']}'")

    if response.status_code != 200:
        print(f"Erro ao obter token: {response.status_code}")
        print(response.text)
        return None

    token = response.json().get("access_token")

    if token:
        print("✔️ Token obtido com sucesso.")
        return token
    else:
        print("❌ Não foi possível extrair o token.")
        return None


def get_dados_mvp(url, parametro):
    import requests

    token = get_token_mvp()

    if not token:
        raise Exception("Erro ao obter token")

    cert_path = r"C:\Certificado mTLS\certificate-prod (1).pem"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        url,
        headers=headers,
        params=parametro,
        cert=cert_path
    )

    return response