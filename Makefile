# Variáveis de Desenvolvimento
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help setup-dev install-dev build lint clean-all

.DEFAULT_GOAL := help

help: ## Mostra esta ajuda (Comandos para DEVELOPERS)
	@printf "\033[1;31m⚠ COMANDOS PARA DESENVOLVEDORES DA CLI ⚠\033[0m\n"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } ' $(MAKEFILE_LIST)

setup-dev: ## Prepara o ambiente virtual para desenvolvimento
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip setuptools
	@$(PIP) install -e .
	@echo "Ambiente de dev configurado. Ative com: source $(VENV)/bin/activate"

install-dev: setup-dev ## Instala dependências de desenvolvimento

build: ## Versão de build (exemplo)
	@$(PYTHON) -m pip install build
	@$(PYTHON) -m build

lint: ## Roda verificações de código
	@$(PIP) install ruff
	@$(VENV)/bin/ruff check .

clean-all: ## Limpa tudo (venv, cache, builds)
	rm -rf $(VENV) dist/ build/ *.egg-info .ruff_cache
	@docker images --filter=reference='app-aesiron-*' -q | xargs -r docker rmi -f

release: ## Automação de nova versão (Uso: make release v=0.2.0)
	@if [ -z "$(v)" ]; then echo "Erro: Informe a versão (ex: make release v=1.0.0)"; exit 1; fi
	@echo "Lançando versão $(v)..."
	@sed -i 's/^version = .*/version = "$(v)"/' pyproject.toml
	@git add pyproject.toml
	@git commit -m "chore: bump version to $(v)"
	@git tag -a v$(v) -m "Release v$(v)"
	@git push origin main
	@git push origin v$(v)
	@echo "Versão v$(v) lançada e enviada para o GitHub!"
