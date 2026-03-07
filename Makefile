# Variáveis
COMPOSE := docker compose
NETWORK_NAME := aesiron-net

# Targets principais
.PHONY: setup-dev run dev down logs app remove-app urls

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

setup-dev:
	@echo "Removing previous virtual environment (if any)..."
	rm -rf $(VENV_DIR)
	@echo "Creating new virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	. $(VENV_DIR)/bin/activate && \
		$(PIP) install --upgrade pip setuptools && \
		[ -f requirements.txt ] && $(PIP) install -r requirements.txt || echo "No requirements.txt found"
	@echo "Setup complete."

run:
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) up -d

dev:
	docker network create $(NETWORK_NAME) || true
	$(COMPOSE) $(ALL_FILES) up 


down:
	$(COMPOSE) $(ALL_FILES) down
	docker network rm $(NETWORK_NAME) || true

logs:
	$(COMPOSE) $(ALL_FILES) logs -f

urls:
	@IP=$$(hostname -I | awk '{print $$1}'); \
	if docker ps --format '{{.Names}}' | grep -q app-aesiron; then \
		echo "Aplicações rodando na rede interna:"; \
		docker ps --format '{{.Names}}|{{.Ports}}' | grep app-aesiron | awk -F'|' '{print $$1" "$$2}' | sed -E "s/app-aesiron-([^ ]+) .*0\.0\.0\.0:([0-9]+)->.*/- \1: http:\/\/$$IP:\2/"; \
	else \
		echo "Nenhuma aplicação está rodando no momento."; \
	fi

clean:
	docker images -a | grep 'app-aesiron-' | awk '{print $$3}' | xargs -r docker rmi -f

rerun: down run

# Remove um app existente
# Uso: make remove-app nome-do-app
remove:
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
# Uso: make app nome_do_app 8502
app:
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
