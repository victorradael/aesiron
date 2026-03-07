#!/bin/bash
# Wrapper para executar a CLI do Aesiron usando o venv local
ABS_PATH=$(realpath "$(dirname "$0")")
if [ ! -d "$ABS_PATH/.venv" ]; then
    echo "Erro: Ambiente virtual não encontrado. Execute 'make setup-cli' primeiro."
    exit 1
fi
"$ABS_PATH/.venv/bin/aesiron" "$@"
