# Acesso pela Rede Local (Wi-Fi)

Este documento explica como qualquer aplicação criada neste projeto (como o **build_keeper**) é configurada nativamente para ser acessada por outros dispositivos (como celulares) na mesma rede Wi-Fi.

## Como as portas são definidas
Nesta arquitetura, as portas não são fixas em `8501`. Quando uma nova aplicação é gerada através do comando `make app`:

```bash
make app nome_do_app [PORTA]
```

O script automaticamente copia o `template` e configura a porta escolhida em dois lugares essenciais:

1. **`compose.yml`**: A porta base é exposta e mapeada de forma igual entre Host e Contêiner (ex: `8503:8503`).
2. **`app/.streamlit/config.toml`**: O Streamlit é instruído a rodar explicitamente nessa porta determinada pela variável `[server] port = [PORTA]`.

Isso garante que cada desenvolvedor possa subir múltiplos apps simultaneamente na mesma máquina, sem colisões de porta.

## Acesso pela Rede Interna (Wi-Fi)
Por padrão, o Docker mapeia as portas divulgadas no `compose.yml` (ex: `8503:8503`) na interface principal da máquina host (`0.0.0.0`). 

Isso significa que, no momento em que a aplicação sobe utilizando o `make run` ou o `docker compose up -d`, ela **já está disponível para toda a sua rede local!**

### Como descobrir sua URL Local
Para acessar de um dispositivo móvel ou outro computador na mesma rede, usamos o comando:

```bash
make urls
```

Ele irá checar o IP interno da sua máquina conectada (ex: `192.168.2.141`) e descobrir dinamicamente quais portas as aplicações `app-aesiron-*` estão utilizando, imprimindo um link pronto:
`http://192.168.2.141:8503`

## Rodando o Streamlit manualmente (Sem Docker)
Caso você queira debugar e rodar o Streamlit diretamente na sua máquina host (sem utilizar o Docker), por padrão ele limitará o acesso ao `localhost`.

Para permitir que outros dispositivos acessem, passe a flag `--server.address 0.0.0.0`:

```bash
streamlit run app/app.py --server.address 0.0.0.0
```
*(Não é necessário passar o `--server.port`, pois ele já vai ler automaticamente seu arquivo `.streamlit/config.toml` e levantar a configuração correta).*
