FROM python:3.11-slim

# Instala dependências do sistema (incluindo docker e make)
RUN apt-get update && apt-get install -y \
    docker.io \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia o projeto
COPY . .

# Instala o pacote
RUN pip install --no-cache-dir -e .

# Define o Arsenal padrão (pode ser sobrescrito via ENV)
ENV AESIRON_ARMORY=/armory

# Entrypoint default
ENTRYPOINT ["aesiron"]
