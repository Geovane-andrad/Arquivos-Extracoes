
from sys_conexaoOdata import get_dados_mvp




url = "https://api-backoffice-mtls.movingpay.com.br/api/v3/transacoes"

parametro = {
    "start_date": "2025-01-01",
    "finish_date": "2025-01-02",
    "page": 1
}

response = get_dados_mvp(url, parametro)

print("Status:", response.status_code)
print("Resposta:", response.text)
