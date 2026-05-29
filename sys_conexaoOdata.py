
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
    
    ## retirado dia 07/08/2025
    ## chave = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjI0ODcsImN1c3RvbWVyc19pZCI6IjgyIiwiaGFzaCI6ImMwNTFmMTE2LTRhMjAtNDhlYS1iMGZmLTBhYjQ5NGZjNzlkZSIsImlhdCI6MTY4MjQ1MTcxNSwiZXhwIjozMTcyMjY4OTQxMTV9.aGFc9j6DmCzolqphoJjfB0GCUSQzWl9ytzwFD7YQo-c"
 
    ## nova key 07/08/2025
    chave = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE2NTMsImN1c3RvbWVyc19pZCI6IjgyIiwiaGFzaCI6IjQwZDJlYzIzLTg0OGYtNDNkZS05YTdjLThkNmFkOWM3MTI3MSIsImlhdCI6MTc1NDQxNjc0MSwiZXhwIjoxNzYyMTkyNzQxfQ.8Wvpz0aVrekqwbqm8BCDHbJjG_Mc0CIz4cBA-PJXjEM"

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