import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, stream_with_context, Response
from consulta_pbdoc import consultar_lista_stream
from google_sheets import conectar, ler_planilha, atualizar_planilha, salvar_processo_no_final, validar_login_email

app = Flask(__name__)

app.secret_key = "pbsaude_consulta_processos"

configuracoes_pbdoc = {}

ultimos_resultados = []

@app.route("/")
def login():

    return render_template("login.html")

def verificar_credenciais_salvas(email_usuario):
    """
    Verifica se o usuário já possui credenciais do PBdoc salvas (Colunas B e C).
    Retorna True se já tiver tudo preenchido, e False se faltar algo.
    """
    try:
        sheet = conectar().worksheet("Configuração de PBdoc")
        
        # Pega todos os dados da aba de uma vez (mais rápido do que buscar célula por célula)
        dados = sheet.get_all_values()
        email_limpo = email_usuario.strip().lower()
        
        for linha in dados:
            # Verifica se a linha tem dados e se a Coluna A (índice 0) é o e-mail logado
            if len(linha) > 0 and linha[0].strip().lower() == email_limpo:
                
                # Verifica se a linha tem pelo menos 3 colunas e se B (índice 1) e C (índice 2) não estão vazias
                if len(linha) >= 3 and linha[1].strip() != "" and linha[2].strip() != "":
                    return True # Já tem usuário e senha configurados!
                else:
                    return False # Encontrou o e-mail, mas falta usuário ou senha
                    
        return False # Prevenção de erro caso o loop termine
        
    except Exception as e:
        print(f"Erro ao verificar credenciais salvas: {e}")
        return False

@app.route('/entrar', methods=['POST'])
def entrar():
    email_digitado = request.form.get('email').strip().lower()
    print(f"--- TENTATIVA DE LOGIN: {email_digitado} ---")
    
    if validar_login_email(email_digitado):
        print("RESULTADO: E-mail encontrado na planilha!")
        session['email'] = email_digitado
        
        if verificar_credenciais_salvas(email_digitado):
            print("AÇÃO: Tem senha salva, indo para INDEX.")
            return redirect(url_for('index')) # ou 'consulta'
        else:
            print("AÇÃO: NÃO tem senha salva, indo para CONFIGURACAO.")
            return redirect(url_for('configuracao'))
            
    else:
        print("RESULTADO: E-mail NÃO ENCONTRADO. Voltando pro login.")
        return render_template('login.html', erro="Acesso Negado: E-mail não autorizado.")

@app.route('/index')
def index():
    # 1. Trava de Segurança: Verifica se o usuário passou pelo login
    if 'email' not in session:
        # Se não estiver logado, chuta de volta para a tela de login
        # (Verifique se o nome da sua função de login é 'login' ou 'entrar')
        return redirect(url_for('login')) 
    
    # 2. Carrega os dados para preencher a tabela logo que a página abre
    # Pega a unidade da URL (ex: /index?unidade=HRG), ou usa "SEDE" como padrão
    unidade = request.args.get("unidade", "SEDE")
    
    try:
        # Usa a sua função já existente para ler a aba da planilha
        ultimos_processos = ler_planilha(unidade)
    except Exception as e:
        print(f"Erro ao carregar a planilha na rota index: {e}")
        ultimos_processos = [] # Manda uma lista vazia se der erro, pra página não quebrar

    # 3. Renderiza o seu arquivo HTML passando os dados
    return render_template(
        'index.html',
        ultimos=ultimos_processos
    )

@app.route("/config_pbdoc")
def config_pbdoc():

    if "email" not in session:
        return redirect(url_for("login"))

    email = session["email"]

    dados = configuracoes_pbdoc.get(email, {})

    return render_template(
        "config_pbdoc.html",
        email=email,
        usuario_pbdoc=dados.get("usuario_pbdoc",""),
        senha_pbdoc=dados.get("senha_pbdoc","")
    )


@app.route("/salvar_pbdoc", methods=["POST"])
def salvar_pbdoc():

    email = session["email"]

    configuracoes_pbdoc[email] = {
        "usuario_pbdoc":request.form.get("usuario_pbdoc"),
        "senha_pbdoc":request.form.get("senha_pbdoc")
    }

    return redirect(url_for("consulta"))


@app.route("/consulta")
def consulta():
    if "email" not in session:
        return redirect(url_for("login"))
    unidade=request.args.get("unidade","SEDE")

    ultimos=ler_planilha(unidade)

    return render_template(
        "index.html",
        ultimos=ultimos
    )

@app.route("/consultar",methods=["POST"])
def consultar():

    global ultimos_resultados

    texto = request.form.get("processos","")
    processos = [
        p.strip()
        for p in texto.splitlines()
        if p.strip()
    ]

    resultados=[]

    for r in consultar_lista_stream(processos):
        resultados.append(r)
    ultimos_resultados = resultados

    return jsonify(resultados)


@app.route("/atualizar_planilha",methods=["POST"])
def atualizar_planilha_rota():
    dados=request.json["dados"]
    aba=request.json["aba"]
    atualizar_planilha(dados,aba)
    return {"status":"ok"}

@app.route('/adicionar_processo', methods=['POST'])
def adicionar_processo():
    dados = request.get_json()
    numero_processo = dados.get('processo')
    unidade = dados.get('unidade') # Nome da aba vindo do select

    if not numero_processo or not unidade:
        return jsonify({'status': 'erro', 'message': 'Dados incompletos'}), 400

    # Chamamos a função passando a aba (unidade) escolhida
    sucesso = salvar_processo_no_final(numero_processo, unidade)

    if sucesso:
        return jsonify({'status': 'sucesso', 'message': 'Gravado com sucesso!'})
    else:
        return jsonify({'status': 'erro', 'message': f'Não encontrei a aba "{unidade}"'}), 500


@app.route('/atualizar_unidade_stream', methods=['POST'])
def atualizar_unidade_stream():
    # 1. Verifica se o usuário está logado!
    if 'email' not in session:
        return jsonify({"status": "erro", "message": "Usuário não autenticado."}), 401
        
    email_logado = session['email']
    
    # 2. Busca as credenciais (usuário e senha do PBdoc) lá da planilha
    from google_sheets import obter_credenciais_pbdoc # Importe de onde estiver a função
    usuario_pbdoc, senha_pbdoc = obter_credenciais_pbdoc(email_logado)
    print(usuario_pbdoc, senha_pbdoc)
    
    if not usuario_pbdoc or not senha_pbdoc:
        return jsonify({"status": "erro", "message": "Credenciais do PBdoc não configuradas."}), 403

    dados_req = request.get_json()
    unidade = dados_req.get('unidade')

    def gerar_eventos():
        try:
            from google_sheets import conectar, atualizar_planilha
            from consulta_pbdoc import criar_sessao, consultar_processo
            
            sheet = conectar().worksheet(unidade)
            siglas = sheet.col_values(1)[1:] # Pega siglas da coluna A
            
            # 3. CRIA A SESSÃO COM AS CREDENCIAIS
            sessao_pbdoc = criar_sessao()
            
            resultados_finais = []

            for i, sigla in enumerate(siglas):
                # Ignora linhas em branco
                if not sigla.strip():
                    continue
                    
                # 4. Usa a 'sessao_pbdoc' aqui
                resultado = consultar_processo(sessao_pbdoc, sigla)
                resultados_finais.append(resultado)
                
                # Envia o resultado parcial para o Front-end
                yield json.dumps({
                    "status": "parcial",
                    "index": i,
                    "total": len(siglas),
                    "dados": resultado
                }) + "\n"

            # Após terminar o loop, atualiza a planilha de uma vez (batch)
            if resultados_finais:
                atualizar_planilha(resultados_finais, unidade)
            
            yield json.dumps({"status": "concluido", "message": "Planilha atualizada com sucesso!"}) + "\n"

        except Exception as e:
            yield json.dumps({"status": "erro", "message": str(e)}) + "\n"

    return Response(stream_with_context(gerar_eventos()), mimetype='application/json')

# @app.route('/atualizar_unidade', methods=['POST'])
# def rota_atualizar_unidade():
#     dados = request.get_json()
#     nome_aba = dados.get('unidade')

#     if not nome_aba:
#         return jsonify({'status': 'erro', 'message': 'Selecione uma unidade!'}), 400

#     try:
#         # Chama a função unificada
#         sucesso, mensagem = processar_e_atualizar_unidade(nome_aba)
        
#         if sucesso:
#             return jsonify({'status': 'sucesso', 'message': mensagem})
#         else:
#             return jsonify({'status': 'erro', 'message': mensagem})
            
#     except Exception as e:
#         return jsonify({'status': 'erro', 'message': str(e)}), 500
    

@app.route('/editar_processo', methods=['POST'])
def editar_processo():
    dados = request.get_json()
    sigla = dados.get('sigla_original')
    unidade = dados.get('unidade') # A unidade diz qual aba abrir
    
    try:
        # 1. Vai direto na aba da unidade selecionada
        sheet = conectar().worksheet(unidade)
        
        # 2. Busca a sigla APENAS na coluna 1 (Coluna A - PBdoc)
        # Isso é muito mais rápido do que procurar na planilha toda
        celula = sheet.find(sigla, in_column=1)
        
        if celula:
            linha = celula.row
            
            # 3. Atualiza os campos na linha encontrada
            # Col 2: Assunto, Col 3: Setor, Col 5: Tempo
            sheet.update_cell(linha, 2, dados.get('assunto'))
            sheet.update_cell(linha, 3, dados.get('setor'))
            sheet.update_cell(linha, 5, dados.get('tempo'))
            
            return jsonify({'status': 'sucesso', 'message': 'Processo atualizado com sucesso!'})
        
        return jsonify({'status': 'erro', 'message': f'Processo {sigla} não encontrado na unidade {unidade}.'}), 404
        
    except Exception as e:
        print(f"Erro na edição: {e}")
        return jsonify({'status': 'erro', 'message': 'Erro interno ao processar a edição.'}), 500


@app.route('/excluir_processo', methods=['POST'])
def excluir_processo():
    try:
        # 1. Recebe os dados do JavaScript
        dados = request.get_json()
        sigla = dados.get('sigla')
        unidade = dados.get('unidade')

        if not sigla or not unidade:
            return jsonify({'status': 'erro', 'message': 'Dados incompletos para exclusão.'}), 400

        # 2. Conecta na planilha e acessa a aba da unidade
        sheet = conectar().worksheet(unidade)

        # 3. Localiza a célula da sigla APENAS na coluna 1 (PBdoc)
        # Isso garante que não excluiremos a linha errada caso o texto exista em outra coluna
        celula = sheet.find(sigla, in_column=1)

        if celula:
            # 4. Remove a linha inteira pelo índice encontrado
            linha_para_excluir = celula.row
            sheet.delete_rows(linha_para_excluir)
            
            print(f"Sucesso: Processo {sigla} removido da aba {unidade} (Linha {linha_para_excluir})")
            return jsonify({
                'status': 'sucesso', 
                'message': f'O processo {sigla} foi removido da planilha com sucesso!'
            })
        else:
            return jsonify({
                'status': 'erro', 
                'message': f'Processo {sigla} não encontrado na unidade {unidade}.'
            }), 404

    except Exception as e:
        print(f"Erro ao excluir: {e}")
        return jsonify({
            'status': 'erro', 
            'message': f'Erro interno no servidor: {str(e)}'
        }), 500

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

if __name__=="__main__":

    app.run(debug=True)