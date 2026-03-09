FROM python:3.11-slim

# Instala dependências do sistema (incluindo docker e make)
RUN apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia o projeto
COPY . .

# Instala o pacote
RUN pip install --no-cache-dir -e .

# Define a pasta onde os projetos da CLI vão ficar (o volume)
VOLUME /armory
WORKDIR /armory

# Mantém a ENV para compatibilidade
ENV AESIRON_ARMORY=/armory

# Copia e instala a própria CLI no sistema global
COPY . /tmp/aesiron-src
RUN pip install --no-cache-dir -e /tmp/aesiron-src

# Entrypoint default para rodar o aesiron e passar comandos a ele
ENTRYPOINT ["aesiron"]
