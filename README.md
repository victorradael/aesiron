<p align="center">
  <img src="./assets/aesiron.png" width="250" alt="Aesiron Logo" />
</p>

<h1 align="center">Aesiron</h1>

<p align="center">
  <strong>Gerenciador de Múltiplos Apps Streamlit com Docker & Make</strong>
</p>

<p align="center">
  Crie, gerencie e faça o deploy de múltiplos apps Streamlit de forma rápida, isolada e organizada.
</p>

---

## 🛠️ Requisitos

Certifique-se de ter as seguintes ferramentas instaladas em sua máquina:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Make](https://www.gnu.org/software/make/)
- Python 3.x

---

## 🚀 Como Começar

O Aesiron foi projetado para ser direto ao ponto. A principal interface de interação é o `Makefile`, que é totalmente **auto-documentado**.

### 1. Configuração Inicial

Prepare seu ambiente de desenvolvimento local (isto cria o ambiente virtual Python e instala dependências básicas):

```bash
make setup-dev
```

### 2. Criando o seu Primeiro App

Crie um novo app a partir do template padrão informando o **nome do app** e a **porta**:

```bash
make app meu-app 8501
```

Isso criará a estrutura do app em `apps/meu-app` e o adicionará automaticamente ao arquivo `compose.yml`.
> **Aviso:** Lembre-se de configurar o arquivo `.env` gerado dentro da pasta do seu novo app, caso necessite de chaves secretas ou configuração de banco de dados.

### 3. Subindo os Serviços

Inicie todos os seus apps em background com o comando:

```bash
make run
```

Pronto! Seu app estará rodando e disponível na porta que você configurou.

---

## 🎯 Comandos Úteis (Make)

Você não precisa decorar dezenas de comandos Docker. Para ver a lista completa de ações possíveis, basta rodar:

```bash
make help
```

Isso exibirá todos os atalhos diretamente no seu terminal, incluindo os mais comuns:

| Comando | Descrição |
|---|---|
| `make app <nome> <porta>` | Cria um novo app Streamlit (Ex: `make app painel 8502`) |
| `make remove <nome>` | Remove completamente um app existente (diretório e compose) |
| `make run` / `make dev` | Inicia os serviços (em background ou modo interativo) |
| `make down` | Para e remove todos os contêineres e a rede do projeto |
| `make logs` | Exibe os logs contínuos de todos os apps em execução |
| `make urls` | Mostra as URLs locais para explorar e acessar os apps na sua rede (Wi-Fi) |
| `make clean` | Limpa imagens Docker descartáveis para poupar espaço no HD |

---

## 📁 Estrutura do Projeto

A organização do repositório foi pensada para escalar:

```text
aesiron/
├── apps/               # Diretório onde ficam seus aplicativos
│   ├── meu-app-1/      # App independente com seu próprio código e .env
│   └── meu-app-2/      # Outro app...
├── template/           # Template base utilizado pelo comando "make app"
├── assets/             # Recursos visuais (logo)
├── compose.yml         # Arquivo mestre de orquestração do Docker
└── Makefile            # Central de comandos e gerenciamento
```

---

## 🕸️ Rede & Comunicação

O Aesiron cria e gerencia automaticamente uma rede Docker externa chamada `aesiron-net`. 
Se você possuir outros serviços em Docker num arquivo diferente ou quiser que seus apps Streamlit comuniquem entre si (ou com APIs / Bancos de Dados locais), basta referenciá-los através desta rede compartilhada.
