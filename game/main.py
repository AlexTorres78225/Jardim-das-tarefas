"""
Jardim das Tarefas - Projeto 016
Aplicativo de lista de tarefas gamificado, tema jardim, inspirado no Habitica.
Ponto de entrada principal.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import random

try:
    import winsound

    SOM_DISPONIVEL = True
except ImportError:
    SOM_DISPONIVEL = False

from PIL import Image, ImageTk

import database as db
import jardim

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _localizar_pasta_assets():
    """
    Acha a pasta 'assets' mesmo que main.py tenha sido movido pra dentro
    de uma subpasta (ex: 'game/'). Procura primeiro do lado do próprio
    arquivo, depois vai subindo até 3 níveis de pasta.
    """
    candidato = BASE_DIR
    for _ in range(4):
        caminho_assets = os.path.join(candidato, "assets")
        if os.path.isdir(caminho_assets):
            return caminho_assets
        candidato = os.path.dirname(candidato)
    # Não achou em nenhum nível — usa o padrão mesmo (vai falhar com aviso claro depois)
    return os.path.join(BASE_DIR, "assets")


PASTA_ASSETS = _localizar_pasta_assets()
PASTA_PLANTAS = os.path.join(PASTA_ASSETS, "plantas")
PASTA_ICONES = os.path.join(PASTA_ASSETS, "icones")
PASTA_FUNDOS = os.path.join(PASTA_ASSETS, "fundos")
PASTA_SONS = os.path.join(PASTA_ASSETS, "sons")

NOMES_CATEGORIA = {"habitos": "Hábitos", "diarias": "Diárias", "afazeres": "Afazeres"}
COR_FUNDO = "#eef7ee"
COR_DESTAQUE = "#4a7c4e"


class AplicativoJardim(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jardim das Tarefas")
        self.geometry("960x640")
        self.configure(bg=COR_FUNDO)
        self.minsize(800, 560)

        self.usuario_atual = None
        self.cache_imagens = {}
        self.rotulos_plantas = {}

        self.container = tk.Frame(self, bg=COR_FUNDO)
        self.container.pack(fill="both", expand=True)

        self.mostrar_tela_login()

    # ---------- Utilidades ----------

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.unbind_all("<MouseWheel>")

    def carregar_imagem(self, nome_arquivo, tamanho=(96, 96)):
        chave = (nome_arquivo, tamanho)
        if chave in self.cache_imagens:
            return self.cache_imagens[chave]

        caminho = os.path.join(PASTA_PLANTAS, nome_arquivo)
        try:
            imagem = Image.open(caminho).convert("RGBA")
            imagem.thumbnail(tamanho)
            foto = ImageTk.PhotoImage(imagem)
            self.cache_imagens[chave] = foto
            return foto
        except FileNotFoundError:
            return None

    def carregar_icone(self, nome_arquivo, tamanho=(20, 20)):
        chave = ("icone", nome_arquivo, tamanho)
        if chave in self.cache_imagens:
            return self.cache_imagens[chave]

        caminho = os.path.join(PASTA_ICONES, nome_arquivo)
        try:
            imagem = Image.open(caminho).convert("RGBA")
            imagem.thumbnail(tamanho)
            foto = ImageTk.PhotoImage(imagem)
            self.cache_imagens[chave] = foto
            return foto
        except FileNotFoundError:
            return None

    def tocar_som(self, nome_arquivo):
        """Toca um efeito sonoro curto, sem travar a interface. Falha em silêncio se não for Windows."""
        if not SOM_DISPONIVEL:
            return
        caminho = os.path.join(PASTA_SONS, nome_arquivo)
        try:
            winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

    def _aplicar_fundo_texturizado(self):
        """Coloca a textura de grama como fundo do container, esticada pro tamanho da janela."""
        chave = "fundo_textura"
        try:
            caminho = os.path.join(PASTA_FUNDOS, "textura_grama.png")
            imagem = Image.open(caminho).convert("RGBA")
            largura = max(self.winfo_width(), 960)
            altura = max(self.winfo_height(), 640)
            imagem = imagem.resize((largura, altura))
            foto = ImageTk.PhotoImage(imagem)
            self.cache_imagens[chave] = foto

            fundo = tk.Label(self.container, image=foto, bg=COR_FUNDO)
            fundo.image = foto
            fundo.place(x=0, y=0, relwidth=1, relheight=1)
            fundo.lower()
        except FileNotFoundError:
            pass

    # ---------- Easter eggs ----------

    FRASES_TITULO = [
        "🌻 Continue regando seus sonhos!",
        "🐛 Ops, uma lagarta passou por aqui...",
        "🍃 O vento sussurra: organize-se!",
        "🌦️ Previsão do tempo: 100% de produtividade",
        "🐝 Zzzzz... uma abelha poliniza suas tarefas",
        "🌈 Você encontrou o canto secreto do jardim!",
    ]

    FRASES_PLANTA = {
        "habitos": ["Continue assim! 💪", "Eu acredito em você!", "Um hábito de cada vez 🌱"],
        "diarias": ["Todo dia conta!", "Rotina é liberdade 🌤️", "Já regou hoje?"],
        "afazeres": ["Vamos riscar essa lista!", "Falta pouco!", "Você consegue! 🌸"],
    }

    def _clicar_titulo(self, rotulo_titulo):
        self.contador_cliques_titulo += 1
        if self.contador_cliques_titulo % 5 == 0:
            frase = random.choice(self.FRASES_TITULO)
            texto_original = rotulo_titulo.cget("text")
            rotulo_titulo.config(text=frase, fg="#e07a2b")
            self.tocar_som("clique.wav")
            self.after(1400, lambda: rotulo_titulo.config(text=texto_original, fg=COR_DESTAQUE)
            if rotulo_titulo.winfo_exists() else None)

    def _clicar_planta(self, categoria, rotulo_planta):
        frase = random.choice(self.FRASES_PLANTA.get(categoria, ["🌿"]))

        balao = tk.Label(rotulo_planta.master, text=frase, bg="#fff9e6", fg="#5c4a1a",
                         font=("Segoe UI", 9, "italic"), relief="solid", bd=1, padx=8, pady=3)
        balao.place(relx=0.5, rely=0.02, anchor="n")
        self.after(1500, lambda: balao.destroy() if balao.winfo_exists() else None)

        self.tocar_som("clique.wav")
        self._animar_crescimento(categoria)

    # ---------- Tela de Login ----------

    def mostrar_tela_login(self):
        self.limpar_tela()
        self._aplicar_fundo_texturizado()

        painel = tk.Frame(self.container, bg=COR_FUNDO)
        painel.place(relx=0.5, rely=0.5, anchor="center")

        self.contador_cliques_titulo = 0
        titulo = tk.Label(painel, text="🌱 Jardim das Tarefas", font=("Segoe UI", 26, "bold"),
                          bg=COR_FUNDO, fg=COR_DESTAQUE, cursor="hand2")
        titulo.pack(pady=(0, 20))
        titulo.bind("<Button-1>", lambda e: self._clicar_titulo(titulo))

        campo_usuario = self._criar_campo(painel, "Usuário")
        campo_senha = self._criar_campo(painel, "Senha", oculto=True)

        def entrar():
            nome_digitado = campo_usuario.get().strip()
            senha_digitada = campo_senha.get()

            # Conta de desenvolvedor: cria na hora se ainda não existir, sem precisar de script à parte
            if nome_digitado == "teste123" and senha_digitada == "teste123":
                if db.obter_usuario_por_nome("teste123") is None:
                    novo_id = db.criar_usuario("teste123", "Dev", "teste123",
                                               "qual sua cor favorita?", "azul")
                    if novo_id:
                        db.atualizar_sementes(novo_id, 1_000_000)

            usuario = db.autenticar_usuario(nome_digitado, senha_digitada)
            if usuario is None:
                messagebox.showerror("Erro", "Usuário ou senha incorretos.")
                return
            self.usuario_atual = usuario
            self.pos_login()

        def esqueci_senha():
            self.mostrar_tela_recuperacao()

        tk.Button(painel, text="Entrar", command=entrar, bg=COR_DESTAQUE, fg="white",
                  font=("Segoe UI", 12, "bold"), width=20, relief="flat").pack(pady=(15, 5))
        tk.Button(painel, text="Criar Conta", command=self.mostrar_tela_cadastro,
                  font=("Segoe UI", 10), relief="flat", bg=COR_FUNDO, fg=COR_DESTAQUE).pack()
        tk.Button(painel, text="Esqueci minha senha", command=esqueci_senha,
                  font=("Segoe UI", 9), relief="flat", bg=COR_FUNDO, fg="#888").pack(pady=(5, 0))
        tk.Button(painel, text="📖 Como funciona esse jardim?", command=self.mostrar_manual,
                  font=("Segoe UI", 9, "underline"), relief="flat", bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(15, 0))

    def _criar_campo(self, painel, rotulo, oculto=False):
        tk.Label(painel, text=rotulo, bg=COR_FUNDO, font=("Segoe UI", 10)).pack(anchor="w")
        entrada = tk.Entry(painel, show="*" if oculto else "", font=("Segoe UI", 12), width=28)
        entrada.pack(pady=(0, 10))
        return entrada

    # ---------- Tela de Cadastro ----------

    def mostrar_tela_cadastro(self):
        self.limpar_tela()
        painel = tk.Frame(self.container, bg=COR_FUNDO)
        painel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(painel, text="Criar Conta", font=("Segoe UI", 20, "bold"),
                 bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(0, 15))

        campo_nome = self._criar_campo(painel, "Nome de exibição")
        campo_usuario = self._criar_campo(painel, "Usuário")
        campo_senha = self._criar_campo(painel, "Senha", oculto=True)
        campo_pergunta = self._criar_campo(painel, "Pergunta secreta (ex: nome do seu pet)")
        campo_resposta = self._criar_campo(painel, "Resposta secreta")

        def cadastrar():
            if not all([campo_nome.get(), campo_usuario.get(), campo_senha.get(),
                        campo_pergunta.get(), campo_resposta.get()]):
                messagebox.showwarning("Atenção", "Preencha todos os campos.")
                return

            resultado = db.criar_usuario(
                campo_usuario.get().strip(), campo_nome.get().strip(),
                campo_senha.get(), campo_pergunta.get().strip(), campo_resposta.get().strip()
            )
            if resultado is None:
                messagebox.showerror("Erro", "Esse nome de usuário já existe.")
                return

            messagebox.showinfo("Sucesso", "Conta criada! Faça login para começar a cuidar do seu jardim.")
            self.mostrar_tela_login()

        tk.Button(painel, text="Criar Conta", command=cadastrar, bg=COR_DESTAQUE, fg="white",
                  font=("Segoe UI", 12, "bold"), width=24, relief="flat").pack(pady=(10, 5))
        tk.Button(painel, text="Voltar", command=self.mostrar_tela_login,
                  font=("Segoe UI", 10), relief="flat", bg=COR_FUNDO, fg="#888").pack()

    # ---------- Recuperação de senha ----------

    def mostrar_tela_recuperacao(self):
        self.limpar_tela()
        painel = tk.Frame(self.container, bg=COR_FUNDO)
        painel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(painel, text="Recuperar Senha", font=("Segoe UI", 20, "bold"),
                 bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(0, 15))

        campo_usuario = self._criar_campo(painel, "Usuário")
        rotulo_pergunta = tk.Label(painel, text="", bg=COR_FUNDO, font=("Segoe UI", 10, "italic"))
        rotulo_pergunta.pack(pady=(0, 5))
        campo_resposta = self._criar_campo(painel, "Sua resposta")
        campo_nova_senha = self._criar_campo(painel, "Nova senha", oculto=True)

        def buscar_pergunta():
            usuario = db.obter_usuario_por_nome(campo_usuario.get().strip())
            if usuario is None:
                messagebox.showerror("Erro", "Usuário não encontrado.")
                return
            rotulo_pergunta.config(text=usuario["pergunta_secreta"])

        def redefinir():
            nome = campo_usuario.get().strip()
            if not db.verificar_resposta_secreta(nome, campo_resposta.get().strip()):
                messagebox.showerror("Erro", "Resposta incorreta.")
                return
            db.redefinir_senha(nome, campo_nova_senha.get())
            messagebox.showinfo("Sucesso", "Senha redefinida! Faça login.")
            self.mostrar_tela_login()

        tk.Button(painel, text="Buscar pergunta secreta", command=buscar_pergunta,
                  bg="#ddd", relief="flat").pack(pady=(0, 10))
        tk.Button(painel, text="Redefinir Senha", command=redefinir, bg=COR_DESTAQUE, fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat").pack(pady=(5, 5))
        tk.Button(painel, text="Voltar", command=self.mostrar_tela_login,
                  font=("Segoe UI", 10), relief="flat", bg=COR_FUNDO, fg="#888").pack()

    # ---------- Pós-login ----------

    def pos_login(self):
        alertas = jardim.processar_virada_de_dia(self.usuario_atual)
        self.usuario_atual = db.obter_usuario_por_nome(self.usuario_atual["nome_usuario"])
        self.mostrar_dashboard()
        self._verificar_e_avisar_conquistas()

        if alertas:
            self.after(300, lambda: messagebox.showwarning(
                "Alerta do Jardim", "\n".join(alertas)))

    # ---------- Dashboard ----------

    ALTURA_CENARIO = 170
    ALTURA_CEU = 90

    def _montar_faixa_ceu(self):
        """
        Cenário decorativo entre o cabeçalho e os canteiros, desenhado num Canvas
        (evita qualquer problema de fundo colado atrás das imagens). Tem céu com
        sol/nuvens, cerca real, faixa de terra com decorações compradas "plantadas",
        e um regador arrastável (puramente cosmético) que solta uma gota ao molhar a terra.
        """
        largura = max(self.winfo_width(), 960)

        canvas = tk.Canvas(self.container, height=self.ALTURA_CENARIO,
                           bg="#cfeaf5", highlightthickness=0)
        canvas.pack(fill="x")
        self.canvas_jardim = canvas

        # Céu e terra como retângulos de fundo
        id_ceu = canvas.create_rectangle(0, 0, largura, self.ALTURA_CEU, fill="#cfeaf5", outline="")
        id_terra_fundo = canvas.create_rectangle(0, self.ALTURA_CEU, largura, self.ALTURA_CENARIO,
                                                 fill="#b3854c", outline="")

        sol = self.carregar_icone("sol.png", (40, 40))
        if sol:
            canvas.create_image(30, 8, image=sol, anchor="nw")
            canvas.imagem_sol = sol

        nuvem = self.carregar_icone("nuvem.png", (60, 38))
        if nuvem:
            canvas.imagens_nuvem = []
            for pos_x in (150, 450, 750):
                canvas.create_image(pos_x, 14, image=nuvem, anchor="nw")
                canvas.imagens_nuvem.append(nuvem)

        icone_cerca = self.carregar_icone("cerca.png", (58, 58))
        if icone_cerca:
            canvas.imagens_cerca = []
            for pos_x in range(0, largura, 55):
                canvas.create_image(pos_x, self.ALTURA_CEU - 18, image=icone_cerca, anchor="nw")
                canvas.imagens_cerca.append(icone_cerca)

        # Todos os itens comprados (flores e decorações) aparecem "plantados" na terra,
        # alinhados pela base (parecem estar de pé no chão) e quebrando linha se precisar
        itens_comprados = db.obter_itens_comprados(self.usuario_atual["id"])
        itens_possuidos = [item for item in jardim.CATALOGO_LOJA if item["id"] in itens_comprados]

        TAMANHO_ITEM = 42
        ESPACO_ITEM = 8
        PASSO_X = TAMANHO_ITEM + ESPACO_ITEM
        BASE_Y = self.ALTURA_CENARIO - 8  # linha do "chão" onde a base da imagem encosta
        ALTURA_LINHA = TAMANHO_ITEM + 4

        itens_por_linha = max(1, (largura - 20) // PASSO_X)

        canvas.imagens_decor = []
        for indice, item in enumerate(itens_possuidos):
            imagem_decor = self.carregar_imagem(item["arquivo"], tamanho=(TAMANHO_ITEM, TAMANHO_ITEM))
            if not imagem_decor:
                continue
            linha_indice = indice // itens_por_linha
            coluna_indice = indice % itens_por_linha
            pos_x = 20 + coluna_indice * PASSO_X
            pos_y = BASE_Y - linha_indice * ALTURA_LINHA
            canvas.create_image(pos_x, pos_y, image=imagem_decor, anchor="sw")
            canvas.imagens_decor.append(imagem_decor)

        # Regador arrastável (decorativo — nunca sai dos limites do cenário)
        icone_regador = self.carregar_icone("regador.png", (58, 46))
        if icone_regador:
            canvas.imagem_regador = icone_regador
            id_regador = canvas.create_image(largura - 80, 15, image=icone_regador, anchor="nw", tags="regador")
            self._tornar_arrastavel(canvas, id_regador, largura)

        def redimensionar(evento):
            nova_largura = evento.width
            canvas.coords(id_ceu, 0, 0, nova_largura, self.ALTURA_CEU)
            canvas.coords(id_terra_fundo, 0, self.ALTURA_CEU, nova_largura, self.ALTURA_CENARIO)
            canvas.tag_lower(id_ceu)
            canvas.tag_lower(id_terra_fundo)

        canvas.bind("<Configure>", redimensionar)

    def _tornar_arrastavel(self, canvas, id_regador, largura_cenario_inicial):
        """Permite arrastar o regador dentro dos limites do cenário; solta gota ao molhar a terra."""
        LARGURA_REGADOR, ALTURA_REGADOR = 58, 46
        canvas.tag_bind(id_regador, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(id_regador, "<Leave>", lambda e: canvas.config(cursor=""))

        def iniciar(evento):
            canvas.dados_arrasto = {"x": evento.x, "y": evento.y}

        def arrastar(evento):
            dados = getattr(canvas, "dados_arrasto", None)
            if not dados:
                return
            dx = evento.x - dados["x"]
            dy = evento.y - dados["y"]

            largura_atual = canvas.winfo_width()
            x1, y1, x2, y2 = canvas.bbox(id_regador)
            novo_x1 = max(0, min(largura_atual - LARGURA_REGADOR, x1 + dx))
            novo_y1 = max(0, min(self.ALTURA_CENARIO - ALTURA_REGADOR, y1 + dy))

            canvas.coords(id_regador, novo_x1, novo_y1)
            canvas.tag_raise(id_regador)
            canvas.dados_arrasto = {"x": evento.x, "y": evento.y}

            self._checar_regada(canvas, id_regador)

        canvas.tag_bind(id_regador, "<Button-1>", iniciar)
        canvas.tag_bind(id_regador, "<B1-Motion>", arrastar)

    def _checar_regada(self, canvas, id_regador):
        """Se o regador estiver tocando a terra, mostra uma gota d'água piscando por perto."""
        x1, y1, x2, y2 = canvas.bbox(id_regador)
        if y2 < self.ALTURA_CEU + 10:
            return  # bico do regador ainda não encostou na terra

        if getattr(self, "_gota_ativa", False):
            return

        self._gota_ativa = True
        gota_img = self.carregar_icone("gota.png", (20, 24))
        if gota_img:
            canvas.imagem_gota_atual = gota_img
            id_gota = canvas.create_image(x2 - 15, y2 - 6, image=gota_img, anchor="nw")

            def remover_gota():
                if id_gota in canvas.find_all():
                    canvas.delete(id_gota)
                self._gota_ativa = False

            self.after(400, remover_gota)
        else:
            self._gota_ativa = False

    def mostrar_dashboard(self):
        self.limpar_tela()
        self._aplicar_fundo_texturizado()

        topo = tk.Frame(self.container, bg=COR_DESTAQUE, height=88)
        topo.pack(fill="x")
        topo.pack_propagate(False)

        linha1 = tk.Frame(topo, bg=COR_DESTAQUE)
        linha1.pack(fill="x", pady=(8, 0))

        tk.Label(linha1, text=f"🌻 Olá, {self.usuario_atual['nome_exibicao']}!",
                 font=("Segoe UI", 14, "bold"), bg=COR_DESTAQUE, fg="white").pack(side="left", padx=20)

        tk.Button(linha1, text="Sair", command=self.mostrar_tela_login,
                  bg="#3a5f3d", fg="white", relief="flat").pack(side="right", padx=20)

        icone_carrinho = self.carregar_icone("carrinho_branco.png", (18, 18))
        btn_loja = tk.Button(linha1, image=icone_carrinho, text=" Loja", compound="left", command=self.mostrar_loja,
                             bg="#3a5f3d", fg="white", relief="flat", padx=8)
        btn_loja.image = icone_carrinho
        btn_loja.pack(side="right", padx=5)

        icone_engrenagem = self.carregar_icone("engrenagem_branca.png", (18, 18))
        btn_config = tk.Button(linha1, image=icone_engrenagem, text=" Config", compound="left",
                               command=self.mostrar_configuracoes, bg="#3a5f3d", fg="white", relief="flat", padx=8)
        btn_config.image = icone_engrenagem
        btn_config.pack(side="right", padx=5)

        tk.Button(linha1, text="📖 Manual", command=self.mostrar_manual,
                  bg="#3a5f3d", fg="white", relief="flat").pack(side="right", padx=5)

        icone_estrela = self.carregar_icone("estrela_dourada.png", (18, 18))
        btn_conquistas = tk.Button(linha1, image=icone_estrela, text=" Conquistas", compound="left",
                                   command=self.mostrar_conquistas, bg="#3a5f3d", fg="white", relief="flat", padx=8)
        btn_conquistas.image = icone_estrela
        btn_conquistas.pack(side="right", padx=5)

        streak = db.calcular_streak(self.usuario_atual["id"])
        nivel, xp_no_nivel, xp_para_prox, titulo = jardim.calcular_nivel(self.usuario_atual["xp_total"])

        linha2 = tk.Frame(topo, bg=COR_DESTAQUE)
        linha2.pack(fill="x", pady=(2, 0))
        tk.Label(linha2, text=f"🔥 Streak: {streak} dias    🌰 Sementes: {self.usuario_atual['sementes']}"
                              f"    ⭐ Nível {nivel} — {titulo}",
                 font=("Segoe UI", 10), bg=COR_DESTAQUE, fg="white").pack(side="left", padx=20)

        # Barrinha de progresso de XP até o próximo nível
        barra_fundo = tk.Frame(topo, bg="#3a5f3d", height=6)
        barra_fundo.pack(fill="x", padx=20, pady=(4, 0))
        barra_fundo.pack_propagate(False)
        largura_disponivel = max(self.winfo_width() - 40, 400)
        largura_xp = max(2, int(largura_disponivel * xp_no_nivel / xp_para_prox))
        tk.Frame(barra_fundo, bg="#ffd54f", height=6, width=largura_xp).place(x=0, y=0)

        self._montar_faixa_ceu()

        corpo = tk.Frame(self.container, bg=COR_FUNDO)
        corpo.pack(fill="both", expand=True, padx=15, pady=15)
        corpo.columnconfigure((0, 1, 2), weight=1)
        corpo.rowconfigure(0, weight=1)

        canteiros = db.obter_canteiros(self.usuario_atual["id"])
        for i, categoria in enumerate(("habitos", "diarias", "afazeres")):
            self._montar_painel_canteiro(corpo, categoria, canteiros[categoria], coluna=i)

    def _montar_painel_canteiro(self, painel_pai, categoria, canteiro, coluna):
        moldura = tk.Frame(painel_pai, bg="white", relief="ridge", bd=1)
        moldura.grid(row=0, column=coluna, sticky="nsew", padx=8, pady=8)

        tk.Label(moldura, text=NOMES_CATEGORIA[categoria], font=("Segoe UI", 13, "bold"),
                 bg="white", fg=COR_DESTAQUE).pack(pady=(10, 5))

        itens_equipados = db.obter_itens_comprados(self.usuario_atual["id"])
        item_equipado_aqui = next((item_id for item_id, cat in itens_equipados.items() if cat == categoria), None)

        area_planta = tk.Frame(moldura, bg="white")
        area_planta.pack(pady=(5, 0))

        nome_sprite = jardim.nome_arquivo_sprite(categoria, canteiro["estagio"], canteiro["vivo"], item_equipado_aqui)
        imagem = self.carregar_imagem(nome_sprite, tamanho=(100, 100))
        rotulo_planta = tk.Label(area_planta, image=imagem, bg="white", cursor="hand2")
        rotulo_planta.image = imagem
        rotulo_planta.pack()
        rotulo_planta.bind("<Button-1>", lambda e, cat=categoria, rot=rotulo_planta: self._clicar_planta(cat, rot))
        self.rotulos_plantas[categoria] = rotulo_planta

        # "Vasinho" decorativo: faixa de terra sob a planta
        tk.Frame(area_planta, bg="#a1694a", height=8, width=90).pack(pady=(0, 10))

        cor_saude = "#4caf50" if canteiro["saude"] > 50 else ("#ff9800" if canteiro["saude"] > 20 else "#f44336")

        barra_fundo = tk.Frame(moldura, bg="#e0e0e0", height=14, width=180)
        barra_fundo.pack(pady=(0, 3))
        barra_fundo.pack_propagate(False)
        largura_preenchida = max(2, int(180 * canteiro["saude"] / 100))
        tk.Frame(barra_fundo, bg=cor_saude, height=14, width=largura_preenchida).place(x=0, y=0)

        tk.Label(moldura, text=f"🌡 Saúde: {canteiro['saude']}%", fg=cor_saude,
                 bg="white", font=("Segoe UI", 9, "bold")).pack(pady=(0, 5))

        if not canteiro["vivo"]:
            tk.Button(moldura, text=f"Replantar (-{jardim.CUSTO_REPLANTIO} 🌰)",
                      command=lambda: self._replantar(categoria, canteiro),
                      bg="#8d6e63", fg="white", relief="flat").pack(pady=8)

        lista_frame = tk.Frame(moldura, bg="white")
        lista_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        tarefas = db.listar_tarefas(self.usuario_atual["id"], categoria=categoria)
        for tarefa in tarefas:
            self._montar_linha_tarefa(lista_frame, tarefa, categoria, canteiro)

        tk.Button(moldura, text="+ Nova tarefa", command=lambda: self._criar_tarefa_dialogo(categoria),
                  bg="#dcedc8", relief="flat").pack(pady=(0, 10))

    def _montar_linha_tarefa(self, painel_pai, tarefa, categoria, canteiro):
        linha = tk.Frame(painel_pai, bg="white")
        linha.pack(fill="x", pady=2)

        if categoria == "habitos":
            icone_check = self.carregar_icone("check_verde.png", (16, 16))
            icone_x = self.carregar_icone("x_vermelho.png", (16, 16))

            if icone_check:
                btn_bom = tk.Button(linha, image=icone_check,
                                    command=lambda: self._clicar_habito(tarefa, canteiro, True),
                                    relief="flat", bg="#e8f5e9")
                btn_bom.image = icone_check
            else:
                btn_bom = tk.Button(linha, text="✔", fg="#2e7d32", font=("Segoe UI", 10, "bold"),
                                    command=lambda: self._clicar_habito(tarefa, canteiro, True),
                                    relief="flat", bg="#e8f5e9", width=2, height=1)
            btn_bom.pack(side="left", padx=1)

            if icone_x:
                btn_ruim = tk.Button(linha, image=icone_x,
                                     command=lambda: self._clicar_habito(tarefa, canteiro, False),
                                     relief="flat", bg="#ffebee")
                btn_ruim.image = icone_x
            else:
                btn_ruim = tk.Button(linha, text="✗", fg="#c62828", font=("Segoe UI", 10, "bold"),
                                     command=lambda: self._clicar_habito(tarefa, canteiro, False),
                                     relief="flat", bg="#ffebee", width=2, height=1)
            btn_ruim.pack(side="left", padx=1)
        else:
            var = tk.BooleanVar(value=bool(tarefa["concluida"]))
            tk.Checkbutton(linha, variable=var, bg="white",
                           command=lambda: self._alternar_conclusao(tarefa, canteiro, var)).pack(side="left")

        texto = tarefa["titulo"]
        if tarefa.get("prazo"):
            texto += f"  ({tarefa['prazo']})"
        cor_texto = "#aaa" if tarefa.get("concluida") else "black"
        tk.Label(linha, text=texto, bg="white", fg=cor_texto,
                 font=("Segoe UI", 9), anchor="w").pack(side="left", fill="x", expand=True)

        icone_lixeira = self.carregar_icone("lixeira_cinza.png", (14, 14))
        if icone_lixeira:
            btn_excluir = tk.Button(linha, image=icone_lixeira, command=lambda: self._excluir_tarefa(tarefa),
                                    relief="flat", bg="white")
            btn_excluir.image = icone_lixeira
        else:
            btn_excluir = tk.Button(linha, text="🗑", command=lambda: self._excluir_tarefa(tarefa),
                                    relief="flat", bg="white", fg="#999", width=2, height=1)
        btn_excluir.pack(side="right")

    # ---------- Loja ----------

    def mostrar_loja(self):
        self.limpar_tela()

        topo = tk.Frame(self.container, bg=COR_DESTAQUE, height=60)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Label(topo, text="🛒 Loja de Sementes", font=("Segoe UI", 15, "bold"),
                 bg=COR_DESTAQUE, fg="white").pack(side="left", padx=20)
        tk.Label(topo, text=f"🌰 {self.usuario_atual['sementes']} sementes",
                 font=("Segoe UI", 12), bg=COR_DESTAQUE, fg="white").pack(side="left", padx=10)
        tk.Button(topo, text="Voltar", command=self.mostrar_dashboard,
                  bg="#3a5f3d", fg="white", relief="flat").pack(side="right", padx=20)

        area_scroll = tk.Frame(self.container, bg=COR_FUNDO)
        area_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        canvas = tk.Canvas(area_scroll, bg=COR_FUNDO, highlightthickness=0)
        barra_rolagem = tk.Scrollbar(area_scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=barra_rolagem.set)
        barra_rolagem.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        corpo = tk.Frame(canvas, bg=COR_FUNDO)
        janela_corpo = canvas.create_window((0, 0), window=corpo, anchor="nw")

        def atualizar_scroll(evento=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_largura(evento):
            canvas.itemconfig(janela_corpo, width=evento.width)

        corpo.bind("<Configure>", atualizar_scroll)
        canvas.bind("<Configure>", ajustar_largura)

        def rolar_com_mouse(evento):
            canvas.yview_scroll(int(-1 * (evento.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", rolar_com_mouse)

        itens_comprados = db.obter_itens_comprados(self.usuario_atual["id"])

        colunas = 3
        for i, item in enumerate(jardim.CATALOGO_LOJA):
            cartao = tk.Frame(corpo, bg="white", relief="ridge", bd=1, width=220, height=220)
            cartao.grid(row=i // colunas, column=i % colunas, padx=10, pady=10)
            cartao.grid_propagate(False)

            imagem = self.carregar_imagem(item["arquivo"], tamanho=(80, 80))
            rotulo_img = tk.Label(cartao, image=imagem, bg="white")
            rotulo_img.image = imagem
            rotulo_img.pack(pady=(15, 5))

            tk.Label(cartao, text=item["nome"], font=("Segoe UI", 11, "bold"), bg="white").pack()
            tk.Label(cartao, text=f"🌰 {item['preco']} sementes", bg="white", fg="#666").pack(pady=(0, 8))

            ja_tem = item["id"] in itens_comprados
            if ja_tem:
                categoria_equipada = itens_comprados[item["id"]]
                if categoria_equipada:
                    tk.Label(cartao, text=f"Equipado em {NOMES_CATEGORIA.get(categoria_equipada, '')}",
                             bg="white", fg=COR_DESTAQUE, font=("Segoe UI", 9, "italic")).pack()
                elif item["categoria"]:
                    tk.Button(cartao, text="Equipar", bg="#dcedc8", relief="flat",
                              command=lambda it=item: self._equipar_item(it)).pack()
                else:
                    tk.Label(cartao, text="✔ Adquirido", bg="white", fg="#888").pack()
            else:
                tk.Button(cartao, text="Comprar", bg=COR_DESTAQUE, fg="white", relief="flat",
                          command=lambda it=item: self._comprar_item(it)).pack()

    def _comprar_item(self, item):
        sucesso, mensagem = jardim.comprar_item_loja(self.usuario_atual, item["id"])
        if item["categoria"] and sucesso:
            db.equipar_item(self.usuario_atual["id"], item["id"], item["categoria"])
        self._atualizar_dados_usuario()
        if not sucesso:
            messagebox.showwarning("Loja", mensagem)
        else:
            self.tocar_som("comprar.wav")
            self._verificar_e_avisar_conquistas()
        self.mostrar_loja()

    def _equipar_item(self, item):
        db.equipar_item(self.usuario_atual["id"], item["id"], item["categoria"])
        self.mostrar_loja()

    # ---------- Manual ----------

    TEXTO_MANUAL = """🌱 BEM-VINDO AO JARDIM DAS TAREFAS

Este é um aplicativo de lista de tarefas onde cada coisa que você faz na vida real ajuda a cuidar de um jardim. Quanto mais organizado você fica, mais bonito o jardim fica.


📋 AS 3 CATEGORIAS

🌿 Hábitos
Coisas que você quer fazer (ou parar de fazer) repetidamente, sem prazo fixo. Cada hábito tem dois botões:
  ✔ verde = você fez algo bom (rega a planta)
  ✗ vermelho = você fez algo que queria evitar (prejudica a planta)
Exemplo: "Beber menos refrigerante", "Ler um pouco"

🌤️ Diárias
Tarefas que se repetem todo santo dia. Se você não marcar como feita, o canteiro de Diárias murcha na virada do dia — mesmo que o aplicativo esteja fechado.
Exemplo: "Escovar os dentes 2x", "Tomar água"

📌 Afazeres
Tarefas únicas, com prazo e prioridade. Depois de concluídas, elas somem da lista.
Exemplo: "Entregar o relatório até sexta"


🌸 COMO A PLANTA CRESCE

Cada canteiro tem uma barra de Saúde (0% a 100%). Completar tarefas aumenta a saúde; hábitos ruins e diárias perdidas diminuem. A planta passa por 4 estágios visuais:
  1️⃣ Semente (grama pequena)
  2️⃣ Broto (touceira)
  3️⃣ Planta (arbusto)
  4️⃣ Flor (floração completa, 85%+)

Se a saúde chegar a 0%, a planta morre 💀 e você precisa replantar gastando sementes.


🌰 SEMENTES E LOJA

Você ganha sementes toda vez que completa uma tarefa ou um hábito bom. Use a Loja (🛒 no topo) pra comprar espécies diferentes de flor (que substituem a flor padrão quando o canteiro floresce) e decorações.


⚙️ DIFICULDADE

Em Configurações, você escolhe Fácil / Médio / Difícil — isso muda o quanto hábitos ruins e diárias perdidas prejudicam a saúde dos canteiros.


🔥 STREAK

O número de dias seguidos em que você completou pelo menos uma tarefa. Perde o streak se passar um dia sem concluir nada.


🔒 SEGREDINHOS

Este jardim tem alguns easter eggs escondidos. Explore clicando nas coisas — talvez você encontre alguma surpresa no título da tela de login, ou nas próprias plantinhas...
"""

    def mostrar_manual(self):
        self.limpar_tela()

        topo = tk.Frame(self.container, bg=COR_DESTAQUE, height=60)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Label(topo, text="📖 Manual do Jardim", font=("Segoe UI", 15, "bold"),
                 bg=COR_DESTAQUE, fg="white").pack(side="left", padx=20)

        tela_anterior = self.mostrar_dashboard if self.usuario_atual else self.mostrar_tela_login
        tk.Button(topo, text="Voltar", command=tela_anterior,
                  bg="#3a5f3d", fg="white", relief="flat").pack(side="right", padx=20)

        corpo = tk.Frame(self.container, bg=COR_FUNDO)
        corpo.pack(fill="both", expand=True, padx=20, pady=15)

        caixa_scroll = tk.Frame(corpo, bg=COR_FUNDO)
        caixa_scroll.pack(fill="both", expand=True)

        barra_rolagem = tk.Scrollbar(caixa_scroll)
        barra_rolagem.pack(side="right", fill="y")

        texto = tk.Text(caixa_scroll, wrap="word", font=("Segoe UI", 10), bg="white",
                        relief="flat", padx=15, pady=15, yscrollcommand=barra_rolagem.set)
        texto.insert("1.0", self.TEXTO_MANUAL)
        texto.config(state="disabled")
        texto.pack(side="left", fill="both", expand=True)
        barra_rolagem.config(command=texto.yview)

    # ---------- Conquistas ----------

    def mostrar_conquistas(self):
        self.limpar_tela()

        topo = tk.Frame(self.container, bg=COR_DESTAQUE, height=60)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Label(topo, text="🏆 Conquistas", font=("Segoe UI", 15, "bold"),
                 bg=COR_DESTAQUE, fg="white").pack(side="left", padx=20)
        tk.Button(topo, text="Voltar", command=self.mostrar_dashboard,
                  bg="#3a5f3d", fg="white", relief="flat").pack(side="right", padx=20)

        area_scroll = tk.Frame(self.container, bg=COR_FUNDO)
        area_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        canvas = tk.Canvas(area_scroll, bg=COR_FUNDO, highlightthickness=0)
        barra_rolagem = tk.Scrollbar(area_scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=barra_rolagem.set)
        barra_rolagem.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        corpo = tk.Frame(canvas, bg=COR_FUNDO)
        janela_corpo = canvas.create_window((0, 0), window=corpo, anchor="nw")

        def atualizar_scroll(evento=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_largura(evento):
            canvas.itemconfig(janela_corpo, width=evento.width)

        corpo.bind("<Configure>", atualizar_scroll)
        canvas.bind("<Configure>", ajustar_largura)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        desbloqueadas = db.obter_conquistas_desbloqueadas(self.usuario_atual["id"])

        for item in jardim.CATALOGO_CONQUISTAS:
            conquistada = item["id"] in desbloqueadas
            linha = tk.Frame(corpo, bg="white" if conquistada else "#f0f0f0",
                             relief="ridge", bd=1)
            linha.pack(fill="x", pady=4)

            cor_texto = "black" if conquistada else "#aaa"
            emoji = item["emoji"] if conquistada else "🔒"

            tk.Label(linha, text=emoji, font=("Segoe UI", 20), bg=linha.cget("bg")).pack(side="left", padx=15, pady=10)
            caixa_texto = tk.Frame(linha, bg=linha.cget("bg"))
            caixa_texto.pack(side="left", fill="x", expand=True, pady=10)
            tk.Label(caixa_texto, text=item["nome"], font=("Segoe UI", 11, "bold"),
                     bg=linha.cget("bg"), fg=cor_texto, anchor="w").pack(fill="x")
            tk.Label(caixa_texto, text=item["descricao"], font=("Segoe UI", 9),
                     bg=linha.cget("bg"), fg=cor_texto, anchor="w").pack(fill="x")

        total = len(jardim.CATALOGO_CONQUISTAS)
        tk.Label(corpo, text=f"{len(desbloqueadas)} / {total} conquistas desbloqueadas",
                 font=("Segoe UI", 10, "italic"), bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(10, 0))

    def _verificar_e_avisar_conquistas(self):
        novas = jardim.verificar_conquistas(self.usuario_atual)
        if novas:
            nomes = "\n".join(f"{c['emoji']} {c['nome']} — {c['descricao']}" for c in novas)
            self.after(200, lambda: messagebox.showinfo("Nova conquista desbloqueada!", nomes))

    # ---------- Configurações ----------

    def mostrar_configuracoes(self):
        self.limpar_tela()
        painel = tk.Frame(self.container, bg=COR_FUNDO)
        painel.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(painel, text="⚙ Configurações", font=("Segoe UI", 20, "bold"),
                 bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(0, 20))

        tk.Label(painel, text="Dificuldade (afeta o dano de hábitos ruins e diárias perdidas):",
                 bg=COR_FUNDO, font=("Segoe UI", 10)).pack(pady=(0, 10))

        dificuldade_var = tk.StringVar(value=self.usuario_atual.get("dificuldade", "medio"))
        for valor, rotulo in [("facil", "Fácil"), ("medio", "Médio"), ("dificil", "Difícil")]:
            tk.Radiobutton(painel, text=rotulo, variable=dificuldade_var, value=valor,
                           bg=COR_FUNDO, font=("Segoe UI", 11)).pack(anchor="w")

        def salvar():
            db.atualizar_dificuldade(self.usuario_atual["id"], dificuldade_var.get())
            self._atualizar_dados_usuario()
            messagebox.showinfo("Configurações", "Dificuldade atualizada!")
            self.mostrar_dashboard()

        tk.Button(painel, text="Salvar", command=salvar, bg=COR_DESTAQUE, fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", width=20).pack(pady=(20, 5))
        tk.Button(painel, text="Voltar", command=self.mostrar_dashboard,
                  font=("Segoe UI", 10), relief="flat", bg=COR_FUNDO, fg="#888").pack()

    # ---------- Animação simples ----------

    def _animar_crescimento(self, categoria):
        """Efeito visual simples: a planta 'pisca' e aumenta de tamanho por um instante."""
        rotulo = self.rotulos_plantas.get(categoria)
        if rotulo is None or not rotulo.winfo_exists():
            return

        canteiros = db.obter_canteiros(self.usuario_atual["id"])
        canteiro = canteiros[categoria]
        itens_equipados = db.obter_itens_comprados(self.usuario_atual["id"])
        item_equipado_aqui = next((iid for iid, cat in itens_equipados.items() if cat == categoria), None)
        nome_sprite = jardim.nome_arquivo_sprite(categoria, canteiro["estagio"], canteiro["vivo"], item_equipado_aqui)

        imagem_grande = self.carregar_imagem(nome_sprite, tamanho=(130, 130))
        imagem_normal = self.carregar_imagem(nome_sprite, tamanho=(100, 100))

        rotulo.config(image=imagem_grande)
        rotulo.image = imagem_grande
        self.after(180, lambda: (rotulo.config(image=imagem_normal), setattr(rotulo, "image", imagem_normal))
        if rotulo.winfo_exists() else None)

    def _criar_tarefa_dialogo(self, categoria):
        titulo = simpledialog.askstring("Nova tarefa", "Nome da tarefa:")
        if not titulo:
            return

        prazo = None
        prioridade = None
        if categoria == "afazeres":
            prazo = simpledialog.askstring("Prazo", "Data limite (ex: 2026-09-10) — opcional:")
            prioridade = simpledialog.askstring("Prioridade", "alta / media / baixa:")

        db.criar_tarefa(self.usuario_atual["id"], categoria, titulo, prioridade=prioridade, prazo=prazo)
        self.mostrar_dashboard()

    def _alternar_conclusao(self, tarefa, canteiro, var):
        if var.get():
            jardim.completar_tarefa(self.usuario_atual, tarefa, canteiro)
            self._atualizar_dados_usuario()
            self.mostrar_dashboard()
            self._animar_crescimento(tarefa["categoria"])
            self.tocar_som("completar.wav")
            self._verificar_e_avisar_conquistas()
        else:
            jardim.desfazer_tarefa(self.usuario_atual, tarefa, canteiro)
            self._atualizar_dados_usuario()
            self.mostrar_dashboard()

    def _clicar_habito(self, tarefa, canteiro, bom):
        resultado = jardim.registrar_habito(self.usuario_atual, tarefa, canteiro, bom)
        self._atualizar_dados_usuario()

        if resultado.get("limite_atingido"):
            messagebox.showinfo("Limite diário",
                                "Esse hábito já atingiu o limite de recompensas por hoje.\n"
                                "Volte amanhã para continuar ganhando por ele.")
            return

        if resultado["morreu"]:
            messagebox.showwarning("Ops!", "Esse canteiro murchou e morreu por causa desse hábito ruim.")
        self.mostrar_dashboard()
        if bom and not resultado["morreu"]:
            self._animar_crescimento(tarefa["categoria"])
            self.tocar_som("completar.wav")
            self._verificar_e_avisar_conquistas()

    def _excluir_tarefa(self, tarefa):
        if messagebox.askyesno("Confirmar", f"Excluir '{tarefa['titulo']}'?"):
            db.excluir_tarefa(tarefa["id"])
            self.mostrar_dashboard()

    def _replantar(self, categoria, canteiro):
        sucesso = jardim.replantar(self.usuario_atual, canteiro)
        if not sucesso:
            messagebox.showwarning("Sementes insuficientes",
                                   f"Você precisa de {jardim.CUSTO_REPLANTIO} sementes para replantar.")
            return
        self._atualizar_dados_usuario()
        self.mostrar_dashboard()
        self._verificar_e_avisar_conquistas()

    def _atualizar_dados_usuario(self):
        self.usuario_atual = db.obter_usuario_por_nome(self.usuario_atual["nome_usuario"])


if __name__ == "__main__":
    db.inicializar_banco()
    app = AplicativoJardim()
    app.mainloop()