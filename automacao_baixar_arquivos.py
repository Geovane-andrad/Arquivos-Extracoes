from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from data_parametro import get_primeiro_dia_mes_atual, get_dia_anterior_ajustado, inserir_data_human_like
from renomear_arquivo import renomear_arquivo_antecipacao, extrair_e_renomear_zip
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import JavascriptException
import time
import os

def importar_arquivo_antecipacao():

    caminho_sharepoint_local_antecipacao = r"C:\Users\geovane.andrade\OneDrive - Valorem Securitizadora de Crédito S A\BI\Projeto - Banco de Dados MEP\Antecipacoes_zip"
    print(f"Diretório de download definido para: {caminho_sharepoint_local_antecipacao}")
    chrome_options = webdriver.ChromeOptions()

    prefs = {
    "download.default_directory": caminho_sharepoint_local_antecipacao, # Define o diretório
    "download.prompt_for_download": False, # Desativa a pergunta "Onde salvar?"
    "download.directory_upgrade": True, # Permite o download para o diretório especificado
    "safebrowsing.enabled": True # Mantém a navegação segura ativa
    }
    chrome_options.add_experimental_option("prefs", prefs)

        # --- Configuração do WebDriver ---
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    driver.get('https://console.movingpay.com.br/login' )

    # --- Login (sem alterações) ---
    try:
        email_acesso = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/form/div[1]/div/div/input')))
        email_acesso.send_keys("GEOVANE.ANDRADE@VALOREM.COM.BR")

        senha_acesso = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/div/form/div[2]/div/div/input')
        senha_acesso.send_keys("Ieq100420")

        botao_acessar = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/div/form/center[1]')
        botao_acessar.click()
        print("Login realizado com sucesso.")
    except Exception as e:
        print(f"Erro durante o login: {e}")
        driver.quit()

    # --- Navegação até a Página de Relatórios (sem alterações) ---
    try:
        aba_relatorio = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="sidenav-horizontal"]/li[8]/a')))
        ActionChains(driver).move_to_element(aba_relatorio).perform()
        botao_solicitar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sidenav-horizontal"]/li[8]/ul/li[1]/a')))
        botao_solicitar.click()
        WebDriverWait(driver, 10).until(EC.url_to_be("https://console.movingpay.com.br/relatorios/solicitar" ))
        print("Página de solicitação de relatório carregada com sucesso!")
    except Exception as e:
        print(f"Erro ao navegar para 'Solicitar Relatório': {e}")
        driver.save_screenshot("erro_navegacao_relatorio.png")
        driver.quit()

    # --- Preenchimento do Formulário de Relatório (sem alterações) ---
    try:
        exportar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div/div/div/div/div/div[2]/div/div[3]/div[3]/div[2]/button')))
        exportar.click()

        selecionar_relatorio = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/form/div[2]/div[2]/div/div')))
        selecionar_relatorio.click()

        relatorio_antecipacao = driver.find_element(By.XPATH, '/html/body/div[3]/div/div/form/div[2]/div[2]/div/div/input')
        relatorio_antecipacao.send_keys("[03] Transações - Antecipadas")

        selecionar_relatorio_antecipacao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/form/div[2]/div[2]/div/div/div[2]/div')))
        selecionar_relatorio_antecipacao.click()

        tipo_data = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/form/div[2]/div[3]/div/div')))
        tipo_data.click()

        data_pagamento = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/form/div[2]/div[3]/div/div/div[2]/div[2]')))
        data_pagamento.click()
        print("Formulário de relatório preenchido.")

    except Exception as e:
        print(f"Erro ao preencher o formulário de relatório: {e}")
        driver.save_screenshot("erro_formulario_relatorio.png")
        driver.quit()


    try:
        xpath_data_inicial = '/html/body/div[3]/div/div/form/div[2]/div[4]/div[1]/div/input'
        xpath_data_final = '/html/body/div[3]/div/div/form/div[2]/div[4]/div[2]/div/input'
    
        data_inicial = get_primeiro_dia_mes_atual()
        data_final = get_dia_anterior_ajustado()

        # Chama a nova função que simula um humano
        inserir_data_human_like(driver, xpath_data_inicial, data_inicial)
        inserir_data_human_like(driver, xpath_data_final, data_final)  

    except Exception as e:
        print(f"Erro ao inserir as datas: {e}")
        driver.save_screenshot("erro_inserir_datas.png")
        driver.quit()
        return

    # --- Download do Relatório (sem alterações) ---
    try:
        solicitar_enviar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/form/div[3]/button[2]')))
        solicitar_enviar.click()
        print("Solicita do relatório iniciado com sucesso! Aguardando processamento...")
    except Exception as e:
        print(f"Erro ao solicitar relatório: {e}")
        driver.save_screenshot("erro_download.png")

        # fechamento aba Exportar Ralatório
    try: 
        fechar = WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[3]/div/div/form/div[3]/button[1]')))
        fechar.click()

    except Exception as e:
        print(f"Erro ao fechar aba para baixar arquivo: {e}")

    try:

        xpath_icone_recarregar = '//*[@id="root"]/div/div/div/div/div/div[2]/div/div[3]/div[3]/div[3]/i'
        xpath_celula_status = '//*[@id="root"]/div/div/div/div/div/div[2]/div/div[4]/table/tbody/tr[1]/td[8]'
        xpath_icone_download = '//*[@id="root"]/div/div/div/div/div/div[2]/div/div[4]/table/tbody/tr[1]/td[1]/i'

        # Inicio do Loop

        relatorio_baixado = False
        max_tentativas = 40
        intervalo_segundos = 20

        for tentativa in range(1, max_tentativas + 1):
            print(f"--- Tentativa {tentativa}/{max_tentativas} ---")
            
            # 1. Clica no botão para recarregar a lista
            print("Recarregando a lista de relatórios...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath_icone_recarregar))
            ).click()
            time.sleep(3) 

            try:
                # 2. VERIFICA O TEXTO DO STATUS PRIMEIRO
                print("Verificando a célula de status...")
                celula_status = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, xpath_celula_status))
                )
                
                status_texto = celula_status.text
                print(f"Status atual: '{status_texto}'")

                # 3. SE o status for "Concluído", tenta baixar
                if "Concluído" in status_texto:
                    print("Status 'Concluído' detectado! Tentando baixar o arquivo.")
                    
                    icone_download = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, xpath_icone_download))
                    )
                    icone_download.click()
                    
                    print("Download iniciado com sucesso!")
                    relatorio_baixado = True
                    break 
                else:
                    print("Relatório ainda não está pronto. Aguardando para a próxima tentativa...")
                    time.sleep(intervalo_segundos)

            except Exception as e:
                # Se não encontrar a célula de status ou o texto, continua tentando
                print(f"Ainda não foi possível verificar o status. Aguardando... (Erro: {e})")
                time.sleep(intervalo_segundos)

        # Após o loop, verifica se o relatório foi baixado
        if not relatorio_baixado:
            raise Exception(f"O relatório não ficou pronto ou não pôde ser baixado após {max_tentativas} tentativas.")

    except Exception as e:
        print(f"Ocorreu um erro no processo de verificação e download: {e}")
        driver.save_screenshot("erro_loop_verificacao.png")

    finally:
        print("Aguardando 45 segundos para o download finalizar...")
        time.sleep(45)
        
        try:
            renomear_arquivo_antecipacao(caminho_sharepoint_local_antecipacao)
            print("Arquivo renomeado com sucesso. 👌")
        except Exception as e:
            print(f"Erro ao renomear o arquivo baixado: {e}")

        try:
            print("Aguardando 5 segundos para extrair arquivo!")
            time.sleep(5)
            extrair_e_renomear_zip(
                pasta_origem=r"C:\Users\geovane.andrade\OneDrive - Valorem Securitizadora de Crédito S A\BI\Projeto - Banco de Dados MEP\Antecipacoes_zip",
                pasta_destino_base=r"C:\Users\geovane.andrade\OneDrive - Valorem Securitizadora de Crédito S A\BI\Projeto - Banco de Dados MEP\Antecipacoes_banco"
            )
    
        except Exception as e:
            print(f"Erro ao extrair e renomear o arquivo baixado: ❌ {e}")
        
        print("Script finalizado.")
        driver.quit()

importar_arquivo_antecipacao()