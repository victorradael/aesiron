FROM python:3.13-alpine

# Instala dependências do sistema
RUN apk add --no-cache \
    docker \
    docker-cli-compose \
    make

WORKDIR /tmp/aesiron-src

# Copia e instala a própria CLI no sistema global, depois limpa os fontes para poupar espaço
COPY . .
RUN pip install --no-cache-dir . \
    && rm -rf /tmp/aesiron-src

# Define a pasta onde os projetos da CLI vão ficar (o volume)
VOLUME /armory
WORKDIR /armory

# Mantém a ENV para compatibilidade
ENV AESIRON_ARMORY=/armory

# Entrypoint default para rodar o aesiron e passar comandos a ele
ENTRYPOINT ["aesiron"]
