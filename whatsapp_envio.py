from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os


def enviar_arquivo(numero, arquivo):

    numero = numero.replace("+","").replace(" ","")

    chrome_options = Options()

    chrome_options.add_argument("--start-maximized")

    chrome_options.add_argument("--user-data-dir=chrome_whatsapp")

    driver = webdriver.Chrome(

        service=Service(ChromeDriverManager().install()),

        options=chrome_options

    )

    link = f"https://web.whatsapp.com/send?phone={numero}&text=Processos"

    driver.get(link)

    print("Abrindo WhatsApp...")

    time.sleep(30)


    try:

        print("Procurando botão clip")

        clip = driver.find_element(

            By.CSS_SELECTOR,

            "span[data-icon='clip']"

        )

        clip.click()

        time.sleep(3)


        print("Procurando input file")

        attach = driver.find_element(

            By.CSS_SELECTOR,

            "input[type='file']"

        )

        attach.send_keys(

            os.path.abspath(arquivo)

        )

        time.sleep(6)


        print("Procurando botão enviar")

        send = driver.find_element(

            By.CSS_SELECTOR,

            "span[data-icon='send']"

        )

        send.click()

        print("Arquivo enviado")

        time.sleep(5)

    except Exception as e:

        print("Erro WhatsApp:",e)

    driver.quit()