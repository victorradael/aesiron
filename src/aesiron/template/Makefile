# Variáveis locais do App {{APP_NAME}}
COMPOSE := docker compose
APP_NAME := {{APP_NAME}}

.PHONY: run dev down logs

run: ## Sobe o app em background
	$(COMPOSE) up --build -d

dev: ## Sobe o app em modo interativo
	$(COMPOSE) up --build

down: ## Para o app
	$(COMPOSE) down

logs: ## Mostra os logs do app
	$(COMPOSE) logs -f
