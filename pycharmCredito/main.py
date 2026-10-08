
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
import fdb
from flask_bcrypt import Bcrypt


app = Flask(__name__)

bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'Chavesdfglkjhgfdshjkjhgfdcvbmnb'


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

# VERIFICAÇÃO DE SENHA

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

    # Verifica se o usuário está logado

    if 'id_usuario' not in session:

        flash('Precisa estar logado', 'error')

        return redirect(url_for('login'))

    # Verifica se o nome está salvo na sessão

    if 'nome_usuario' not in session:

        session.clear()

        flash('Faça login novamente!', 'error')

        return redirect(url_for('login'))

    else:

        # Envia o nome do usuário para o inicio.html

        return render_template(

            'inicio.html',

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

    # Recebe os dados enviados pelo formulário

    nome = request.form["nome"]

    email = request.form["email"]

    senha = request.form["senha"]

    receita_mensal = request.form["renda_mensal"]

    despesa_mensal = request.form["despesas_mensal"]

    tipo_usuario = request.form["tipo_usuario"]

    # ==========================================

    # VERIFICA OS CAMPOS

    # ==========================================

    if not nome or not email or not senha or not receita_mensal or not despesa_mensal:

        flash("Preencha todos os campos!", "error")

        return redirect(url_for("pagina_cadastro"))

    # ==========================================

    # VERIFICA A SENHA

    # ==========================================

    if not senha_forte(senha):

        flash(

            "A senha deve ter pelo menos 8 caracteres, letras maiúsculas, minúsculas e números.",

            "error"

        )

        return redirect(url_for("pagina_cadastro"))

    # Abre o cursor do banco

    cursor = con.cursor()

    try:

        # ==========================================

        # VERIFICA SE O E-MAIL JÁ EXISTE

        # ==========================================

        cursor.execute("""

                       SELECT 1

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        if cursor.fetchone():

            flash(

                "Este e-mail já está cadastrado!",

                "error"

            )

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CONVERTE OS VALORES FINANCEIROS

        # ==========================================

        receita_mensal = receita_mensal.replace("R$", "").replace(" ", "").strip()

        despesa_mensal = despesa_mensal.replace("R$", "").replace(" ", "").strip()

        if "," in receita_mensal:

            receita_mensal = receita_mensal.replace(".", "").replace(",", ".")

        if "," in despesa_mensal:

            despesa_mensal = despesa_mensal.replace(".", "").replace(",", ".")

        receita_mensal = float(receita_mensal)

        despesa_mensal = float(despesa_mensal)

        if receita_mensal < 0 or despesa_mensal < 0:

            flash("A renda e as despesas não podem ser negativas.", "error")

            return redirect(url_for("pagina_cadastro"))

        # ==========================================

        # CRIPTOGRAFA A SENHA

        # ==========================================

        senha_hash = bcrypt.generate_password_hash(senha).decode("utf-8")

        # ==========================================

        # INSERE O USUÁRIO

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

        # Salva no banco

        con.commit()

        flash(

            "Cadastro realizado com sucesso!",

            "success"

        )

        return redirect(url_for("login"))

    except ValueError:

        con.rollback()

        flash(

            "Digite valores válidos para renda e despesas.",

            "error"

        )

        return redirect(url_for("pagina_cadastro"))

    except Exception as e:

        con.rollback()

        flash(

            f"Ocorreu um erro: {e}",

            "error"

        )

        return redirect(url_for("pagina_cadastro"))

    finally:

        cursor.close()


# ==========================================

# PÁGINA DE LOGIN

# ==========================================

@app.route("/login")

def login():

    return render_template("login.html")


# ==========================================

# ENTRAR NA CONTA

# ==========================================

@app.route("/login", methods=["POST"])

def entrar_usuario():

    # Recebe os dados do formulário

    email = request.form["email"]

    senha = request.form["senha"]

    # Abre o cursor

    cursor = con.cursor()

    try:

        # ==========================================

        # BUSCA ID, NOME E SENHA DO USUÁRIO

        # ==========================================

        cursor.execute("""

                       SELECT ID_USUARIO, NOME, SENHA

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                       """, (email,))

        usuario = cursor.fetchone()

        # ==========================================

        # VERIFICA SE O USUÁRIO EXISTE

        # ==========================================

        if not usuario:

            flash(

                "Usuário não encontrado",

                "error"

            )

            return redirect(url_for("login"))

        # Recebe os três dados encontrados

        id_usuario, nome, senha_hash = usuario

        # ==========================================

        # VERIFICA A SENHA

        # ==========================================

        if bcrypt.check_password_hash(senha_hash, senha):

            # Limpa dados de sessões anteriores

            session.clear()

            # Guarda o ID do usuário

            session["id_usuario"] = id_usuario

            # Guarda o nome do usuário

            session["nome_usuario"] = nome

            # Mensagem de sucesso

            flash(

                "Login realizado com sucesso!",

                "success"

            )

            # Redireciona para o início

            return redirect(url_for("novo"))

        else:

            flash(

                "E-mail ou senha incorretos!",

                "error"

            )

            return redirect(url_for("login"))

    except Exception as e:

        flash(

            f"Ocorreu um erro: {e}",

            "error"

        )

        return redirect(url_for("login"))

    finally:

        cursor.close()


# ==========================================

# INICIA O SERVIDOR

# ==========================================


# ==========================================

# EDITAR USUÁRIO

# ==========================================

@app.route("/editar_usuario")
def editar_usuario():
    # Verifica se está logado

    if "id_usuario" not in session:
        flash("Precisa estar logado!", "error")

        return redirect(url_for("login"))

    cursor = con.cursor()

    try:

        # Busca os dados do usuário logado

        cursor.execute("""

                       SELECT ID_USUARIO,
                              NOME,
                              EMAIL,
                              RECEITA_MENSAL,

                              DESPESA_MENSAL,
                              TIPO_USUARIO

                       FROM USUARIO

                       WHERE ID_USUARIO = ?

                       """, (session["id_usuario"],))

        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuário não encontrado!", "error")

            return redirect(url_for("login"))

        return render_template("editar_usuario.html", usuario=usuario)

    finally:

        cursor.close()


# ==========================================

# SALVAR ALTERAÇÕES DO USUÁRIO

# ==========================================

@app.route("/salvar_edicao", methods=["POST"])
def salvar_edicao():
    # Verifica se está logado

    if "id_usuario" not in session:
        flash("Precisa estar logado!", "error")

        return redirect(url_for("login"))

    # Recebe os campos do HTML

    nome = request.form["nome"].strip()

    email = request.form["email"].strip()

    senha = request.form["senha"]

    receita_mensal = request.form["renda_mensal"]

    despesa_mensal = request.form["despesas_mensal"]

    if not nome or not email:
        flash("Preencha nome e e-mail!", "error")

        return redirect(url_for("editar_usuario"))

    # Se informar uma senha, verifica se é forte

    if senha and not senha_forte(senha):
        flash("A nova senha não atende aos requisitos!", "error")

        return redirect(url_for("editar_usuario"))

    cursor = con.cursor()

    try:

        # Verifica se outro usuário já possui esse e-mail

        cursor.execute("""

                       SELECT ID_USUARIO

                       FROM USUARIO

                       WHERE UPPER(EMAIL) = UPPER(?)

                         AND ID_USUARIO <> ?

                       """, (email, session["id_usuario"]))

        if cursor.fetchone():
            flash("Este e-mail já está cadastrado!", "error")

            return redirect(url_for("editar_usuario"))

        # Converte renda e despesas para números

        receita_mensal = receita_mensal.replace("R$", "").replace(" ", "")

        despesa_mensal = despesa_mensal.replace("R$", "").replace(" ", "")

        if "," in receita_mensal:
            receita_mensal = receita_mensal.replace(".", "").replace(",", ".")

        if "," in despesa_mensal:
            despesa_mensal = despesa_mensal.replace(".", "").replace(",", ".")

        receita_mensal = float(receita_mensal)

        despesa_mensal = float(despesa_mensal)

        if receita_mensal < 0 or despesa_mensal < 0:
            flash("Os valores não podem ser negativos!", "error")

            return redirect(url_for("editar_usuario"))

        # Se informou uma nova senha, atualiza a senha também

        if senha:

            senha_hash = bcrypt.generate_password_hash(senha).decode("utf-8")

            cursor.execute("""

                           UPDATE USUARIO

                           SET NOME           = ?,
                               EMAIL          = ?,
                               SENHA          = ?,

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

            # Se não informou senha, mantém a senha antiga

            cursor.execute("""

                           UPDATE USUARIO

                           SET NOME           = ?,
                               EMAIL          = ?,

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

        # Salva as alterações

        con.commit()

        # Atualiza o nome da sessão

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


































if __name__ == "__main__":

    app.run(debug=True)

