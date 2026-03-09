<p align="center">
  <img src="./assets/aesiron.png" width="250" alt="Aesiron Logo" />
</p>

<h1 align="center">Aesiron</h1>

<p align="center">
  <strong>O Ferreiro de Apps Streamlit Standalone</strong>
</p>

<p align="center">
  Forgue, gerencie e orquestre múltiplos aplicativos Streamlit em containers Docker com uma única ferramenta.
</p>

---

## ⚡ Plug-and-Play (Instalação Rápida)

Você **não precisa** clonar este repositório para usar o Aesiron. Escolha uma das formas abaixo:

### A. Via Python (Pip)
Instale diretamente do GitHub no seu ambiente Python:
```bash
pip install git+https://github.com/victorradael/aesiron.git
```
Agora o comando `aesiron` (ou seu alias mais curto, `iron`) estará disponível globalmente (ou no seu venv).

### B. Via Docker (Sem Python local)
Se você tem Docker, pode usar a CLI sem instalar nada no seu host. 
*(Recomendamos usar uma tag de versão específica, ex: `:0.1.0`, para maior estabilidade)*:
```bash
# Crie um alias para facilitar o uso (você pode escolher aesiron ou iron)
alias iron='docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/armory -e HOST_PWD=$(pwd) -e HOST_UID=$(id -u) -e HOST_GID=$(id -g) victorradael/aesiron:latest'

# Forjando um app
iron forge meu-app --port 8501
```

---

## 🚀 Como Funciona

O Aesiron gerencia um **Arsenal (Armory)**: diretório atual (`cwd`) onde seus apps independentes são criados.

1.  **Forjando um App**:
    ```bash
    aesiron forge meu-dashboard --port 8501
    ```
    Isso cria a pasta `./meu-dashboard` com tudo que o app precisa (Dockerfile, Compose, Makefile local).

2.  **Orquestração Massiva**:
    ```bash
    aesiron run          # Sobe TODOS os apps encontrados na pasta
    aesiron list         # Mostra quais apps estão rodando
    aesiron urls         # Exibe as URLs de acesso de todos os apps
    ```

---

## 🎯 Comandos da CLI

*Dica: Você pode usar `aesiron <comando>` ou simplesmente `iron <comando>`.*

| Comando | Descrição |
|---|---|
| `iron help` | Mostra os comandos disponíveis |
| `iron forge <nome>` | Cria um novo app independente |
| `iron run [nome]` | Inicia um ou todos os apps |
| `iron stop [nome]` | Para os containers |
| `iron list` | Status dos apps no Arsenal |
| `iron urls` | Painel de links de acesso |
| `iron destroy <nome>` | Remove permanentemente um app |

---

## 📁 Estrutura do Ecossistema

- **Ferreiro (CLI)**: A ferramenta que você instala para gerar e comandar.
- **Arsenal (Armory)**: Sua pasta de trabalho onde os apps gerados residem.
- **Apps Forjados**: Cada app é autossuficiente (Docker + Makefile local).

---

## 🛠️ Desenvolvimento (Para Contribuidores)

Se você quer modificar a CLI do Aesiron:

1.  Clone o repositório: `git clone ...`
2.  Configure o ambiente de dev: `make setup-dev`
3.  Teste suas mudanças: `source .venv/bin/activate && aesiron help`

---

## 🕸️ Rede & Comunicação
Todos os apps compartilham a rede `aesiron-net`, permitindo comunicação direta entre eles e outros serviços Docker.
