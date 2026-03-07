# Variáveis
COMPOSE := docker compose
NETWORK_NAME := aesiron-net

# Targets principais
.PHONY: help setup-dev run dev down logs app remove urls clean rerun banner
.DEFAULT_GOAL := help

##@ Ajuda

banner:
	@printf "\033[1;36m"
	@printf "    _    _____ ____ ___ ____   ___  _   _ \n"
	@printf "   / \  | ____/ ___|_ _|  _ \ / _ \| \ | |\n"
	@printf "  / _ \ |  _| \___ \| || |_) | | | |  \| |\n"
	@printf " / ___ \| |___ ___) | ||  _ <| |_| | |\  |\n"
	@printf "/_/   \_\_____|____/___|_| \_\___/|_| \_|\n"
	@printf "\033[0m\n"

help: banner  ## Mostra esta mensagem de ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# Função para criar novo app
define COMPOSE_SERVICE_TEMPLATE
\n  {{APP_NAME}}:
    build: ../aesiron-armory/{{APP_NAME}}
    image: app-aesiron-{{APP_NAME}}
    container_name: app-aesiron-{{APP_NAME}}
    volumes:
      - ../aesiron-armory/{{APP_NAME}}/app:/app
    ports:
      - "{{PORT}}:{{PORT}}"
    env_file:
      - ../aesiron-armory/{{APP_NAME}}/.env
    networks:
      - aesiron-net
endef
export COMPOSE_SERVICE_TEMPLATE


PYTHON := python3
VENV_DIR := .venv
PIP := $(VENV_DIR)/bin/pip

##@ Ambiente de Desenvolvimento (Host)

setup-dev:  ## Configura o ambiente virtual Python (.venv) e instala dependências
	@echo "Removing previous virtual environment (if any)..."
	rm -rf $(VENV_DIR)
	@echo "Creating new virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	. $(VENV_DIR)/bin/activate && \
		$(PIP) install --upgrade pip setuptools && \
		[ -f requirements.txt ] && $(PIP) install -r requirements.txt || echo "No requirements.txt found"
	@echo "Setup complete."

##@ Execução e Deploy

# Capturar possível argumento de nome do app para run, dev, down e logs
APP_TARGET := $(word 2,$(MAKECMDGOALS))
APP_SERVICE := $(APP_TARGET)

run: banner  ## Inicia os contêineres em background (Uso: make run [nome-do-app])
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) up -d $(APP_SERVICE)

dev: banner  ## Inicia os contêineres conectando os terminais em modo interativo (Uso: make dev [nome-do-app])
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) $(ALL_FILES) up $(APP_SERVICE)

down:  ## Para e remove contêineres e a rede criada (Uso: make down [nome-do-app])
	$(COMPOSE) $(ALL_FILES) down $(APP_SERVICE)
	$(if $(APP_TARGET),,docker network rm $(NETWORK_NAME) || true)

##@ Manutenção e Observabilidade

logs:  ## Exibe os logs contínuos dos contêineres rodando (Uso: make logs [nome-do-app])
	$(COMPOSE) $(ALL_FILES) logs -f $(APP_SERVICE)

urls:  ## Mostra as URLs para acessar os apps por dispositivos na mesma rede (Wi-Fi/Local)
	@IP=$$(hostname -I | awk '{print $$1}'); \
	if docker ps --format '{{.Names}}' | grep -q app-aesiron; then \
		echo "Aplicações rodando na rede interna:"; \
		docker ps --format '{{.Names}}|{{.Ports}}' | grep app-aesiron | awk -F'|' '{print $$1" "$$2}' | sed -E "s/app-aesiron-([^ ]+) .*0\.0\.0\.0:([0-9]+)->.*/- \1: http:\/\/$$IP:\2/"; \
	else \
		echo "Nenhuma aplicação está rodando no momento."; \
	fi

clean:  ## Remove imagens Docker locais de aplicações para liberar espaço (Uso: make clean)
	@docker images --filter=reference='app-aesiron-*' -q | xargs -r docker rmi -f

rerun: down run  ## Reinicia o ambiente, derrubando tudo e subindo novamente

##@ Gerenciamento de Projetos e Apps

# Remove um app existente
remove:  ## Remove completamente um app existente da armory e suas entradas no compose (Uso: make remove <nome>)
	@if [ -z "$(word 2,$(MAKECMDGOALS))" ]; then \
		echo "Error: App name is required. Usage: make remove-app nome-do-app"; \
		exit 1; \
	fi
	$(eval APP_NAME := $(word 2,$(MAKECMDGOALS)))
	@echo "Removing app: $(APP_NAME)"
	@if [ ! -d "../aesiron-armory/$(APP_NAME)" ]; then \
		echo "Error: App directory ../aesiron-armory/$(APP_NAME) does not exist"; \
		exit 1; \
	fi
	@echo "Cleaning up root-owned cache files using docker..."
	@docker run --rm -v $(PWD)/../aesiron-armory/$(APP_NAME):/app alpine sh -c "rm -rf /app/* /app/.* 2>/dev/null" || true
	@echo "Removing app directory..."
	@rm -rf ../aesiron-armory/$(APP_NAME)
	@echo "Removing service from compose.yml..."
	@sed -i '/^[[:space:]]*$(APP_NAME):/,/[[:space:]]*- aesiron-net/d' compose.yml
	@sed -i '/^$$/N;/^\n$$/D' compose.yml  # Remove linhas em branco duplicadas
	@echo "App $(APP_NAME) removed successfully!"
	@echo "Don't forget to run 'make down' and 'make run' to apply the changes"

# Regra para capturar argumentos posicionais
%:
	@:

# Criar novo app baseado no template
app:  ## Cria um app Streamlit a partir do template (Uso: make app <nome>)
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
	@echo "Creating new app: $(APP_NAME) with port: $(PORT) in aesiron-armory"
	@mkdir -p ../aesiron-armory/$(APP_NAME)
	@cp -r template/. ../aesiron-armory/$(APP_NAME)/
	@cp ../aesiron-armory/$(APP_NAME)/.env.example ../aesiron-armory/$(APP_NAME)/.env
	@find ../aesiron-armory/$(APP_NAME) -type f -exec sed -i 's/{{APP_NAME}}/$(APP_NAME)/g' {} +
	@find ../aesiron-armory/$(APP_NAME) -type f -exec sed -i 's/{{PORT}}/$(PORT)/g' {} +
	@echo "$$COMPOSE_SERVICE_TEMPLATE" | sed 's/{{APP_NAME}}/$(APP_NAME)/g' | sed 's/{{PORT}}/$(PORT)/g' >> compose.yml
	@echo "App $(APP_NAME) created successfully in ../aesiron-armory!"
	@echo "Don't forget to:"
	@echo "1. Configure .env file in ../aesiron-armory/$(APP_NAME)/.env"
	@echo "2. Review the new service in compose.yml"
