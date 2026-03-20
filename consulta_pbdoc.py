import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = os.environ['LOGIN_URL']

PROCESSO_URL = os.environ['PROCESSO_URL']

USUARIO = os.environ['USUARIO']
SENHA = os.environ['SENHA']

# Coloque as duas variáveis dentro dos parênteses!
# def criar_sessao(usuario_pbdoc, senha_pbdoc):
    
#     # É recomendado usar um nome diferente de 'session' aqui dentro
#     sessao_requests = requests.Session()

#     # O robô agora usa as variáveis que vieram da sua rota
#     payload = {
#         "username": usuario_pbdoc,
#         "password": senha_pbdoc
#     }

#     params = {
#         "cont": "https://pbdoc.pb.gov.br/siga/app/principal"
#     }

#     LOGIN_URL = "https://pbdoc.pb.gov.br/siga/app/principal"
    
#     sessao_requests.post(LOGIN_URL, params=params, data=payload)

#     return sessao_requests

def criar_sessao():
    session = requests.Session()

    payload = {
        "username": USUARIO,
        "password": SENHA
    }

    params = {
        "cont": "https://pbdoc.pb.gov.br/siga/app/principal"
    }

    session.post(LOGIN_URL, params=params, data=payload)
    return session


# def consultar_processo(session, sigla):

#     params = {"sigla": sigla}

#     response = session.get(PROCESSO_URL, params=params)

#     html = response.text
#     soup = BeautifulSoup(html, "html.parser")

#     link = f"https://pbdoc.pb.gov.br/sigaex/app/expediente/doc/exibir?sigla={sigla}"

#     data_verificacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

#     if "inacessível ao usuário" in html.lower():

#         return [
#             sigla,
#             "Documento inacessível ao usuário - Limitado entre lotações",
#             "-",
#             "-",
#             "-",
#             data_verificacao,
#             link
#         ]

#     assunto = "Não encontrado"

#     descricao = soup.find("p", id="descricao")

#     if descricao:
#         assunto = descricao.get_text().replace("Assunto:", "").strip()

#     setor = "Não encontrado"

#     match_setor = re.search(r'\[label="([^"]+)"\]\[color="red"\]', html)

#     if match_setor:
#         setor = match_setor.group(1)

#     status = "Não encontrado"

#     h3 = soup.find("h3")

#     if h3:

#         texto = h3.get_text(strip=True)

#         if "-" in texto:
#             status = texto.split("-")[1].split("[")[0].strip()

#     tempo = "Não encontrado"

#     linhas = soup.find_all("tr")

#     for linha in linhas:

#         if "anexacao" in str(linha).lower() or "juntada" in str(linha).lower():

#             colunas = linha.find_all("td")

#             if len(colunas) >= 1:

#                 tempo = colunas[0].get_text(strip=True)

#                 break

#     return [
#         sigla,
#         assunto,
#         setor,
#         status,
#         tempo,
#         data_verificacao,
#         link
#     ]

def consultar_processo(session, sigla):
    params = {"sigla": sigla}

    response = session.get(PROCESSO_URL, params=params)

    # --- CÓDIGO DE TESTE (Adicione estas 3 linhas) ---
    print(f"\nTentando consultar: {sigla}")
    print(f"URL que o robô realmente abriu: {response.url}")
    # -------------------------------------------------

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    link = f"https://pbdoc.pb.gov.br/sigaex/app/expediente/doc/exibir?sigla={sigla}"
    data_verificacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if "inacessível ao usuário" in html.lower():
        return [sigla, "Documento inacessível", "-", "-", "-", data_verificacao, link]

    # --- Assunto ---
    assunto = "Não encontrado"
    descricao = soup.find("p", id="descricao")
    if descricao:
        assunto = descricao.get_text().replace("Assunto:", "").strip()

    # --- Setor ---
    setor = "Não encontrado"
    match_setor = re.search(r'\[label="([^"]+)"\]\[color="red"\]', html)
    if match_setor:
        setor = match_setor.group(1)

    # --- Status (Ajustado para Volume h3) ---
    status = "Não encontrado"
    h3 = soup.find("h3")
    if h3:
        texto = h3.get_text(strip=True)
        if "-" in texto:
            # Isola a parte após o volume e remove o que estiver em colchetes
            status = texto.split("-", 1)[1].split("[")[0].strip()

    # --- Tempo (Última tramitação relevante) ---
    tempo = "Não encontrado"
    linhas = soup.find_all("tr")
    for linha in linhas:
        texto_linha = linha.get_text().lower()
        if "anexacao" in texto_linha or "juntada" in texto_linha:
            colunas = linha.find_all("td")
            if colunas:
                tempo = colunas[0].get_text(strip=True)
                break

    return [sigla, assunto, setor, status, tempo, data_verificacao, link]

def consultar_lista_stream(processos):

    session = criar_sessao()

    for processo in processos:

        resultado = consultar_processo(session, processo)

        yield resultado