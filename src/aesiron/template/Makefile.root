# Variáveis
COMPOSE := docker compose
NETWORK_NAME := aesiron-net
ARMORY_DIR := ../aesiron-armory

# Coleta todos os apps que possuem um Makefile na Armory
APPS := $(shell find $(ARMORY_DIR) -maxdepth 2 -name Makefile -exec dirname {} \; | xargs -n1 basename 2>/dev/null)

# Targets principais
.PHONY: help setup-dev run dev down logs app remove urls clean rerun banner _ensure_armory
.DEFAULT_GOAL := help

# Garante que a pasta da Armaria existe antes de qualquer operação
_ensure_armory:
	@mkdir -p $(ARMORY_DIR)

##@ Ajuda

banner:
	@printf "\033[1;36m"
	@printf "    _    _____ ____ ___ ____   ___  _   _ \n"
	@printf "   / \  | ____/ ___|_ _|  _ \ / _ \| \ | |\n"
	@printf "  / _ \ |  _| \___ \| || |_) | | | |  \| |\n"
	@printf " / ___ \| |___ ___) | ||  _ <| |_| | |\  |\n"
	@printf "/_/   \_\_____|____/___|_| \_\ ___/|_| \_|\n"
	@printf "\033[0m\n"

help: banner  ## Mostra esta mensagem de ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


PYTHON := python3
VENV_PATH := $(ARMORY_DIR)/.venv
PIP := $(VENV_PATH)/bin/pip

##@ Ambiente de Desenvolvimento (Host)

setup-dev: _ensure_armory  ## Configura o ambiente virtual (.venv) na Armaria e instala dependências de TODOS os apps
	@echo "Removendo ambiente virtual anterior na Armaria (se houver)..."
	@rm -rf $(VENV_PATH)
	@echo "Criando novo ambiente virtual em $(VENV_PATH)..."
	@$(PYTHON) -m venv $(VENV_PATH)
	@echo "Atualizando pip e setuptools..."
	@. $(VENV_PATH)/bin/activate && \
		$(PIP) install --upgrade pip setuptools >/dev/null
	@for app in $(APPS); do \
		if [ -f "$(ARMORY_DIR)/$$app/requirements.txt" ]; then \
			echo "Instalando dependências de: $$app..."; \
			. $(VENV_PATH)/bin/activate && \
			$(PIP) install -r $(ARMORY_DIR)/$$app/requirements.txt >/dev/null || echo "Falha ao instalar dependências de $$app"; \
		fi \
	done
	@echo "Ambiente configurado com sucesso! Utilize o .venv da pasta $(ARMORY_DIR) no seu editor."

##@ Gerenciamento de Execução

# Capturar possível argumento de nome do app para run, dev, down e logs
APP_TARGET := $(word 2,$(MAKECMDGOALS))

run: banner ## Inicia os apps (Uso: make run [nome])
dev: banner ## Inicia os apps em modo interativo (Uso: make dev [nome])
down: ## Para os apps (Uso: make down [nome])
logs: ## Exibe logs dos apps (Uso: make logs [nome])

run dev down logs: _ensure_armory
	@docker network create $(NETWORK_NAME) || true
	@if [ -n "$(APP_TARGET)" ]; then \
		if [ -d "$(ARMORY_DIR)/$(APP_TARGET)" ]; then \
			echo "Executing $@ on $(APP_TARGET)..."; \
			$(MAKE) -C $(ARMORY_DIR)/$(APP_TARGET) $@; \
		else \
			echo "Error: App $(APP_TARGET) not found in Armory"; \
			exit 1; \
		fi \
	else \
		for app in $(APPS); do \
			echo "Executing $@ on $$app..."; \
			$(MAKE) -C $(ARMORY_DIR)/$$app $@; \
		done \
	fi
	@if [ "$@" = "run" ]; then $(MAKE) urls; fi

rerun: down run  ## Reinicia o ambiente executando down e run em sequência

urls:  ## Mostra as URLs de acesso local/Wi-Fi para os apps
	@IP=$$(hostname -I | awk '{print $$1}'); \
	CONTAINERS=$$(docker ps --format '{{.Names}}|{{.Ports}}' | grep app-aesiron); \
	if [ -n "$$CONTAINERS" ]; then \
		echo ""; \
		printf "\033[1;36m┌──────────────────────────────────────────────────────────┐\033[0m\n"; \
		printf "\033[1;36m│          🚀 APLICATIVOS DISPONÍVEIS NA REDE              │\033[0m\n"; \
		printf "\033[1;36m└──────────────────────────────────────────────────────────┘\033[0m\n"; \
		echo "$$CONTAINERS" | while IFS='|' read -r name ports; do \
			APP_NAME=$$(echo $$name | sed 's/app-aesiron-//'); \
			PORT=$$(echo $$ports | sed -E 's/.*0\.0\.0\.0:([0-9]+)->.*/\1/'); \
			printf "  \033[1;33m%-15s\033[0m \033[1;32m➜\033[0m  http://%s:%s\n" "$$APP_NAME" "$$IP" "$$PORT"; \
		done; \
		echo ""; \
	else \
		printf "\n\033[1;31m[!] Nenhuma aplicação está rodando no momento.\033[0m\n\n"; \
	fi

clean:  ## Remove imagens Docker locais de aplicações para liberar espaço (Uso: make clean)
	@docker images --filter=reference='app-aesiron-*' -q | xargs -r docker rmi -f

##@ Gerenciamento de Projetos e Geradores

# Remove um app existente da armory
remove:  ## Remove completamente um app existente da armory (Uso: make remove <nome>)
	@if [ -z "$(word 2,$(MAKECMDGOALS))" ]; then \
		echo "Error: App name is required. Usage: make remove-app nome-do-app"; \
		exit 1; \
	fi
	$(eval APP_NAME := $(word 2,$(MAKECMDGOALS)))
	@echo "Removing app: $(APP_NAME)"
	@if [ ! -d "$(ARMORY_DIR)/$(APP_NAME)" ]; then \
		echo "Error: App directory $(ARMORY_DIR)/$(APP_NAME) does not exist"; \
		exit 1; \
	fi
	@echo "Stopping and removing containers for $(APP_NAME)..."
	@if [ -f "$(ARMORY_DIR)/$(APP_NAME)/Makefile" ]; then \
		$(MAKE) -C $(ARMORY_DIR)/$(APP_NAME) down >/dev/null 2>&1 || true; \
	fi
	@echo "Removing docker image app-aesiron-$(APP_NAME)..."
	@docker rmi app-aesiron-$(APP_NAME):latest >/dev/null 2>&1 || true
	@echo "Cleaning up root-owned cache files using docker..."
	@docker run --rm -v $(PWD)/$(ARMORY_DIR)/$(APP_NAME):/app alpine sh -c "rm -rf /app/* /app/.* 2>/dev/null" || true
	@echo "Removing app directory..."
	@rm -rf $(ARMORY_DIR)/$(APP_NAME)
	@echo "App $(APP_NAME) removed successfully!"

# Criar novo app descentralizado
app: _ensure_armory  ## Cria um app Streamlit independente na armory (Uso: make app <nome> <porta>)
	@if [ -z "$(word 2,$(MAKECMDGOALS))" ]; then \
		echo "Error: App name is required. Usage: make app nome_do_app 8502"; \
		exit 1; \
	fi
	@if [ -z "$(word 3,$(MAKECMDGOALS))" ]; then \
		echo "Error: Port is required. Usage: make app nome_do_app 8502"; \
		exit 1; \
	fi
	$(eval APP_NAME := $(word 2,$(MAKECMDGOALS)))
	$(eval PORT := $(word 3,$(MAKECMDGOALS)))
	@echo "Forging new decentralized app: $(APP_NAME) on port $(PORT)"
	@mkdir -p $(ARMORY_DIR)/$(APP_NAME)
	@cp -r template/. $(ARMORY_DIR)/$(APP_NAME)/
	@cp $(ARMORY_DIR)/$(APP_NAME)/.env.example $(ARMORY_DIR)/$(APP_NAME)/.env
	@find $(ARMORY_DIR)/$(APP_NAME) -type f -exec sed -i 's/{{APP_NAME}}/$(APP_NAME)/g' {} +
	@find $(ARMORY_DIR)/$(APP_NAME) -type f -exec sed -i 's/{{PORT}}/$(PORT)/g' {} +
	@echo "App $(APP_NAME) created successfully in $(ARMORY_DIR)!"
	@echo "Now you can run 'make run $(APP_NAME)' from here or go to the app folder."

# Regra para capturar argumentos posicionais sem erro
%:
	@:
