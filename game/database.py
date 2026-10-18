"""
Módulo de banco de dados - Jardim das Tarefas (Projeto 016)
Gerencia toda a persistência em SQLite: usuários, canteiros, tarefas e histórico.
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(BASE_DIR, "jardim.db")

CATEGORIAS = ("habitos", "diarias", "afazeres")


def obter_conexao():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT UNIQUE NOT NULL,
            nome_exibicao TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            sal TEXT NOT NULL,
            pergunta_secreta TEXT NOT NULL,
            resposta_secreta_hash TEXT NOT NULL,
            dificuldade TEXT NOT NULL DEFAULT 'medio',
            sementes INTEGER NOT NULL DEFAULT 20,
            xp_total INTEGER NOT NULL DEFAULT 0,
            ultima_data_acesso TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
    """)

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN xp_total INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conquistas_desbloqueadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            conquista_id TEXT NOT NULL,
            data_desbloqueio TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, conquista_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canteiros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            categoria TEXT NOT NULL CHECK (categoria IN ('habitos','diarias','afazeres')),
            estagio INTEGER NOT NULL DEFAULT 1,
            saude INTEGER NOT NULL DEFAULT 100,
            vivo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, categoria)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            categoria TEXT NOT NULL CHECK (categoria IN ('habitos','diarias','afazeres')),
            titulo TEXT NOT NULL,
            tipo_habito TEXT,
            prioridade TEXT,
            prazo TEXT,
            concluida INTEGER NOT NULL DEFAULT 0,
            ultima_conclusao TEXT,
            data_criacao TEXT NOT NULL,
            cliques_bom_hoje INTEGER NOT NULL DEFAULT 0,
            cliques_ruim_hoje INTEGER NOT NULL DEFAULT 0,
            data_cliques_habito TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    for coluna_sql in (
        "ALTER TABLE tarefas ADD COLUMN cliques_bom_hoje INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE tarefas ADD COLUMN cliques_ruim_hoje INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE tarefas ADD COLUMN data_cliques_habito TEXT",
    ):
        try:
            cursor.execute(coluna_sql)
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            tarefas_concluidas INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, data)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_comprados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            categoria_equipada TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, item_id)
        )
    """)

    conexao.commit()
    conexao.close()


# ---------- Autenticação ----------

def gerar_hash(texto, sal):
    return hashlib.sha256((sal + texto).encode("utf-8")).hexdigest()


def criar_usuario(nome_usuario, nome_exibicao, senha, pergunta_secreta, resposta_secreta):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    sal = secrets.token_hex(16)
    senha_hash = gerar_hash(senha, sal)
    resposta_hash = gerar_hash(resposta_secreta.strip().lower(), sal)
    hoje = date.today().isoformat()

    try:
        cursor.execute("""
            INSERT INTO usuarios
            (nome_usuario, nome_exibicao, senha_hash, sal, pergunta_secreta,
             resposta_secreta_hash, ultima_data_acesso, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome_usuario, nome_exibicao, senha_hash, sal, pergunta_secreta,
              resposta_hash, hoje, hoje))

        usuario_id = cursor.lastrowid

        for categoria in CATEGORIAS:
            cursor.execute("""
                INSERT INTO canteiros (usuario_id, categoria, estagio, saude, vivo)
                VALUES (?, ?, 1, 10, 1)
            """, (usuario_id, categoria))

        conexao.commit()
        return usuario_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conexao.close()


def autenticar_usuario(nome_usuario, senha):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    linha = cursor.fetchone()
    conexao.close()

    if linha is None:
        return None

    if gerar_hash(senha, linha["sal"]) == linha["senha_hash"]:
        return dict(linha)
    return None


def obter_usuario_por_nome(nome_usuario):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    linha = cursor.fetchone()
    conexao.close()
    return dict(linha) if linha else None


def verificar_resposta_secreta(nome_usuario, resposta):
    usuario = obter_usuario_por_nome(nome_usuario)
    if usuario is None:
        return False
    return gerar_hash(resposta.strip().lower(), usuario["sal"]) == usuario["resposta_secreta_hash"]


def redefinir_senha(nome_usuario, nova_senha):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT sal FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    linha = cursor.fetchone()
    if linha is None:
        conexao.close()
        return False

    novo_hash = gerar_hash(nova_senha, linha["sal"])
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE nome_usuario = ?",
                   (novo_hash, nome_usuario))
    conexao.commit()
    conexao.close()
    return True


# ---------- Canteiros ----------

def obter_canteiros(usuario_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM canteiros WHERE usuario_id = ?", (usuario_id,))
    linhas = cursor.fetchall()
    conexao.close()
    return {linha["categoria"]: dict(linha) for linha in linhas}


def atualizar_canteiro(canteiro_id, estagio=None, saude=None, vivo=None):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    campos, valores = [], []
    if estagio is not None:
        campos.append("estagio = ?")
        valores.append(estagio)
    if saude is not None:
        campos.append("saude = ?")
        valores.append(max(0, min(100, saude)))
    if vivo is not None:
        campos.append("vivo = ?")
        valores.append(1 if vivo else 0)

    if campos:
        valores.append(canteiro_id)
        cursor.execute(f"UPDATE canteiros SET {', '.join(campos)} WHERE id = ?", valores)
        conexao.commit()
    conexao.close()


def replantar_canteiro(canteiro_id):
    atualizar_canteiro(canteiro_id, estagio=1, saude=10, vivo=1)


# ---------- Tarefas ----------

def criar_tarefa(usuario_id, categoria, titulo, tipo_habito=None, prioridade=None, prazo=None):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    agora = date.today().isoformat()
    cursor.execute("""
        INSERT INTO tarefas (usuario_id, categoria, titulo, tipo_habito, prioridade, prazo, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (usuario_id, categoria, titulo, tipo_habito, prioridade, prazo, agora))
    conexao.commit()
    tarefa_id = cursor.lastrowid
    conexao.close()
    return tarefa_id


def obter_tarefa_por_id(tarefa_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,))
    linha = cursor.fetchone()
    conexao.close()
    return dict(linha) if linha else None


def atualizar_contador_clique_habito(tarefa_id, bom, novo_valor, data):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    coluna = "cliques_bom_hoje" if bom else "cliques_ruim_hoje"
    cursor.execute(f"""
        UPDATE tarefas SET {coluna} = ?, data_cliques_habito = ?
        WHERE id = ?
    """, (novo_valor, data, tarefa_id))
    conexao.commit()
    conexao.close()


def listar_tarefas(usuario_id, categoria=None):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    if categoria:
        cursor.execute("SELECT * FROM tarefas WHERE usuario_id = ? AND categoria = ? ORDER BY id",
                       (usuario_id, categoria))
    else:
        cursor.execute("SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY categoria, id", (usuario_id,))
    linhas = [dict(linha) for linha in cursor.fetchall()]
    conexao.close()
    return linhas


def editar_tarefa(tarefa_id, **campos):
    if not campos:
        return
    conexao = obter_conexao()
    cursor = conexao.cursor()
    partes = [f"{chave} = ?" for chave in campos]
    valores = list(campos.values()) + [tarefa_id]
    cursor.execute(f"UPDATE tarefas SET {', '.join(partes)} WHERE id = ?", valores)
    conexao.commit()
    conexao.close()


def excluir_tarefa(tarefa_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
    conexao.commit()
    conexao.close()


def marcar_conclusao(tarefa_id, concluida=True):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    hoje = date.today().isoformat()
    cursor.execute("""
        UPDATE tarefas SET concluida = ?, ultima_conclusao = ?
        WHERE id = ?
    """, (1 if concluida else 0, hoje if concluida else None, tarefa_id))
    conexao.commit()
    conexao.close()


# ---------- Histórico / Estatísticas ----------

def registrar_conclusao_no_historico(usuario_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    hoje = date.today().isoformat()
    cursor.execute("""
        INSERT INTO historico (usuario_id, data, tarefas_concluidas)
        VALUES (?, ?, 1)
        ON CONFLICT(usuario_id, data)
        DO UPDATE SET tarefas_concluidas = tarefas_concluidas + 1
    """, (usuario_id, hoje))
    conexao.commit()
    conexao.close()


def desregistrar_conclusao_no_historico(usuario_id):
    """Reverte um registro de conclusão do dia (usado quando o usuário desmarca uma tarefa)."""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    hoje = date.today().isoformat()
    cursor.execute("""
        UPDATE historico SET tarefas_concluidas = MAX(0, tarefas_concluidas - 1)
        WHERE usuario_id = ? AND data = ?
    """, (usuario_id, hoje))
    conexao.commit()
    conexao.close()


def obter_historico(usuario_id, dias=30):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT data, tarefas_concluidas FROM historico
        WHERE usuario_id = ? ORDER BY data DESC LIMIT ?
    """, (usuario_id, dias))
    linhas = [dict(linha) for linha in cursor.fetchall()]
    conexao.close()
    return linhas


def calcular_streak(usuario_id):
    historico = obter_historico(usuario_id, dias=365)
    if not historico:
        return 0

    datas_com_conclusao = {registro["data"] for registro in historico if registro["tarefas_concluidas"] > 0}
    streak = 0
    dia_atual = date.today()

    while dia_atual.isoformat() in datas_com_conclusao:
        streak += 1
        dia_atual = date.fromordinal(dia_atual.toordinal() - 1)

    return streak


def atualizar_ultimo_acesso(usuario_id, nova_data):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("UPDATE usuarios SET ultima_data_acesso = ? WHERE id = ?", (nova_data, usuario_id))
    conexao.commit()
    conexao.close()


def atualizar_sementes(usuario_id, delta):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("UPDATE usuarios SET sementes = MAX(0, sementes + ?) WHERE id = ?", (delta, usuario_id))
    conexao.commit()
    conexao.close()


def atualizar_xp(usuario_id, delta):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("UPDATE usuarios SET xp_total = MAX(0, xp_total + ?) WHERE id = ?", (delta, usuario_id))
    conexao.commit()
    conexao.close()


def obter_conquistas_desbloqueadas(usuario_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT conquista_id FROM conquistas_desbloqueadas WHERE usuario_id = ?", (usuario_id,))
    resultado = {linha["conquista_id"] for linha in cursor.fetchall()}
    conexao.close()
    return resultado


def desbloquear_conquista(usuario_id, conquista_id, data):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO conquistas_desbloqueadas (usuario_id, conquista_id, data_desbloqueio)
            VALUES (?, ?, ?)
        """, (usuario_id, conquista_id, data))
        conexao.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexao.close()


def somar_total_historico(usuario_id):
    """Soma todas as conclusões já registradas no histórico (proxy de 'total de tarefas concluídas na vida')."""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT COALESCE(SUM(tarefas_concluidas), 0) AS total FROM historico WHERE usuario_id = ?",
                   (usuario_id,))
    total = cursor.fetchone()["total"]
    conexao.close()
    return total


def atualizar_dificuldade(usuario_id, dificuldade):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("UPDATE usuarios SET dificuldade = ? WHERE id = ?", (dificuldade, usuario_id))
    conexao.commit()
    conexao.close()


# ---------- Loja ----------

def obter_itens_comprados(usuario_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT item_id, categoria_equipada FROM itens_comprados WHERE usuario_id = ?", (usuario_id,))
    linhas = cursor.fetchall()
    conexao.close()
    return {linha["item_id"]: linha["categoria_equipada"] for linha in linhas}


def comprar_item(usuario_id, item_id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO itens_comprados (usuario_id, item_id) VALUES (?, ?)",
                       (usuario_id, item_id))
        conexao.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexao.close()


def equipar_item(usuario_id, item_id, categoria):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    # Desequipa qualquer outro item na mesma categoria
    cursor.execute("""
        UPDATE itens_comprados SET categoria_equipada = NULL
        WHERE usuario_id = ? AND categoria_equipada = ?
    """, (usuario_id, categoria))
    cursor.execute("""
        UPDATE itens_comprados SET categoria_equipada = ?
        WHERE usuario_id = ? AND item_id = ?
    """, (categoria, usuario_id, item_id))
    conexao.commit()
    conexao.close()