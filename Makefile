# Variáveis
CLI := ./aesiron-cli.sh

.PHONY: help setup-cli forge run stop list urls destroy clean banner

.DEFAULT_GOAL := help

banner:
	@$(CLI) --help | head -n 1 || true
	@printf "\033[1;36m"
	@printf "    _    _____ ____ ___ ____   ___  _   _ \n"
	@printf "   / \  | ____/ ___|_ _|  _ \ / _ \| \ | |\n"
	@printf "  / _ \ |  _| \___ \| || |_) | | | |  \| |\n"
	@printf " / ___ \| |___ ___) | ||  _ <| |_| | |\  |\n"
	@printf "/_/   \_\_____|____/___|_| \_\ ___/|_| \_|\n"
	@printf "\033[0m\n"

help: banner ## Mostra esta mensagem de ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } ' $(MAKEFILE_LIST)

setup-cli: ## Configura o ambiente da CLI localmente
	@python3 -m venv .venv
	@. .venv/bin/activate && pip install -e .
	@chmod +x aesiron-cli.sh
	@echo "CLI configurada com sucesso! Use './aesiron-cli.sh' ou os comandos do Makefile."

forge: ## Forja um novo app (Uso: make forge name=meu-app port=8501)
	@$(CLI) forge $(name) --port $(port)

run: ## Inicia apps (Uso: make run [name=meu-app])
	@$(CLI) run $(name)

stop: ## Para apps (Uso: make stop [name=meu-app])
	@$(CLI) stop $(name)

list: ## Lista apps no arsenal
	@$(CLI) list

urls: ## Mostra as URLs de acesso
	@$(CLI) urls

destroy: ## Remove um app (Uso: make destroy name=meu-app)
	@$(CLI) destroy $(name)

clean: ## Limpa imagens docker
	@docker images --filter=reference='app-aesiron-*' -q | xargs -r docker rmi -f
