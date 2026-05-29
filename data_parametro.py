from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
import calendar
import time

# Capture uma única vez o "agora", para ser usado por todas as funções
HOJE = datetime.now()


def get_primeiro_dia_mes_atual():
    primeiro_dia = HOJE.replace(day=1)
    resultado = primeiro_dia.strftime("%d/%m/%Y")
    print(f"[DEBUG DENTRO DA FUNÇÃO] get_primeiro_dia_mes_atual está retornando: '{resultado}'")
    return resultado


def get_dia_anterior_ajustado():
    if HOJE.day == 1:
        return HOJE.strftime("%d/%m/%Y")  # primeiro dia do mês
    else:
        resultado = (HOJE - timedelta(days=1)).strftime("%d/%m/%Y")
        print(f"[DEBUG DENTRO DA FUNÇÃO] get_dia_anterior_ajustado está retornando: '{resultado}'")
        return resultado


def get_ultimo_dia_mes_atual():
    ultimo_dia = calendar.monthrange(HOJE.year, HOJE.month)[1]
    data_final = HOJE.replace(day=ultimo_dia)
    return data_final.strftime("%d/%m/%Y")


def get_dia_atual():
    return HOJE.strftime("%d/%m/%Y")


def inserir_data_human_like(driver: WebDriver, xpath: str, data_str: str):
    """
    Insere a data em um campo de input simulando o comportamento humano.
    Esta é a abordagem mais robusta para componentes de data complexos.
    """
    try:
        print(f"Tentando inserir a data '{data_str}' de forma humanizada...")
        
        # 1. Espera o elemento ser clicável e clica nele para dar foco
        campo_data = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        campo_data.click()
        time.sleep(0.5) # Pequena pausa para o calendário (se houver) aparecer

        # 2. Limpa o campo de forma robusta (CTRL+A, Backspace)
        campo_data.send_keys(Keys.CONTROL, "a")
        campo_data.send_keys(Keys.BACK_SPACE)
        time.sleep(0.5) # Pausa para o campo ser limpo

        # 3. Digita a nova data
        campo_data.send_keys(data_str)
        time.sleep(0.5) # Pausa após a digitação

        # 4. Pressiona Enter para confirmar a entrada
        campo_data.send_keys(Keys.ENTER)
        
        print(f"Data '{data_str}' inserida com sucesso no campo: {xpath}")

    except Exception as e:
        print(f"Erro ao tentar inserir a data '{data_str}' de forma humanizada. Erro: {e}")
        raise
