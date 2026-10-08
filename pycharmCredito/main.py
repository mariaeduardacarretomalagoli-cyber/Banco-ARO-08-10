
from flask import Flask, render_template, request, flash, redirect, url_for, session

import fdb

from flask_bcrypt import Bcrypt


app = Flask(__name__)

bcrypt = Bcrypt(app)

app.config["SECRET_KEY"] = "Chavesdfglkjhgfdshjkjhgfdcvbmnb"


# ==========================================

# CONEXÃO COM O BANCO

# ==========================================

host = "localhost"

database = r"C:\Users\Aluno\Downloads\BANCO.FDB"

user = "sysdba"

password = "sysdba"

con = fdb.connect(

    host=host,

    database=database,

    user=user,

    password=password

)


# ==========================================

# VERIFICAÇÃO DE SENHA FORTE

# ==========================================

def senha_forte(senha):

    if len(senha) < 8:

        return False

    elif senha == senha.lower():

        return False

    elif senha == senha.upper():

        return False

    elif senha.isalpha():

        return False

    elif senha.isdigit():

        return False

    else:

        return True


# ==========================================

# VERIFICA A SENHA CRIPTOGRAFADA

# ==========================================

def verificar_senha(senha_hash, senha):

    # Verifica os hashes antigos

    if senha_hash.startswith("$2"):

        return bcrypt.check_password_hash(senha_hash, senha)

    # Verifica os hashes novos

    else:

        return bcrypt.check_password_hash(

            bytes.fromhex(senha_hash),

            senha

        )


# ==========================================

# VERIFICA SE O USUÁRIO ESTÁ AUTENTICADO

# ==========================================

def usuario_autenticado():

    # Verifica se está logado

    if "id_usuario" not in session:

        return False

    cursor = con.cursor()

    try:

        # Busca se o usuário está ativo

        cursor.execute("""

                       SELECT ATIVO

                       FROM USUARIO

                       WHERE ID_USUARIO = ?

                       """, (session["id_usuario"],))

        usuario = cursor.fetchone()

        # Só permite usuário existente e ativo

        if usuario:

            if usuario[0] == 1:

                return True

        return False

    finally:

        cursor.close()


# ==========================================

# PÁGINA INICIAL

# ==========================================

@app.route("/")

def landing():

    return render_template("landing.html")


# ==========================================

# PÁGINA DO USUÁRIO LOGADO

# ==========================================

@app.route("/novo")

def novo():

    # Verifica se está logado e ativo

    if not usuario_autenticado():

        session.clear()

        flash("Precisa estar logado e ativo!", "error")

        return redirect(url_for("login"))

    # Verifica se o nome está na sessão

    if "nome_usuario" not in session:

        session.clear()

        flash("Faça login novamente!", "error")

        return redirect(url_for("login"))

    # Mostra a página com o nome do usuário

    return render_template(

        "inicio.html",

        usuario=session["nome_usuario"]

    )


# ==========================================

# PÁGINA DE CADASTRO

# ==========================================

@app.route("/cadastro")

def pagina_cadastro():

    return render_template("cadastro.html")


# ==========================================

# CADASTRAR USUÁRIO

# ==========================================

@app.route("/cadastro", methods=["POST"])

def cadastro():

    # Recebe os dados do HTML

    nome = request.form["nome"]

    email = request.form["email"]

    senha = request.form["senha"]

    receita_mensal = request.form["renda_mensal"]

    despesa_mensal = request.form["despesas_mensal"]

    # Tipo de usuário empreendedor

    tipo_usuario = 7

    # Verifica se os campos estão preenchidos

    if not nome or not email or not senha or not receita_mensal or not despesa_mensal:

        flash("Preencha todos os campos!", "error")

        return redirect(url_for("pagina_cadastro"))

    # Verifica se a senha é forte

    if not senha_forte(senha):

        flash(

            "A senha deve ter pelo menos 8 caracteres, letras maiúsculas, minúsculas e números.",

            "error"

        )

        return redirect(url_for("pagina_cadastro"))

    cursor = con.cursor()

    try:

        # ==========================================

        # NÃO PERMITE E-MAIL REPETIDO

        # ==========================================

        cursor.execute("""

                       SELECT ID_USUARIO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        if cursor.fetchone():

            flash("Este e-mail já está cadastrado!", "error")

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CONVERTE RENDA E DESPESAS

        # ==========================================

        receita_mensal = float(receita_mensal)

        despesa_mensal = float(despesa_mensal)

        if receita_mensal < 0 or despesa_mensal < 0:

            flash("Os valores não podem ser negativos!", "error")

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CRIPTOGRAFA A SENHA

        # ==========================================

        senha_hash = bcrypt.generate_password_hash(senha).hex()

        # ==========================================

        # SALVA O USUÁRIO NO BANCO

        # ==========================================

        cursor.execute("""

                       INSERT INTO USUARIO

                           (NOME, EMAIL, SENHA, RECEITA_MENSAL, DESPESA_MENSAL, TIPO_USUARIO)

                       VALUES (?, ?, ?, ?, ?, ?)

                       """, (

                           nome,

                           email,

                           senha_hash,

                           receita_mensal,

                           despesa_mensal,

                           tipo_usuario

                       ))

        con.commit()

        flash("Cadastro realizado com sucesso!", "success")

        return redirect(url_for("login"))

    except ValueError:

        con.rollback()

        flash("Digite valores válidos para renda e despesas.", "error")

        return redirect(url_for("pagina_cadastro"))

    except Exception as e:

        con.rollback()

        flash(f"Erro ao cadastrar: {e}", "error")

        return redirect(url_for("pagina_cadastro"))

    finally:

        cursor.close()


# ==========================================

# PÁGINA DE LOGIN

# ==========================================

@app.route("/login")

def login():

    # Para desbloqueio temporário durante os testes:

    # session["tentativas"] = 0

    return render_template("login.html")


# ==========================================

# ENTRAR NA CONTA

# ==========================================

@app.route("/login", methods=["POST"])

def entrar_usuario():

    # Recebe os dados do formulário

    email = request.form["email"]

    senha = request.form["senha"]

    # Inicia o contador de tentativas

    if "tentativas" not in session:

        session["tentativas"] = 0

    # Verifica se o login já está bloqueado

    if session["tentativas"] >= 3:

        flash("Login bloqueado após 3 tentativas!", "error")

        return redirect(url_for("login"))

    cursor = con.cursor()

    try:

        # ==========================================

        # PROCURA O USUÁRIO PELO E-MAIL

        # ==========================================

        cursor.execute("""

                       SELECT ID_USUARIO, NOME, SENHA, ATIVO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        usuario = cursor.fetchone()

        # ==========================================

        # VERIFICA O LOGIN

        # ==========================================

        if usuario:

            id_usuario, nome, senha_hash, ativo = usuario

            # Não permite login de usuário inativo

            if ativo != 1:

                flash("Usuário inativo! Não é possível fazer login.", "error")

                return redirect(url_for("login"))

            # Verifica se a senha está correta

            if verificar_senha(senha_hash, senha):

                # Limpa as tentativas anteriores

                session.clear()

                # Guarda os dados do usuário logado

                session["id_usuario"] = id_usuario

                session["nome_usuario"] = nome

                flash("Login realizado com sucesso!", "success")

                return redirect(url_for("novo"))

        # ==========================================

        # CONTA AS TENTATIVAS INCORRETAS

        # ==========================================

        session["tentativas"] = session["tentativas"] + 1

        if session["tentativas"] >= 3:

            flash("Login bloqueado após 3 tentativas!", "error")

        else:

            flash("E-mail ou senha incorretos!", "error")

        return redirect(url_for("login"))

    except Exception as e:

        con.rollback()

        flash(f"Ocorreu um erro: {e}", "error")

        return redirect(url_for("login"))

    finally:

        cursor.close()


# ==========================================

# LOGOUT

# ==========================================

@app.route("/logout", methods=["POST"])

def logout():

    # Verifica se o usuário está logado

    if "id_usuario" not in session:

        flash("Precisa estar logado!", "error")

        return redirect(url_for("login"))

    # Encerra a sessão

    session.clear()

    flash("Você saiu da sua conta!", "success")

    return redirect(url_for("login"))


# ==========================================

# EDITAR USUÁRIO

# ==========================================

@app.route("/editar_usuario")

def editar_usuario():

    # Verifica se está logado e ativo

    if not usuario_autenticado():

        session.clear()

        flash("Precisa estar logado e ativo!", "error")

        return redirect(url_for("login"))

    cursor = con.cursor()

    try:

        # Busca os dados do usuário logado

        cursor.execute("""

                       SELECT ID_USUARIO, NOME, EMAIL,

                              RECEITA_MENSAL, DESPESA_MENSAL, TIPO_USUARIO

                       FROM USUARIO

                       WHERE ID_USUARIO = ?

                       """, (session["id_usuario"],))

        usuario = cursor.fetchone()

        if not usuario:

            session.clear()

            flash("Usuário não encontrado!", "error")

            return redirect(url_for("login"))

        return render_template(

            "editar_usuario.html",

            usuario=usuario

        )

    finally:

        cursor.close()


# ==========================================

# SALVAR EDIÇÃO DO USUÁRIO

# ==========================================

@app.route("/salvar_edicao", methods=["POST"])

def salvar_edicao():

    # Verifica se está logado e ativo

    if not usuario_autenticado():

        session.clear()

        flash("Precisa estar logado e ativo!", "error")

        return redirect(url_for("login"))

    # Recebe os dados do formulário

    nome = request.form["nome"]

    email = request.form["email"]

    senha = request.form["senha"]

    receita_mensal = request.form["renda_mensal"]

    despesa_mensal = request.form["despesas_mensal"]

    # Verifica se os campos estão preenchidos

    if not nome or not email or not receita_mensal or not despesa_mensal:

        flash("Preencha todos os campos!", "error")

        return redirect(url_for("editar_usuario"))

    # Verifica a nova senha

    if senha and not senha_forte(senha):

        flash("A nova senha não atende aos requisitos!", "error")

        return redirect(url_for("editar_usuario"))

    cursor = con.cursor()

    try:

        # ==========================================

        # VERIFICA E-MAIL REPETIDO

        # ==========================================

        cursor.execute("""

                       SELECT ID_USUARIO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                         AND ID_USUARIO <> ?

                       """, (email, session["id_usuario"]))

        if cursor.fetchone():

            flash("Este e-mail já está cadastrado!", "error")

            return redirect(url_for("editar_usuario"))

        # ==========================================

        # CONVERTE RENDA E DESPESAS

        # ==========================================

        receita_mensal = float(receita_mensal)

        despesa_mensal = float(despesa_mensal)

        if receita_mensal < 0 or despesa_mensal < 0:

            flash("Os valores não podem ser negativos!", "error")

            return redirect(url_for("editar_usuario"))

        # ==========================================

        # ATUALIZA OS DADOS

        # ==========================================

        if senha:

            # Busca a senha atual e as três anteriores

            cursor.execute("""

                           SELECT SENHA, SENHA_ANTERIOR1,

                                  SENHA_ANTERIOR2, SENHA_ANTERIOR3

                           FROM USUARIO

                           WHERE ID_USUARIO = ?

                           """, (session["id_usuario"],))

            dados = cursor.fetchone()

            if not dados:

                session.clear()

                flash("Usuário não encontrado!", "error")

                return redirect(url_for("login"))

            # ==========================================

            # VERIFICA AS SENHAS ANTERIORES

            # ==========================================

            for senha_antiga in dados:

                # Ignora os campos vazios

                if senha_antiga:

                    if verificar_senha(senha_antiga, senha):

                        flash(

                            "Você não pode reutilizar uma das últimas 3 senhas!",

                            "error"

                        )

                        return redirect(url_for("editar_usuario"))

            # ==========================================

            # CRIPTOGRAFA A NOVA SENHA

            # ==========================================

            senha_hash = bcrypt.generate_password_hash(senha).hex()

            # ==========================================

            # ATUALIZA OS DADOS E O HISTÓRICO

            # ==========================================

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

                               nome,

                               email,

                               senha_hash,

                               receita_mensal,

                               despesa_mensal,

                               session["id_usuario"]

                           ))

        else:

            # Atualiza os dados sem modificar a senha

            cursor.execute("""

                           UPDATE USUARIO

                           SET NOME = ?,

                               EMAIL = ?,

                               RECEITA_MENSAL = ?,

                               DESPESA_MENSAL = ?

                           WHERE ID_USUARIO = ?

                           """, (

                               nome,

                               email,

                               receita_mensal,

                               despesa_mensal,

                               session["id_usuario"]

                           ))

        # ==========================================

        # SALVA NO BANCO

        # ==========================================

        con.commit()

        # Atualiza o nome na sessão

        session["nome_usuario"] = nome

        flash("Usuário atualizado com sucesso!", "success")

        return redirect(url_for("novo"))

    except ValueError:

        con.rollback()

        flash("Digite valores numéricos válidos!", "error")

        return redirect(url_for("editar_usuario"))

    except Exception as e:

        con.rollback()

        flash(f"Erro ao editar usuário: {e}", "error")

        return redirect(url_for("editar_usuario"))

    finally:

        cursor.close()


# ==========================================

# INICIA O SERVIDOR

# ==========================================

if __name__ == "__main__":

    app.run(debug=True)

