import gspread

from google.oauth2.service_account import Credentials


SCOPES=[
"https://www.googleapis.com/auth/spreadsheets",
"https://www.googleapis.com/auth/drive"
]


def conectar():

    CREDS=Credentials.from_service_account_file(

        "google_credentials.json",

        scopes=SCOPES

    )

    client=gspread.authorize(CREDS)

    return client.open_by_key(

"11EbVwUjQObbKxNYWY8nevfaDQzupOzHs2GZHZ27tLAk"

)


def ler_planilha(aba="SEDE"):

    sheet=conectar().worksheet(aba)

    dados=sheet.get_all_values()

    if len(dados) <=1:

        return []

    return dados[1:]


def atualizar_planilha(dados,aba):

    sheet=conectar().worksheet(aba)

    total=len(sheet.get_all_values())

    if total>1:

        sheet.batch_clear([f"A2:G{total}"])

    if dados:

        sheet.insert_rows(dados,row=2)
        
def salvar_processo_no_final(numero_processo, aba):
    try:
        # Conecta na aba específica
        sheet = conectar().worksheet(aba)
        
        # Cria a linha
        nova_linha = [numero_processo] 
        
        # Adiciona no final
        sheet.append_row(nova_linha)
        
        return True
    except Exception as e:
        print(f"Erro ao acessar a aba '{aba}': {e}")
        return False


def validar_login_email(email_usuario):
    """
    Verifica se o e-mail consta na coluna A da aba 'Configuração de PBdoc'
    """
    try:
        # Abre a aba específica
        sheet = conectar().worksheet("Configuração de PBdoc")
        
        # Pega todos os valores da Coluna A (onde devem estar os e-mails)
        emails_autorizados = sheet.col_values(1)
        
        # Limpeza e comparação (ignora letras maiúsculas e espaços)
        email_limpo = email_usuario.strip().lower()
        lista_limpa = [e.strip().lower() for e in emails_autorizados]
        
        if email_limpo in lista_limpa:
            return True
        return False
        
    except Exception as e:
        print(f"Erro ao validar e-mail: {e}")
        return False
    
def obter_credenciais_pbdoc(email_usuario):
    """
    Busca o usuário e senha do PBdoc salvos na planilha para o e-mail logado.
    Garante o retorno de dois valores do tipo string.
    """
    try:
        # Conecta na aba de configurações
        sheet = conectar().worksheet("Configuração de PBdoc")
        
        # Pega a tabela inteira para a memória
        dados = sheet.get_all_values()
        email_limpo = email_usuario.strip().lower()
        
        # Varre linha por linha procurando o e-mail
        for linha in dados:
            if len(linha) >= 3 and linha[0].strip().lower() == email_limpo:
                # Converte explicitamente para string e remove espaços em branco
                usuario_pbdoc = str(linha[1]).strip()
                senha_pbdoc = str(linha[2]).strip()
                return usuario_pbdoc, senha_pbdoc
        
        # Caso não encontre o e-mail, retorna strings vazias
        return "", ""
        
    except Exception as e:
        print(f"Erro ao buscar credenciais na planilha: {e}")
        # Caso ocorra erro na conexão ou busca, retorna strings vazias
        return "", ""