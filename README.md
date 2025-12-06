# Aesiron

## 📋 Requisitos

- Docker
- Docker Compose
- Make
- Python 3.x

## 🚀 Como Usar

### Configuração Inicial

1. Configure o ambiente de desenvolvimento:
```bash
make setup-dev
```

Este comando irá:
- Criar um ambiente virtual Python
- Instalar as dependências necessárias
- Configurar o ambiente de desenvolvimento

### Gerenciamento de Apps

#### Criar um Novo App
```bash
make app nome-do-app porta
```

Exemplo:
```bash
make app meu-app 8501
```

Este comando irá:
- Criar uma nova pasta em `apps/nome-do-app`
- Configurar o app com base no template padrão
- Adicionar o serviço no arquivo compose.yml
- Configurar a porta especificada

#### Remover um App Existente
```bash
make remove-app nome-do-app
```

Este comando irá:
- Remover a pasta do app em `apps/nome-do-app`
- Remover o serviço correspondente do compose.yml

### Comandos de Execução

#### Iniciar os Serviços
```bash
make run
```

#### Iniciar em Modo Desenvolvimento
```bash
make dev
```

#### Parar os Serviços
```bash
make down
```

#### Ver Logs
```bash
make logs
```

#### Limpar Imagens Docker
```bash
make clean
```

#### Reiniciar os Serviços
```bash
make rerun
```

## 📁 Estrutura do Projeto

```
.
├── apps/                    # Diretório principal dos apps
│   └── [outros-apps]/     # Apps individuais
├── template/               # Template para novos apps
├── compose.yml             # Configuração do Docker Compose
└── Makefile               # Comandos make para gestão do projeto
```

## 🔧 Desenvolvimento

### Template de App

O template em `template` é usado como base para novos apps. Ao criar um novo app, o conteúdo deste template é copiado e personalizado com:
- Nome do app
- Porta configurada
- Configurações específicas

### Docker Compose

Cada app é configurado como um serviço no `compose.yml` com:
- Build próprio
- Volume para desenvolvimento
- Porta mapeada
- Variáveis de ambiente via `.env`
- Rede compartilhada

## 🌐 Rede

O projeto usa uma rede Docker externa chamada `aesiron-net` para comunicação entre os serviços.

## ⚠️ Notas Importantes

1. Sempre configure o arquivo `.env` após criar um novo app
2. Revise as configurações no compose.yml após alterações
3. Use `make down` e `make run` para aplicar mudanças na configuração dos serviços

   Para iniciar os contêineres do Pub/Sub emulator e do cliente, rode o seguinte comando:

   ```bash
   make run
   ```

2. **Verificar logs**:

   Para acompanhar os logs enquanto os contêineres estão em execução, utilize o comando:

   ```bash
   make logs
   ```

3. **Parar os contêineres e remover a rede**:

   Quando terminar, pare os contêineres e remova a rede com:

   ```bash
   make down
   ```

4. **Reiniciar os contêineres**:

   Caso você precise reiniciar os serviços, pode usar o comando `rerun`:

   ```bash
   make rerun
   ```

### Explicação dos Targets no Makefile

- **client**: Inicializa o contêiner que representa o cliente que interage com o Pub/Sub emulator.
- **pubsub**: Inicializa o contêiner que executa o emulador do Google Pub/Sub.
- **run**: Cria a rede necessária e inicializa ambos os contêineres (Pub/Sub emulator e cliente).
- **down**: Derruba os contêineres e remove a rede.
- **logs**: Exibe logs dos contêineres em execução.
- **clean-images**: Remove as imagens Docker não utilizadas.
- **rerun**: Derruba os contêineres e os reinicia, criando a rede novamente.
