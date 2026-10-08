
# Importa as ferramentas do Flask para criar páginas, receber dados e controlar o login.

from flask import Flask, render_template, request, flash, redirect, url_for, session

# Permite conectar o Python ao banco de dados Firebird.

import fdb

# Importa o Bcrypt, usado para proteger e verificar as senhas.

from flask_bcrypt import Bcrypt


# Cria o aplicativo Flask, que controla o funcionamento do site.

app = Flask(__name__)

# Liga o Bcrypt ao Flask para trabalhar com as senhas.

bcrypt = Bcrypt(app)

# Chave que protege os dados da sessão. Se mudar, sessões antigas deixam de funcionar.

app.config["SECRET_KEY"] = "Chavesdfglkjhgfdshjkjhgfdcvbmnb"


# ==========================================

# CONEXÃO COM O BANCO

# ==========================================

# Endereço do servidor. localhost significa que está no próprio computador.

host = "localhost"

# Caminho do banco. Se mover o arquivo, precisa atualizar esse caminho.

database = r"C:\Users\Aluno\Downloads\BANCO.FDB"

# Nome do usuário utilizado para entrar no Firebird.

user = "sysdba"

# Senha utilizada para conectar ao Firebird.

password = "sysdba"

# Cria a conexão com o banco utilizando os dados acima.

con = fdb.connect(

    host=host,             # Indica onde está o servidor.

    database=database,     # Indica qual banco será utilizado.

    user=user,             # Informa o usuário do banco.

    password=password      # Informa a senha do banco.

)


# ==========================================

# VERIFICAÇÃO DE SENHA FORTE

# ==========================================

# Cria uma função que verifica se a senha atende às regras.

def senha_forte(senha):

    # Se a senha tiver menos de 8 caracteres, não será aceita.

    # Se mudar 8 para 10, vai exigir pelo menos 10 caracteres.

    if len(senha) < 8:

        return False  # False significa que a senha não foi aprovada.

    # Se a senha não tiver nenhuma letra maiúscula, não aceita.

    elif senha == senha.lower():

        return False

    # Se a senha não tiver nenhuma letra minúscula, não aceita.

    elif senha == senha.upper():

        return False

    # Se a senha tiver apenas letras, não aceita.

    elif senha.isalpha():

        return False

    # Se a senha tiver apenas números, não aceita.

    elif senha.isdigit():

        return False

    # Se passar pelas verificações, a senha será aceita.

    else:

        return True  # True significa que foi aprovada.


# ==========================================

# VERIFICA A SENHA CRIPTOGRAFADA

# ==========================================

# Recebe a senha salva no banco e a senha digitada pelo usuário.

def verificar_senha(senha_hash, senha):

    # Verifica se a senha salva está no formato antigo do Bcrypt.

    if senha_hash.startswith("$2"):

        # Compara a senha digitada com a senha protegida.

        return bcrypt.check_password_hash(senha_hash, senha)

    # Caso contrário, verifica o formato hexadecimal usado no projeto.

    else:

        # bytes.fromhex prepara o hash para a comparação do Bcrypt.

        return bcrypt.check_password_hash(

            bytes.fromhex(senha_hash),

            senha

        )


# ==========================================

# VERIFICA SE O USUÁRIO ESTÁ AUTENTICADO

# ==========================================

# Verifica se o usuário está logado e se a conta continua ativa.

def usuario_autenticado():

    # Se o ID não estiver na sessão, significa que não está logado.

    if "id_usuario" not in session:

        return False

    # Prepara uma consulta ao banco de dados.

    cursor = con.cursor()

    try:

        # Procura a situação da conta do usuário logado.

        cursor.execute("""

                       SELECT ATIVO

                       FROM USUARIO

                       WHERE ID_USUARIO = ?

                       """, (session["id_usuario"],))

        # Pega o resultado da consulta.

        usuario = cursor.fetchone()

        # Verifica se o usuário foi encontrado.

        if usuario:

            # Se ATIVO for 1, a conta pode acessar o sistema.

            # Se for 0, a conta está inativa.

            if usuario[0] == 1:

                return True

        # Se não encontrou o usuário ou ele está inativo, bloqueia o acesso.

        return False

    finally:

        # Fecha o cursor depois de consultar o banco.

        cursor.close()


# ==========================================

# PÁGINA INICIAL DO SITE

# ==========================================

# Define a rota principal. A barra / representa o início do site.

@app.route("/")

def landing():

    # Abre o arquivo landing.html dentro da pasta templates.

    # Se mudar o nome, o arquivo HTML também precisa existir.

    return render_template("landing.html")


# ==========================================

# PÁGINA DO USUÁRIO LOGADO

# ==========================================

# Cria o endereço /novo para abrir a página do usuário.

@app.route("/novo")

def novo():

    # Verifica se o usuário está logado e ativo.

    if not usuario_autenticado():

        # Apaga os dados da sessão para impedir o acesso.

        session.clear()

        # Mostra uma mensagem na página.

        flash("Precisa estar logado e ativo!", "error")

        # Envia o usuário para a página de login.

        return redirect(url_for("login"))

    # Verifica se o nome do usuário está salvo na sessão.

    if "nome_usuario" not in session:

        # Limpa os dados da sessão incompleta.

        session.clear()

        # Mostra uma mensagem para entrar novamente.

        flash("Faça login novamente!", "error")

        # Volta para o login.

        return redirect(url_for("login"))

    # Abre o inicio.html e envia o nome do usuário para aparecer na página.

    return render_template(

        "inicio.html",

        usuario=session["nome_usuario"]

    )


# ==========================================

# PÁGINA DE CADASTRO

# ==========================================

# Cria a rota /cadastro para abrir o formulário.

@app.route("/cadastro")

def pagina_cadastro():

    # Abre a página onde o usuário informa seus dados.

    return render_template("cadastro.html")


# ==========================================

# CADASTRAR USUÁRIO

# ==========================================

# POST significa que esta rota recebe dados enviados pelo formulário.

@app.route("/cadastro", methods=["POST"])

def cadastro():

    # Recebe o nome digitado no campo name="nome".

    nome = request.form["nome"]

    # Recebe o e-mail digitado.

    email = request.form["email"]

    # Recebe a senha digitada.

    senha = request.form["senha"]

    # Recebe a renda mensal informada no cadastro.

    receita_mensal = request.form["renda_mensal"]

    # Recebe as despesas mensais informadas.

    despesa_mensal = request.form["despesas_mensal"]

    # Define o tipo do usuário como empreendedor.

    # O número 7 representa esse tipo no banco.

    tipo_usuario = 7

    # Verifica se algum campo obrigatório ficou vazio.

    # O "or" significa "ou": basta um estar vazio para entrar neste if.

    if not nome or not email or not senha or not receita_mensal or not despesa_mensal:

        # Mostra uma mensagem se faltar algum dado.

        flash("Preencha todos os campos!", "error")

        # Volta para a página de cadastro.

        return redirect(url_for("pagina_cadastro"))

    # Chama a função senha_forte para verificar a senha.

    if not senha_forte(senha):

        # Mostra uma mensagem se a senha for recusada.

        flash(

            "A senha deve ter pelo menos 8 caracteres, letras maiúsculas, minúsculas e números.",

            "error"

        )

        # Volta para o cadastro para corrigir a senha.

        return redirect(url_for("pagina_cadastro"))

    # Cria um cursor para fazer consultas e alterações no Firebird.

    cursor = con.cursor()

    # try tenta executar o código e permite tratar erros.

    try:

        # ==========================================

        # VERIFICA E-MAIL REPETIDO

        # ==========================================

        # SELECT procura dados no banco.

        # UPPER compara os e-mails sem diferenciar maiúsculas de minúsculas.

        # O ? recebe o e-mail enviado pelo Python.

        cursor.execute("""

                       SELECT ID_USUARIO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        # fetchone pega um resultado. Se encontrou, o e-mail já existe.

        if cursor.fetchone():

            # Mostra que não pode cadastrar o mesmo e-mail.

            flash("Este e-mail já está cadastrado!", "error")

            # Volta para o formulário.

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CONVERTE RENDA E DESPESAS

        # ==========================================

        # float transforma a renda em número com casas decimais.

        receita_mensal = float(receita_mensal)

        # Faz a mesma conversão com a despesa.

        despesa_mensal = float(despesa_mensal)

        # O < 0 verifica se o valor é negativo.

        if receita_mensal < 0 or despesa_mensal < 0:

            # Mostra o erro se algum valor for negativo.

            flash("Os valores não podem ser negativos!", "error")

            # Volta para o cadastro.

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CRIPTOGRAFA A SENHA

        # ==========================================

        # Protege a senha com Bcrypt e salva o resultado em hexadecimal.

        # Não guarda a senha original digitada pelo usuário.

        senha_hash = bcrypt.generate_password_hash(senha).hex()

        # ==========================================

        # SALVA O USUÁRIO NO BANCO

        # ==========================================

        # INSERT adiciona um novo usuário na tabela USUARIO.

        # Cada ? recebe um valor da lista que vem logo abaixo.

        cursor.execute("""

                       INSERT INTO USUARIO

                           (NOME, EMAIL, SENHA, RECEITA_MENSAL, DESPESA_MENSAL, TIPO_USUARIO)

                       VALUES (?, ?, ?, ?, ?, ?)

                       """, (

                           nome,              # Nome que será salvo.

                           email,             # E-mail que será salvo.

                           senha_hash,        # Senha protegida.

                           receita_mensal,    # Renda mensal.

                           despesa_mensal,    # Despesas mensais.

                           tipo_usuario       # Tipo de usuário: 7.

                       ))

        # Confirma e grava o cadastro no banco.

        con.commit()

        # Mostra uma mensagem de sucesso.

        flash("Cadastro realizado com sucesso!", "success")

        # Abre a página de login.

        return redirect(url_for("login"))

    # Se a renda ou despesa não puder ser convertida para número.

    except ValueError:

        # Cancela alterações pendentes no banco.

        con.rollback()

        # Mostra uma mensagem explicando o erro.

        flash("Digite valores válidos para renda e despesas.", "error")

        # Volta para o cadastro.

        return redirect(url_for("pagina_cadastro"))

    # Trata outros erros que acontecerem durante o cadastro.

    except Exception as e:

        # Cancela alterações pendentes.

        con.rollback()

        # Mostra o erro encontrado.

        flash(f"Erro ao cadastrar: {e}", "error")

        # Volta para o cadastro.

        return redirect(url_for("pagina_cadastro"))

    # O finally executa no final, mesmo se acontecer erro.

    finally:

        # Fecha o cursor para terminar a consulta.

        cursor.close()


# ==========================================

# PÁGINA DE LOGIN

# ==========================================

# Define o endereço da página de login.

@app.route("/login")

def login():

    # Abre o login.html, onde o usuário digita e-mail e senha.

   # só tirar de comentario quando quiser desbloquear o login
   # session["tentativas"] = 0

    return render_template("login.html")


# ==========================================

# ENTRAR NA CONTA

# ==========================================

# Recebe os dados enviados pelo formulário de login.

@app.route("/login", methods=["POST"])

def entrar_usuario():

    # Recebe o e-mail digitado.

    email = request.form["email"]

    # Recebe a senha digitada.

    senha = request.form["senha"]

    # Verifica se o contador de tentativas ainda não existe na sessão.

    if "tentativas" not in session:

        # Começa com zero tentativas erradas.

        session["tentativas"] = 0

    # Se chegar a 3 erros nesta sessão, impede novas tentativas.

    # Se mudar 3 para 5, serão permitidos até 5 erros.

    if session["tentativas"] >= 3:

        # Mostra uma mensagem de bloqueio.

        flash("Login bloqueado após 3 tentativas!", "error")

        # Volta para a página de login.

        return redirect(url_for("login"))

    # Abre uma consulta ao banco.

    cursor = con.cursor()

    try:

        # ==========================================

        # PROCURA O USUÁRIO PELO E-MAIL

        # ==========================================

        # Busca o ID, nome, senha protegida e situação da conta.

        cursor.execute("""

                       SELECT ID_USUARIO, NOME, SENHA, ATIVO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        # Recebe o usuário encontrado na consulta.

        usuario = cursor.fetchone()

        # ==========================================

        # VERIFICA O LOGIN

        # ==========================================

        # Confere se encontrou algum usuário.

        if usuario:

            # Separa os dados encontrados em quatro variáveis.

            id_usuario, nome, senha_hash, ativo = usuario

            # Se ATIVO não for 1, a conta não pode fazer login.

            if ativo != 1:

                # Mostra que o usuário está inativo.

                flash("Usuário inativo! Não é possível fazer login.", "error")

                # Volta para o login.

                return redirect(url_for("login"))

            # Compara a senha digitada com a senha protegida no banco.

            if verificar_senha(senha_hash, senha):

                # Apaga as tentativas erradas anteriores.

                session.clear()

                # Guarda o ID para reconhecer quem está logado.

                session["id_usuario"] = id_usuario

                # Guarda o nome para mostrar na página inicial.

                session["nome_usuario"] = nome

                # Mostra que entrou na conta.

                flash("Login realizado com sucesso!", "success")

                # Abre a página inicial do usuário.

                return redirect(url_for("novo"))

        # ==========================================

        # CONTA AS TENTATIVAS INCORRETAS

        # ==========================================

        # Soma 1 ao contador sempre que o login falha.

        session["tentativas"] = session["tentativas"] + 1

        # Confere se atingiu o limite de 3 erros.

        if session["tentativas"] >= 3:

            # Mostra a mensagem de bloqueio.

            flash("Login bloqueado após 3 tentativas!", "error")

        # Se ainda não chegou a 3 erros.

        else:

            # Avisa que os dados estão incorretos.

            flash("E-mail ou senha incorretos!", "error")

        # Volta para o login.

        return redirect(url_for("login"))

    # Trata erros durante a consulta.

    except Exception as e:

        # Cancela alterações pendentes.

        con.rollback()

        # Mostra o erro.

        flash(f"Ocorreu um erro: {e}", "error")

        # Volta para o login.

        return redirect(url_for("login"))

    finally:

        # Fecha o cursor depois de terminar.

        cursor.close()


# ==========================================

# LOGOUT

# ==========================================

# Cria a rota de saída. POST recebe o clique enviado pelo formulário.

@app.route("/logout", methods=["POST"])

def logout():

    # Verifica se o usuário está logado antes de permitir a saída.

    if "id_usuario" not in session:

        # Mostra que é necessário estar logado.

        flash("Precisa estar logado!", "error")

        # Volta para a página de login.

        return redirect(url_for("login"))

    # Apaga os dados da sessão e desconecta o usuário.

    session.clear()

    # Mostra que a pessoa saiu da conta.

    flash("Você saiu da sua conta!", "success")

    # Volta para a página de login.

    return redirect(url_for("login"))


# ==========================================

# EDITAR USUÁRIO

# ==========================================

# Define o endereço da página de edição de perfil.

@app.route("/editar_usuario")

def editar_usuario():

    # Impede que usuários deslogados ou inativos entrem.

    if not usuario_autenticado():

        # Limpa a sessão.

        session.clear()

        # Mostra uma mensagem.

        flash("Precisa estar logado e ativo!", "error")

        # Volta para o login.

        return redirect(url_for("login"))

    # Prepara uma consulta ao banco.

    cursor = con.cursor()

    try:

        # Busca os dados do usuário que está logado.

        # WHERE garante que pega apenas o usuário com aquele ID.

        cursor.execute("""

                       SELECT ID_USUARIO, NOME, EMAIL,

                              RECEITA_MENSAL, DESPESA_MENSAL, TIPO_USUARIO

                       FROM USUARIO

                       WHERE ID_USUARIO = ?

                       """, (session["id_usuario"],))

        # Pega os dados encontrados.

        usuario = cursor.fetchone()

        # Verifica se o usuário foi encontrado.

        if not usuario:

            # Apaga a sessão.

            session.clear()

            # Mostra que o usuário não existe.

            flash("Usuário não encontrado!", "error")

            # Volta para o login.

            return redirect(url_for("login"))

        # Abre o editar_usuario.html com os dados da conta.

        return render_template(

            "editar_usuario.html",

            usuario=usuario

        )

    finally:

        # Fecha a consulta depois de terminar.

        cursor.close()


# ==========================================

# SALVAR EDIÇÃO DO USUÁRIO

# ==========================================

# Cria a rota que recebe as alterações do formulário.

@app.route("/salvar_edicao", methods=["POST"])

def salvar_edicao():

    # Impede alterações de usuários deslogados ou inativos.

    if not usuario_autenticado():

        # Encerra a sessão.

        session.clear()

        # Mostra a mensagem.

        flash("Precisa estar logado e ativo!", "error")

        # Volta para o login.

        return redirect(url_for("login"))

    # Recebe o nome informado no formulário.

    nome = request.form["nome"]

    # Recebe o e-mail informado.

    email = request.form["email"]

    # Recebe a senha nova, caso a pessoa queira alterar.

    senha = request.form["senha"]

    # Recebe a renda mensal.

    receita_mensal = request.form["renda_mensal"]

    # Recebe as despesas mensais.

    despesa_mensal = request.form["despesas_mensal"]

    # Confere se os campos obrigatórios foram preenchidos.

    if not nome or not email or not receita_mensal or not despesa_mensal:

        # Mostra que existem campos vazios.

        flash("Preencha todos os campos!", "error")

        # Volta para a edição.

        return redirect(url_for("editar_usuario"))

    # Se digitou uma nova senha, confere se ela é forte.

    if senha and not senha_forte(senha):

        # Mostra que a nova senha não foi aceita.

        flash("A nova senha não atende aos requisitos!", "error")

        # Volta para a edição.

        return redirect(url_for("editar_usuario"))

    # Abre uma consulta ao banco.

    cursor = con.cursor()

    try:

        # ==========================================

        # VERIFICA E-MAIL REPETIDO

        # ==========================================

        # Procura o mesmo e-mail em outras contas.

        # <> significa diferente. Assim, ignora o ID de quem está editando.

        cursor.execute("""

                       SELECT ID_USUARIO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                         AND ID_USUARIO <> ?

                       """, (email, session["id_usuario"]))

        # Se encontrar outro usuário com o e-mail, impede salvar.

        if cursor.fetchone():

            # Mostra o erro.

            flash("Este e-mail já está cadastrado!", "error")

            # Volta para a edição.

            return redirect(url_for("editar_usuario"))

        # ==========================================

        # CONVERTE RENDA E DESPESAS

        # ==========================================

        # Transforma a renda em número decimal.

        receita_mensal = float(receita_mensal)

        # Transforma as despesas em número decimal.

        despesa_mensal = float(despesa_mensal)

        # Verifica se algum valor é negativo.

        if receita_mensal < 0 or despesa_mensal < 0:

            # Mostra a mensagem de erro.

            flash("Os valores não podem ser negativos!", "error")

            # Volta para a edição.

            return redirect(url_for("editar_usuario"))

        # ==========================================

        # ATUALIZA OS DADOS

        # ==========================================

        # Se o usuário digitou uma senha nova.

        if senha:

            # Busca a senha atual e as três anteriores no banco.

            cursor.execute("""

                           SELECT SENHA, SENHA_ANTERIOR1,

                                  SENHA_ANTERIOR2, SENHA_ANTERIOR3

                           FROM USUARIO

                           WHERE ID_USUARIO = ?

                           """, (session["id_usuario"],))

            # Pega os resultados encontrados.

            dados = cursor.fetchone()

            # Confere se encontrou o usuário.

            if not dados:

                # Apaga a sessão.

                session.clear()

                # Mostra o erro.

                flash("Usuário não encontrado!", "error")

                # Volta para o login.

                return redirect(url_for("login"))

            # ==========================================

            # VERIFICA AS SENHAS ANTERIORES

            # ==========================================

            # Verifica uma por uma: senha atual e as três anteriores.

            for senha_antiga in dados:

                # Ignora os campos que ainda estão vazios.

                if senha_antiga:

                    # Compara a nova senha com cada senha já utilizada.

                    if verificar_senha(senha_antiga, senha):

                        # Impede repetir senhas recentes.

                        flash(

                            "Você não pode reutilizar uma das últimas 3 senhas!",

                            "error"

                        )

                        # Volta para a edição.

                        return redirect(url_for("editar_usuario"))

            # ==========================================

            # CRIPTOGRAFA A NOVA SENHA

            # ==========================================

            # Protege a nova senha usando Bcrypt.

            senha_hash = bcrypt.generate_password_hash(senha).hex()

            # ==========================================

            # ATUALIZA OS DADOS E O HISTÓRICO

            # ==========================================

            # UPDATE altera os dados que já existem na tabela.

            # As senhas anteriores passam para a próxima posição.

            # A senha atual passa para SENHA_ANTERIOR1.

            # A senha nova entra no campo SENHA.

            cursor.execute("""

                           UPDATE USUARIO

                           SET NOME = ?,

                               EMAIL = ?,

                               SENHA_ANTERIOR3 = SENHA_ANTERIOR2,

                               SENHA_ANTERIOR2 = SENHA_ANTERIOR1,

                               SENHA_ANTERIOR1 = SENHA,

                               SENHA = ?,

                               RECEITA_MENSAL = ?,

                               DESPESA_MENSAL = ?

                           WHERE ID_USUARIO = ?

                           """, (

                               nome,                  # Novo nome.

                               email,                 # Novo e-mail.

                               senha_hash,            # Nova senha protegida.

                               receita_mensal,        # Nova renda mensal.

                               despesa_mensal,        # Nova despesa mensal.

                               session["id_usuario"]  # ID do usuário que será alterado.

                           ))

        # Se não digitou uma nova senha.

        else:

            # Atualiza os outros dados sem modificar a senha.

            cursor.execute("""

                           UPDATE USUARIO

                           SET NOME = ?,

                               EMAIL = ?,

                               RECEITA_MENSAL = ?,

                               DESPESA_MENSAL = ?

                           WHERE ID_USUARIO = ?

                           """, (

                               nome,                  # Nome atualizado.

                               email,                 # E-mail atualizado.

                               receita_mensal,        # Renda atualizada.

                               despesa_mensal,        # Despesa atualizada.

                               session["id_usuario"]  # ID de quem está logado.

                           ))

        # ==========================================

        # SALVA NO BANCO

        # ==========================================

        # Confirma as alterações no Firebird.

        con.commit()

        # Atualiza o nome na sessão para mostrar o nome novo no site.

        session["nome_usuario"] = nome

        # Mostra que os dados foram atualizados.

        flash("Usuário atualizado com sucesso!", "success")

        # Volta para a página inicial do usuário.

        return redirect(url_for("novo"))

    # Trata erros quando renda ou despesas não são números válidos.

    except ValueError:

        # Cancela alterações pendentes.

        con.rollback()

        # Mostra a mensagem.

        flash("Digite valores numéricos válidos!", "error")

        # Volta para a edição.

        return redirect(url_for("editar_usuario"))

    # Trata outros erros que acontecerem.

    except Exception as e:

        # Cancela alterações pendentes.

        con.rollback()

        # Mostra o erro encontrado.

        flash(f"Erro ao editar usuário: {e}", "error")

        # Volta para a edição.

        return redirect(url_for("editar_usuario"))

    finally:

        # Fecha o cursor depois de terminar.

        cursor.close()


# ==========================================

# INICIA O SERVIDOR

# ==========================================

# Verifica se este arquivo está sendo executado diretamente.

if __name__ == "__main__":

    # Inicia o servidor Flask.

    # debug=True ajuda a encontrar erros durante os testes.

    # Em um site publicado, deve ficar desativado.

    app.run(debug=True)

