"""
Módulo de lógica do Jardim - Projeto 016
Regras de crescimento, saúde dos canteiros e penalidades por dificuldade.
"""

from datetime import date
import os
import database as db

ESTAGIO_MAXIMO = 4

DANO_HABITO_RUIM = {
    "facil": 5,
    "medio": 10,
    "dificil": 18,
}

GANHO_HABITO_BOM = 8
GANHO_TAREFA_CONCLUIDA = 15
DANO_DIARIA_PERDIDA = {
    "facil": 8,
    "medio": 15,
    "dificil": 25,
}
SEMENTES_POR_TAREFA = 3
CUSTO_REPLANTIO = 15

CATALOGO_LOJA = [
    # --- Espécies de Hábitos ---
    {"id": "lavanda", "nome": "Lavanda", "preco": 20, "categoria": "habitos",
     "arquivo": os.path.join("loja", "especie_lavanda.png")},
    {"id": "violeta", "nome": "Violeta", "preco": 25, "categoria": "habitos",
     "arquivo": os.path.join("loja", "especie_violeta.png")},
    {"id": "orquidea", "nome": "Orquídea", "preco": 40, "categoria": "habitos",
     "arquivo": os.path.join("loja", "especie_orquidea.png")},

    # --- Espécies de Diárias ---
    {"id": "girassol", "nome": "Girassol", "preco": 20, "categoria": "diarias",
     "arquivo": os.path.join("loja", "especie_girassol.png")},
    {"id": "margarida", "nome": "Margarida", "preco": 25, "categoria": "diarias",
     "arquivo": os.path.join("loja", "especie_margarida.png")},
    {"id": "dente_leao", "nome": "Dente-de-leão", "preco": 40, "categoria": "diarias",
     "arquivo": os.path.join("loja", "especie_dente_leao.png")},

    # --- Espécies de Afazeres ---
    {"id": "papoula", "nome": "Papoula", "preco": 20, "categoria": "afazeres",
     "arquivo": os.path.join("loja", "especie_papoula.png")},
    {"id": "tulipa", "nome": "Tulipa", "preco": 25, "categoria": "afazeres",
     "arquivo": os.path.join("loja", "especie_tulipa.png")},
    {"id": "rosa", "nome": "Rosa", "preco": 40, "categoria": "afazeres",
     "arquivo": os.path.join("loja", "especie_rosa.png")},

    # --- Decorações do cenário (sem categoria, ficam no jardim geral) ---
    {"id": "arbusto_ornamental", "nome": "Arbusto Ornamental", "preco": 30, "categoria": None,
     "arquivo": os.path.join("loja", "especie_arbusto_ornamental.png")},
    {"id": "pinheiro_mini", "nome": "Pinheiro Mini", "preco": 30, "categoria": None,
     "arquivo": os.path.join("loja", "especie_pinheiro_mini.png")},
    {"id": "vaso_decorativo", "nome": "Vaso Decorativo", "preco": 15, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_vaso.png")},
    {"id": "cogumelo", "nome": "Cogumelos", "preco": 18, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_cogumelo.png")},
    {"id": "arvore_pequena", "nome": "Árvore Pequena", "preco": 45, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_arvore_pequena.png")},
    {"id": "palmeira", "nome": "Palmeira", "preco": 45, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_palmeira.png")},
    {"id": "arbusto_grande", "nome": "Arbusto Grande", "preco": 28, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_arbusto_grande.png")},
    {"id": "pinheiro_redondo", "nome": "Pinheiro Redondo", "preco": 32, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_pinheiro_redondo.png")},
    {"id": "pedra", "nome": "Pedra de Jardim", "preco": 10, "categoria": None,
     "arquivo": os.path.join("loja", "decoracao_pedra.png")},
]


def obter_item_catalogo(item_id):
    for item in CATALOGO_LOJA:
        if item["id"] == item_id:
            return item
    return None


def comprar_item_loja(usuario, item_id):
    item = obter_item_catalogo(item_id)
    if item is None:
        return False, "Item não encontrado."
    if usuario["sementes"] < item["preco"]:
        return False, "Sementes insuficientes."

    sucesso = db.comprar_item(usuario["id"], item_id)
    if not sucesso:
        return False, "Você já possui esse item."

    db.atualizar_sementes(usuario["id"], -item["preco"])
    return True, "Item comprado!"


def estagio_por_saude(saude):
    """Calcula o estágio visual (0-4) diretamente a partir da saúde atual."""
    if saude <= 0:
        return 0
    limiar_por_estagio = 100 / ESTAGIO_MAXIMO
    return min(ESTAGIO_MAXIMO, int(saude // limiar_por_estagio) + 1)


def ajustar_saude(canteiro, delta):
    """
    Ajusta a saúde do canteiro por 'delta' (positivo ou negativo) e recalcula
    o estágio a partir do novo valor. Mata a planta se a saúde chegar a 0.
    Retorna (nova_saude, novo_estagio, morreu).
    """
    nova_saude = max(0, min(100, canteiro["saude"] + delta))
    morreu = nova_saude <= 0

    if morreu:
        db.atualizar_canteiro(canteiro["id"], estagio=0, saude=0, vivo=0)
        return 0, 0, True

    novo_estagio = estagio_por_saude(nova_saude)
    db.atualizar_canteiro(canteiro["id"], estagio=novo_estagio, saude=nova_saude, vivo=1)
    return nova_saude, novo_estagio, False


def aplicar_ganho_saude(canteiro, quantidade):
    """Aumenta a saúde do canteiro e evolui o estágio se atingir o limiar."""
    nova_saude, novo_estagio, _ = ajustar_saude(canteiro, quantidade)
    return nova_saude, novo_estagio


def aplicar_dano_saude(canteiro, quantidade):
    """Reduz a saúde do canteiro; mata a planta se chegar a zero."""
    nova_saude, novo_estagio, morreu = ajustar_saude(canteiro, -quantidade)
    return nova_saude, novo_estagio, morreu


def completar_tarefa(usuario, tarefa, canteiro):
    """Processa a conclusão de uma tarefa: rega o canteiro, dá sementes/XP, atualiza histórico."""
    db.marcar_conclusao(tarefa["id"], concluida=True)
    ajustar_saude(canteiro, GANHO_TAREFA_CONCLUIDA)
    db.atualizar_sementes(usuario["id"], SEMENTES_POR_TAREFA)
    db.atualizar_xp(usuario["id"], XP_POR_TAREFA)
    db.registrar_conclusao_no_historico(usuario["id"])


def desfazer_tarefa(usuario, tarefa, canteiro):
    """
    Reverte a conclusão de uma tarefa (usuário desmarcou a caixa de novo).
    Devolve exatamente o que 'completar_tarefa' concedeu, pra impedir que
    marcar/desmarcar repetidamente gere sementes ou saúde de graça.
    """
    db.marcar_conclusao(tarefa["id"], concluida=False)
    ajustar_saude(canteiro, -GANHO_TAREFA_CONCLUIDA)
    db.atualizar_sementes(usuario["id"], -SEMENTES_POR_TAREFA)
    db.atualizar_xp(usuario["id"], -XP_POR_TAREFA)
    db.desregistrar_conclusao_no_historico(usuario["id"])


MAX_CLIQUES_RECOMPENSADOS_POR_DIA = 5

XP_POR_TAREFA = 8
XP_POR_HABITO_BOM = 5
XP_POR_NIVEL = 60

NOMES_NIVEL = [
    (1, "Semeador Iniciante"),
    (5, "Jardineiro Aprendiz"),
    (10, "Jardineiro Dedicado"),
    (20, "Jardineiro Experiente"),
    (35, "Mestre Jardineiro"),
    (50, "Lenda do Jardim"),
]


def calcular_nivel(xp_total):
    """Retorna (nivel, xp_no_nivel_atual, xp_necessario_pro_proximo, titulo)."""
    nivel = xp_total // XP_POR_NIVEL + 1
    xp_no_nivel = xp_total % XP_POR_NIVEL

    titulo = NOMES_NIVEL[0][1]
    for limite, nome in NOMES_NIVEL:
        if nivel >= limite:
            titulo = nome

    return nivel, xp_no_nivel, XP_POR_NIVEL, titulo


CATALOGO_CONQUISTAS = [
    {"id": "primeiro_passo", "nome": "Primeiro Passo", "descricao": "Complete sua primeira tarefa.",
     "emoji": "🌱"},
    {"id": "dedicado", "nome": "Dedicado", "descricao": "Complete 10 tarefas no total.",
     "emoji": "📌"},
    {"id": "cem_tarefas", "nome": "Centena", "descricao": "Complete 100 tarefas no total.",
     "emoji": "💯"},
    {"id": "streak_semana", "nome": "Semana Completa", "descricao": "Alcance um streak de 7 dias.",
     "emoji": "🔥"},
    {"id": "flor_habitos", "nome": "Hábito Florido", "descricao": "Deixe o canteiro de Hábitos florescer.",
     "emoji": "🌸"},
    {"id": "flor_diarias", "nome": "Rotina Florida", "descricao": "Deixe o canteiro de Diárias florescer.",
     "emoji": "🌼"},
    {"id": "flor_afazeres", "nome": "Afazer Florido", "descricao": "Deixe o canteiro de Afazeres florescer.",
     "emoji": "🌻"},
    {"id": "jardim_completo", "nome": "Jardim Completo", "descricao": "Tenha os 3 canteiros florescidos ao mesmo tempo.",
     "emoji": "🏡"},
    {"id": "primeira_compra", "nome": "Primeira Compra", "descricao": "Compre seu primeiro item na loja.",
     "emoji": "🛒"},
    {"id": "colecionador", "nome": "Colecionador", "descricao": "Possua 5 itens diferentes da loja.",
     "emoji": "🎁"},
    {"id": "resiliente", "nome": "Resiliente", "descricao": "Replante um canteiro que morreu.",
     "emoji": "♻️"},
    {"id": "nivel_5", "nome": "Nível 5", "descricao": "Alcance o nível 5 de jardineiro.",
     "emoji": "⭐"},
]


def verificar_conquistas(usuario):
    """
    Confere todas as condições de conquista contra o estado atual do usuário
    e desbloqueia as que forem atingidas pela primeira vez. Retorna a lista
    das conquistas recém-desbloqueadas nessa checagem (pra mostrar um aviso).
    """
    ja_desbloqueadas = db.obter_conquistas_desbloqueadas(usuario["id"])
    canteiros = db.obter_canteiros(usuario["id"])
    itens_comprados = db.obter_itens_comprados(usuario["id"])
    total_historico = db.somar_total_historico(usuario["id"])
    streak = db.calcular_streak(usuario["id"])
    nivel, _, _, _ = calcular_nivel(usuario["xp_total"])

    condicoes = {
        "primeiro_passo": total_historico >= 1,
        "dedicado": total_historico >= 10,
        "cem_tarefas": total_historico >= 100,
        "streak_semana": streak >= 7,
        "flor_habitos": canteiros["habitos"]["estagio"] == ESTAGIO_MAXIMO,
        "flor_diarias": canteiros["diarias"]["estagio"] == ESTAGIO_MAXIMO,
        "flor_afazeres": canteiros["afazeres"]["estagio"] == ESTAGIO_MAXIMO,
        "jardim_completo": all(c["estagio"] == ESTAGIO_MAXIMO for c in canteiros.values()),
        "primeira_compra": len(itens_comprados) >= 1,
        "colecionador": len(itens_comprados) >= 5,
        "nivel_5": nivel >= 5,
    }

    hoje = date.today().isoformat()
    novas = []
    for conquista_id, atingida in condicoes.items():
        if atingida and conquista_id not in ja_desbloqueadas:
            sucesso = db.desbloquear_conquista(usuario["id"], conquista_id, hoje)
            if sucesso:
                item_catalogo = next(c for c in CATALOGO_CONQUISTAS if c["id"] == conquista_id)
                novas.append(item_catalogo)

    return novas


def desbloquear_conquista_manual(usuario_id, conquista_id):
    """Usado por eventos pontuais que não são 'estado atual' (ex: replantar após morte)."""
    hoje = date.today().isoformat()
    sucesso = db.desbloquear_conquista(usuario_id, conquista_id, hoje)
    if sucesso:
        return next(c for c in CATALOGO_CONQUISTAS if c["id"] == conquista_id)
    return None


def registrar_habito(usuario, tarefa, canteiro, bom: bool):
    """
    Processa um clique de hábito bom ou ruim. Cada hábito só recompensa
    (dá sementes/saúde, ou tira saúde) até MAX_CLIQUES_RECOMPENSADOS_POR_DIA
    vezes por dia — cliques além disso não fazem nada, pra impedir gerar
    sementes infinitas só de ficar clicando.
    """
    hoje = date.today().isoformat()
    tarefa_atual = db.obter_tarefa_por_id(tarefa["id"])

    dia_mudou = tarefa_atual.get("data_cliques_habito") != hoje
    cliques_bom = 0 if dia_mudou else tarefa_atual.get("cliques_bom_hoje", 0)
    cliques_ruim = 0 if dia_mudou else tarefa_atual.get("cliques_ruim_hoje", 0)

    if bom:
        if cliques_bom >= MAX_CLIQUES_RECOMPENSADOS_POR_DIA:
            db.atualizar_contador_clique_habito(tarefa["id"], True, cliques_bom, hoje)
            return {"morreu": False, "limite_atingido": True}

        aplicar_ganho_saude(canteiro, GANHO_HABITO_BOM)
        db.atualizar_sementes(usuario["id"], 1)
        db.atualizar_xp(usuario["id"], XP_POR_HABITO_BOM)
        db.registrar_conclusao_no_historico(usuario["id"])
        db.atualizar_contador_clique_habito(tarefa["id"], True, cliques_bom + 1, hoje)
        return {"morreu": False, "limite_atingido": False}
    else:
        if cliques_ruim >= MAX_CLIQUES_RECOMPENSADOS_POR_DIA:
            db.atualizar_contador_clique_habito(tarefa["id"], False, cliques_ruim, hoje)
            return {"morreu": False, "limite_atingido": True}

        dificuldade = usuario.get("dificuldade", "medio")
        dano = DANO_HABITO_RUIM.get(dificuldade, DANO_HABITO_RUIM["medio"])
        _, _, morreu = aplicar_dano_saude(canteiro, dano)
        db.atualizar_contador_clique_habito(tarefa["id"], False, cliques_ruim + 1, hoje)
        return {"morreu": morreu, "limite_atingido": False}


def replantar(usuario, canteiro):
    """Gasta sementes para replantar um canteiro morto."""
    if usuario["sementes"] < CUSTO_REPLANTIO:
        return False
    db.atualizar_sementes(usuario["id"], -CUSTO_REPLANTIO)
    db.replantar_canteiro(canteiro["id"])
    desbloquear_conquista_manual(usuario["id"], "resiliente")
    return True


def processar_virada_de_dia(usuario):
    """
    Detecta quantos dias se passaram desde o último acesso e aplica a
    penalidade de Diárias não cumpridas retroativamente para cada dia perdido.
    Retorna a lista de canteiros que murcharam/morreram, para exibir alerta.
    """
    hoje = date.today()
    ultima_data = date.fromisoformat(usuario["ultima_data_acesso"])
    dias_passados = (hoje - ultima_data).days

    alertas = []

    if dias_passados <= 0:
        return alertas

    canteiros = db.obter_canteiros(usuario["id"])
    canteiro_diarias = canteiros.get("diarias")

    if canteiro_diarias and canteiro_diarias["vivo"]:
        tarefas_diarias = db.listar_tarefas(usuario["id"], categoria="diarias")
        dificuldade = usuario.get("dificuldade", "medio")
        dano_por_dia = DANO_DIARIA_PERDIDA.get(dificuldade, DANO_DIARIA_PERDIDA["medio"])

        for _ in range(dias_passados):
            if tarefas_diarias:
                _, _, morreu = aplicar_dano_saude(canteiro_diarias, dano_por_dia)
                canteiro_diarias = db.obter_canteiros(usuario["id"])["diarias"]
                if morreu:
                    alertas.append("O canteiro de Diárias murchou e morreu por abandono!")
                    break

        # Reseta o status "concluída" das diárias para o novo dia
        for tarefa in tarefas_diarias:
            db.marcar_conclusao(tarefa["id"], concluida=False)

    db.atualizar_ultimo_acesso(usuario["id"], hoje.isoformat())

    canteiros_atualizados = db.obter_canteiros(usuario["id"])
    for categoria, canteiro in canteiros_atualizados.items():
        if canteiro["vivo"] and canteiro["saude"] < 30:
            nome_categoria = {"habitos": "Hábitos", "diarias": "Diárias", "afazeres": "Afazeres"}[categoria]
            alertas.append(f"O canteiro de {nome_categoria} está murchando! Cuide dele.")

    return alertas


def nome_arquivo_sprite(categoria, estagio, vivo, item_equipado=None):
    """Resolve qual arquivo de imagem usar para o estado atual do canteiro."""
    if not vivo or estagio == 0:
        return "planta_morta.png"
    if estagio == 1:
        return "estagio1_semente.png"
    if estagio == 2:
        return "estagio2_broto.png"
    if estagio == 3:
        return "estagio3_planta.png"

    # Estágio 4 (floração): usa espécie comprada na loja, se equipada
    if item_equipado:
        item = obter_item_catalogo(item_equipado)
        if item:
            return item["arquivo"]

    return f"estagio4_flor_{categoria}.png"