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

O Aesiron foi projetado para ser um **Ferreiro de Software**. A principal interface de interação é o `Makefile` na raiz, que orquestra a criação e execução de apps independentes.

### 1. Configuração Inicial

Antes de forjar seus aplicativos, você precisa criar o "Arsenal" (o repositório irmão) onde os apps gerados serão salvos. Ele deve ficar **exatamente no mesmo nível de diretório** que a pasta do Aesiron.

```bash
# Volte uma pasta para trás, caso esteja dentro do aesiron
cd ..
mkdir aesiron-armory
cd aesiron
```

### 2. Criando o seu Primeiro App

Crie um novo app independente informando o **nome** e a **porta**:

```bash
make app meu-app 8501
```

Isso forjará a estrutura completa do app em `../aesiron-armory/meu-app`. O app gerado é **autossuficiente** e possui seu próprio `compose.yml` e `Makefile`.

### 3. Orquestração e Execução

Você pode gerenciar seus apps de duas formas:

**A. Pelo Aesiron (Orquestração Massiva):**
Na raiz do Aesiron, você pode comandar todos os apps da Armaria ao mesmo tempo:
```bash
make run          # Sobe TODOS os apps da Armaria
make run meu-app  # Sobe apenas um app específico
make down         # Derruba todos
```

**B. Pelo Aplicativo (Execução Isolada):**
Você pode entrar na pasta de qualquer app na Armaria e usar os comandos locais:
```bash
cd ../aesiron-armory/meu-app
make run
```

---

## 🎯 Comandos do Aesiron (Ferreiro)

| Comando | Descrição |
|---|---|
| `make app <nome> <porta>` | Forja um novo app independente na Armaria |
| `make remove <nome>` | Remove um app permanentemente da Armaria |
| `make run [nome]` | Inicia apps (todos ou um específico) |
| `make down [nome]` | Para os apps |
| `make logs [nome]` | Exibe logs dos apps |
| `make urls` | Mostra as URLs de todos os apps rodando na rede |
| `make clean` | Limpa imagens Docker `app-aesiron-*` |

---

## 📁 Estrutura Descentralizada

A nova arquitetura garante que a ferramenta (`aesiron`) e os produtos (`armory`) vivam separados:

```text
projetos/
├── aesiron/                # O "Ferreiro": Gerador e Orquestrador Massivo
│   ├── template/           # Moldes (Templates) dos apps
│   └── Makefile            # Painel de Controle Central
│
└── aesiron-armory/         # O "Arsenal": Coleção de Apps Independentes
    └── meu-app/
        ├── app/            # Código Python/Streamlit
        ├── compose.yml     # Orquestração local do app
        ├── Makefile        # Comandos locais do app
        └── .env            # Configurações sensíveis
```

---

## 🕸️ Rede & Comunicação

O Aesiron cria e gerencia automaticamente uma rede Docker externa chamada `aesiron-net`. 
Se você possuir outros serviços em Docker num arquivo diferente ou quiser que seus apps Streamlit comuniquem entre si (ou com APIs / Bancos de Dados locais), basta referenciá-los através desta rede compartilhada.
