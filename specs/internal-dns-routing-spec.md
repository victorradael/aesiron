# Especificacao de implementacao: DNS LAN para apps Aesiron

## Objetivo

Permitir que apps forjados pelo Aesiron possam ser acessados na rede interna por nomes amigaveis, por exemplo:

- `http://app.iron`
- `http://meu-dashboard.iron`

Em vez de depender de IP + porta, o usuario deve conseguir acessar cada app por hostname dentro da rede local do usuario.

## Escopo desta funcionalidade

Esta entrega nao implementa o codigo. Ela define o plano completo para implementar a funcionalidade.

## Observacao tecnica importante

DNS sozinho nao resolve o problema completo. Ele apenas traduz `app.local` para um IP. Para que `http://app.iron` abra o app correto sem informar porta, tambem sera necessario um roteador HTTP interno (reverse proxy) escutando na porta 80 da rede Aesiron.

Arquitetura recomendada:

- um container de DNS interno para resolver `*.iron` na LAN, com gateway na maquina do Aesiron
- um container de reverse proxy para receber requests HTTP na porta 80
- cada app Aesiron registrado com hostname proprio
- o proxy encaminha pelo header `Host` para o container correto

Sem proxy, o DNS ainda exigiria porta explicita, por exemplo `http://app.iron:8501`.

## Resultado esperado

Depois da implementacao:

- ao executar `aesiron run`, o ecossistema garante que a infraestrutura de rede interna esteja disponivel
- cada app criado ou iniciado pelo Aesiron fica acessivel por hostname previsivel
- `aesiron urls` passa a priorizar URLs por nome, por exemplo `http://meu-app.iron`
- a solucao funciona para varios apps em paralelo na mesma rede local

## Requisitos funcionais

1. Criar uma infraestrutura compartilhada da rede Aesiron para descoberta por nome.
2. Registrar cada app em um dominio interno previsivel baseado no nome do app.
3. Permitir acesso HTTP sem informar porta manualmente.
4. Suportar multiplos apps ao mesmo tempo.
5. Atualizar a experiencia da CLI para exibir os novos enderecos.
6. Permitir reinicio e destruicao de apps sem deixar configuracoes orfas.

## Requisitos nao funcionais

- manter o comportamento atual por porta como fallback temporario durante a migracao
- nao quebrar os fluxos atuais de `forge`, `run`, `stop`, `restart`, `destroy`, `urls`
- manter a responsabilidade por camadas conforme a arquitetura do projeto
- permitir testes automatizados sem depender de infraestrutura externa permanente

## Arquitetura proposta

### 1. Rede compartilhada existente

Reutilizar a rede Docker ja criada por `ensure_network()` com nome `aesiron-net`.

### 2. Container de DNS interno

Criar um servico infra, por exemplo `aesiron-dns`, com uma das abordagens abaixo:

- recomendado: `dnsmasq`
- alternativa: CoreDNS

Responsabilidade:

- responder consultas para dominios internos do Aesiron
- apontar `*.iron` ou uma zona dedicada do Aesiron para o IP do proxy interno

### 3. Container de reverse proxy

Criar um servico infra, por exemplo `aesiron-gateway`, com uma das abordagens abaixo:

- recomendado: Traefik
- alternativa: Nginx

Responsabilidade:

- escutar HTTP na porta 80
- ler rotas por hostname
- encaminhar `meu-app.iron` para o container `app-aesiron-meu-app`

### 4. Convencao de hostname

Mapeamento recomendado:

- nome do app: `financeiro`
- hostname: `financeiro.iron`

Regra:

- usar o nome do app em minusculas
- trocar espacos por hifen se algum fluxo futuro permitir
- manter apenas caracteres validos para hostname

## Plano de implementacao passo a passo

### Fase 1 - Definir a estrategia de rede

1. Confirmar a zona interna oficial da funcionalidade.
2. Recomendacao atual: usar `*.iron` apenas se o ambiente alvo aceitar bem multicast/local DNS; caso haja conflito, migrar para `*.aesiron.test` ou `*.aesiron.local`.
3. Documentar a decisao no projeto antes de codificar.
4. Definir se o acesso sera apenas entre containers ou tambem a partir da maquina host.

Saida esperada da fase:

- uma convencao oficial de hostname
- uma definicao clara do alcance da resolucao de nomes

### Fase 2 - Criar a infraestrutura compartilhada

1. Adicionar um diretoria/template de infraestrutura compartilhada do Aesiron, separada dos apps individuais.
2. Criar compose da infraestrutura com os servicos:
   - `aesiron-dns`
   - `aesiron-gateway`
3. Conectar ambos a rede `aesiron-net`.
4. Garantir reinicializacao automatica apropriada.
5. Definir nomes de container fixos para facilitar descoberta e manutencao.

Saida esperada da fase:

- compose proprio da infraestrutura interna
- containers compartilhados inicializaveis independentemente dos apps

### Fase 3 - Registrar rotas dos apps no gateway

1. Escolher a estrategia de registro dinamico.
2. Recomendacao atual: usar labels Docker nos containers dos apps e Traefik como descoberta automatica.
3. Ajustar o template de compose dos apps forjados para incluir labels de roteamento por hostname.
4. Garantir que o nome do host seja derivado do nome do app.
5. Garantir que o gateway enxergue apenas containers da rede `aesiron-net`.

Saida esperada da fase:

- todo app novo forjado ja nasce pronto para roteamento por hostname

### Fase 4 - Configurar o DNS

1. Fazer o DNS interno responder a zona escolhida.
2. Configurar a resolucao para apontar os hostnames dos apps para o IP do gateway.
3. Se a estrategia for wildcard, configurar `*.iron` ou a zona decidida para o gateway.
4. Se a estrategia for por registros explicitos, gerar/atualizar registros a cada app criado, removido ou renomeado.
5. Definir TTL baixo durante a fase inicial para facilitar propagacao e debug.

Saida esperada da fase:

- qualquer hostname valido do Aesiron resolve para o gateway na rede local

### Fase 5 - Integrar com os fluxos atuais do Aesiron

1. Atualizar a camada de services para subir a infraestrutura compartilhada antes dos apps quando necessario.
2. Encapsular isso em um caso de uso na camada application, sem jogar regra na CLI.
3. Garantir que `run_apps_command()` inicialize a infraestrutura base antes de subir os apps.
4. Garantir que `stop` de um app nao derrube DNS/proxy compartilhados.
5. Definir se havera um comando futuro dedicado para gerenciar a infra, como `aesiron infra up` e `aesiron infra down`.

Saida esperada da fase:

- fluxo atual do usuario continua simples
- a infraestrutura compartilhada e tratada como dependencia do ecossistema

### Fase 6 - Ajustar a exibicao de URLs

1. Atualizar a logica de descoberta em `src/aesiron/services/docker.py` para montar URLs baseadas em hostname.
2. Preservar o formato antigo com IP:porta como fallback, se necessario.
3. Atualizar a view da CLI para priorizar URLs amigaveis.
4. Exemplo esperado:
   - `financeiro -> http://financeiro.iron`

Saida esperada da fase:

- `aesiron urls` reflete o novo modelo de acesso

### Fase 7 - Tratar rename e destroy

1. Garantir que `rename_app()` atualize o hostname refletido no roteamento.
2. Garantir que `destroy_app()` remova o app sem deixar rota ativa no gateway.
3. Garantir que o DNS continue funcional para os apps restantes.
4. Se houver registros gerados dinamicamente, remover os registros antigos.

Saida esperada da fase:

- consistencia da rede apos mudancas de ciclo de vida dos apps

### Fase 8 - Testes automatizados

1. Criar testes unitarios para a regra de derivacao de hostname.
2. Criar testes dos services que montam configuracoes de infra e labels.
3. Criar testes da camada application para garantir que a infraestrutura e inicializada antes do app.
4. Criar testes da CLI para verificar a exibicao de URLs por hostname.
5. Se viavel no ambiente de CI, adicionar teste de integracao com Docker para validar roteamento real.

Saida esperada da fase:

- cobertura minima da logica critica sem acoplamento excessivo

### Fase 9 - Documentacao

1. Atualizar `README.md` explicando o novo fluxo.
2. Documentar como o DNS interno funciona.
3. Documentar limitacoes do dominio escolhido.
4. Mostrar exemplos com `forge`, `run` e `urls`.
5. Explicar fallback e troubleshooting.

Saida esperada da fase:

- usuario entende como acessar apps por nome e como depurar se falhar

## Mudancas previstas por area

### `src/aesiron/services/`

- novo modulo para infraestrutura compartilhada de rede
- possivel extracao da responsabilidade de URLs e gateway de `docker.py`
- helper puro para gerar hostname a partir do nome do app

### `src/aesiron/application/`

- casos de uso para garantir a infra antes de subir apps
- DTOs, se necessario, para representar URL publica por hostname

### `src/aesiron/cli.py`

- ajuste apenas de apresentacao, sem regras de negocio

### template dos apps

- incluir labels ou configuracao de proxy no compose gerado para cada app

### novos artefatos

- compose/template da infraestrutura compartilhada
- arquivos de configuracao do DNS
- arquivos de configuracao do proxy

## Decisoes recomendadas

1. Usar Traefik como gateway por facilitar descoberta dinamica via Docker labels.
2. Usar `dnsmasq` para o DNS se a necessidade for simples e direta.
3. Tratar `app.local` como requisito funcional desejado, mas validar tecnicamente se `local` e a melhor zona para o ambiente alvo.
4. Manter `ip:porta` como fallback ate a funcionalidade estabilizar.

## Riscos e pontos de atencao

### Uso de `.iron`

- `.local` pode conflitar com mDNS/Avahi/Bonjour em alguns ambientes
- se o objetivo incluir acesso a partir do host, esse risco aumenta

### Acesso a partir do host

- resolver nomes na LAN depende dos clientes usarem o DNS do Aesiron
- pode ser necessario expor o DNS ao host ou orientar configuracao local do sistema operacional

### DNS dinamico

- se o DNS mantiver registros por app, rename e destroy precisam ser muito bem tratados

### Dependencia extra

- a funcionalidade introduz pelo menos um ou dois containers compartilhados no ecossistema

## Criterios de aceite

1. Um app chamado `demo` pode ser acessado por `http://demo.iron` sem informar porta, dentro do escopo definido para a feature.
2. Dois ou mais apps podem coexistir com hostnames distintos na mesma rede.
3. `aesiron urls` mostra os enderecos por hostname.
4. `rename` atualiza o endereco esperado.
5. `destroy` remove o app sem quebrar os demais.
6. O fluxo atual por porta continua disponivel durante a transicao, se decidido assim.

## Ordem sugerida de execucao

1. escolher zona DNS
2. escolher proxy e DNS
3. criar infraestrutura compartilhada
4. adaptar template dos apps com roteamento
5. integrar subida da infra ao fluxo `run`
6. atualizar `urls`
7. cobrir rename/destroy
8. escrever testes
9. atualizar documentacao

## Fora de escopo nesta etapa

- HTTPS/TLS automatico
- painel administrativo para DNS
- descoberta fora do Docker sem configuracao adicional do host
- balanceamento entre varias replicas do mesmo app

## Definicao de pronto

A funcionalidade sera considerada concluida quando:

- a infraestrutura compartilhada subir de forma previsivel
- um app forjado puder ser acessado por hostname amigavel
- a CLI refletir esse novo endereco
- os fluxos de ciclo de vida continuarem consistentes
- os testes e a documentacao cobrirem o novo comportamento
