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
    build: ./apps/{{APP_NAME}}
    image: app-aesiron-{{APP_NAME}}
    container_name: app-aesiron-{{APP_NAME}}
    volumes:
      - ./apps/{{APP_NAME}}/app:/app
    ports:
      - "{{PORT}}:{{PORT}}"
    env_file:
      - ./apps/{{APP_NAME}}/.env
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

run: banner  ## Inicia os contêineres em background (detached mode)
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) up -d

dev: banner  ## Inicia os contêineres conectando os terminais (modo interativo)
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) $(ALL_FILES) up 


down:  ## Para e remove todos os contêineres e a rede criada
	$(COMPOSE) $(ALL_FILES) down
	docker network rm $(NETWORK_NAME) || true

##@ Manutenção e Observabilidade

logs:  ## Exibe os logs contínuos de todos os contêineres rodando
	$(COMPOSE) $(ALL_FILES) logs -f

urls:  ## Mostra as URLs para acessar os apps por dispositivos na mesma rede (Wi-Fi/Local)
	@IP=$$(hostname -I | awk '{print $$1}'); \
	if docker ps --format '{{.Names}}' | grep -q app-aesiron; then \
		echo "Aplicações rodando na rede interna:"; \
		docker ps --format '{{.Names}}|{{.Ports}}' | grep app-aesiron | awk -F'|' '{print $$1" "$$2}' | sed -E "s/app-aesiron-([^ ]+) .*0\.0\.0\.0:([0-9]+)->.*/- \1: http:\/\/$$IP:\2/"; \
	else \
		echo "Nenhuma aplicação está rodando no momento."; \
	fi

clean:  ## Remove imagens Docker locais de aplicações para liberar espaço
	docker images -a | grep 'app-aesiron-' | awk '{print $$3}' | xargs -r docker rmi -f

rerun: down run  ## Reinicia o ambiente, derrubando tudo e subindo novamente

##@ Gerenciamento de Projetos e Apps

# Remove um app existente
remove:  ## Remove completamente um app existente e suas entradas no compose (Uso: make remove <nome>)
	@if [ -z "$(word 2,$(MAKECMDGOALS))" ]; then \
		echo "Error: App name is required. Usage: make remove-app nome-do-app"; \
		exit 1; \
	fi
	$(eval APP_NAME := $(word 2,$(MAKECMDGOALS)))
	@echo "Removing app: $(APP_NAME)"
	@if [ ! -d "apps/$(APP_NAME)" ]; then \
		echo "Error: App directory apps/$(APP_NAME) does not exist"; \
		exit 1; \
	fi
	@echo "Removing app directory..."
	@rm -rf apps/$(APP_NAME)
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
	@echo "Creating new app: $(APP_NAME) with port: $(PORT)"
	@mkdir -p apps/$(APP_NAME)
	@cp -r template/. apps/$(APP_NAME)/
	@find apps/$(APP_NAME) -type f -exec sed -i 's/{{APP_NAME}}/$(APP_NAME)/g' {} +
	@find apps/$(APP_NAME) -type f -exec sed -i 's/{{PORT}}/$(PORT)/g' {} +
	@echo "$$COMPOSE_SERVICE_TEMPLATE" | sed 's/{{APP_NAME}}/$(APP_NAME)/g' | sed 's/{{PORT}}/$(PORT)/g' >> compose.yml
	@echo "App $(APP_NAME) created successfully!"
	@echo "Don't forget to:"
	@echo "1. Configure .env file in apps/$(APP_NAME)/.env"
	@echo "2. Review the new service in compose.yml"
