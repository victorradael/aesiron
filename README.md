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

Isso forjará a estrutura do app no repositório irmão em `../aesiron-armory/meu-app` e o adicionará automaticamente ao arquivo `compose.yml` da ferramenta.
> **Aviso:** Lembre-se de configurar o arquivo `.env` gerado dentro da pasta do seu novo app, caso necessite de chaves secretas ou configuração de banco de dados.

### 3. Subindo os Serviços

Inicie todos os seus apps em background com o comando:

```bash
make run
```

Se quiser iniciar apenas o novo app que você acabou de criar (e deixar os demais parados), basta informar o nome dele:

```bash
make run meu-app
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
| `make app <nome> <porta>` | Cria um novo app Streamlit na armory (Ex: `make app painel 8502`) |
| `make remove <nome>` | Remove completamente um app existente da armory e do compose local |
| `make run [nome]` / `make dev [nome]` | Inicia os serviços (todos ou usando um nome em modo bg/interativo) |
| `make down [nome]` | Para e remove todos os contêineres e a rede (ou apenas de um app) |
| `make logs [nome]` | Exibe os logs contínuos de todos os apps (ou de um específico) em execução |
| `make urls` | Mostra as URLs locais para explorar e acessar os apps na sua rede (Wi-Fi) |
| `make clean` | Limpa imagens Docker descartáveis para poupar espaço no HD |

---

## 📁 Estrutura do Projeto

A organização do repositório foi pensada em formato de "Ferreiro e Armaria". A ferramenta mora num repositório e seus projetos moram em outro, paralelos entre si:

```text
projetos/
├── aesiron/                # A "Forja": O gerador e orquestrador via Docker centralizado
│   ├── template/           # Template base utilizado pelo comando "make app"
│   ├── assets/             # Recursos visuais (logo)
│   ├── compose.yml         # Arquivo mestre de orquestração do Docker
│   └── Makefile            # Central de comandos e gerenciamento
│
└── aesiron-armory/         # O "Arsenal": A sua coleção de apps gerados independentes
    ├── meu-app-1/          # App independente com seu próprio código e .env
    └── meu-app-2/          # Outro app...
```

---

## 🕸️ Rede & Comunicação

O Aesiron cria e gerencia automaticamente uma rede Docker externa chamada `aesiron-net`. 
Se você possuir outros serviços em Docker num arquivo diferente ou quiser que seus apps Streamlit comuniquem entre si (ou com APIs / Bancos de Dados locais), basta referenciá-los através desta rede compartilhada.
