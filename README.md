# 🌱 Jardim das Tarefas

Um aplicativo de lista de tarefas gamificado, com tema de jardim, inspirado no conceito do Habitica. Em vez de números e listas frias, cada hábito, tarefa diária e afazer cuidado ajuda a fazer um jardim crescer — e cada tarefa negligenciada o deixa murchar.

Projeto 016 da Saga MundoPessoal.

---

## ✨ Funcionalidades

- **Conta com login e múltiplos perfis** — autenticação com senha (hash + sal), recuperação por pergunta secreta
- **3 categorias de tarefas**, cada uma com seu próprio canteiro:
  - 🌿 **Hábitos** — ações repetíveis, marcadas como boas ou ruins
  - 🌤️ **Diárias** — tarefas que resetam todo dia; ficar sem completar murcha o canteiro
  - 📌 **Afazeres** — tarefas únicas, com prazo e prioridade
- **Crescimento visual real**: cada canteiro evolui em 4 estágios (semente → broto → planta → flor) conforme a saúde sobe; pode morrer e precisar ser replantado
- **Economia de sementes**: ganhe sementes completando tarefas e gaste numa loja com 18 itens (espécies de flores e decorações)
- **Nível de Jardineiro e Conquistas**: sistema de XP com títulos progressivos e 12 conquistas desbloqueáveis
- **Cenário interativo**: céu com sol/nuvens, cerca, decorações plantadas na terra, e um regador arrastável com o mouse (puramente decorativo)
- **Dificuldade configurável** (fácil / médio / difícil)
- **Easter eggs escondidos** — vale a pena clicar nas coisas
- **Efeitos sonoros** (Windows, via `winsound`)
- **Manual integrado**, acessível já na tela de login

---

## 🛠️ Tecnologias

- **Python 3** com **tkinter** (interface gráfica, biblioteca padrão)
- **SQLite** (`sqlite3`, biblioteca padrão) para persistência de dados
- **Pillow (PIL)** para carregar e redimensionar imagens
- **winsound** (biblioteca padrão do Windows) para efeitos sonoros

---

## 📦 Instalação

### Pré-requisitos
- Python 3.10 ou mais recente
- Sistema operacional Windows (para os efeitos sonoros; o restante do app funciona em qualquer sistema)

### Passo a passo

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd jardim-das-tarefas
   ```

2. Instale a única dependência externa:
   ```bash
   pip install Pillow
   ```

3. Rode o aplicativo:
   ```bash
   python main.py
   ```

Na primeira execução, o banco de dados (`jardim.db`) é criado automaticamente na mesma pasta.

---

## ▶️ Como usar

1. Na tela inicial, clique em **Criar Conta** e cadastre usuário, senha e uma pergunta secreta (para recuperação futura)
2. Depois de logado, adicione tarefas nas 3 colunas (Hábitos, Diárias, Afazeres) usando o botão **+ Nova tarefa**
3. Complete tarefas para regar os canteiros e ganhar sementes
4. Use as sementes na **Loja** para comprar novas espécies de plantas e decorações
5. Acompanhe seu progresso pelo **Nível de Jardineiro** e pelas **Conquistas**, no topo da tela
6. Consulte o **Manual** (📖) a qualquer momento se tiver dúvidas sobre alguma mecânica

> Quer testar sem esperar acumular sementes jogando? Faça login com usuário `teste123` e senha `teste123` — a conta é criada automaticamente na primeira vez, já com 1 milhão de sementes.

---

## 📁 Estrutura do projeto

```
jardim-das-tarefas/
├── main.py              # Interface gráfica (todas as telas)
├── database.py          # Camada de persistência (SQLite)
├── jardim.py            # Regras de jogo (crescimento, loja, conquistas, XP)
├── jardim.db            # Banco de dados (gerado automaticamente, não versionado)
└── assets/
    ├── plantas/         # Sprites de crescimento e espécies da loja
    ├── icones/          # Ícones de interface (check, X, lixeira, regador, etc.)
    ├── fundos/          # Texturas de fundo
    └── sons/            # Efeitos sonoros (.wav)
```

---

## 🎨 Créditos de assets

Os elementos visuais (plantas, ícones, cerca) e sonoros usados são do banco de assets gratuitos **[Kenney](https://kenney.nl/)**, licenciados sob **CC0 1.0 (domínio público)** — uso livre em projetos pessoais e comerciais, crédito apreciado mas não obrigatório.

---

## 📄 Licença

Projeto pessoal, desenvolvido para fins de aprendizado como parte da Saga MundoPessoal (100 projetos em Python).
