# Guia para escrever boas specs

## Objetivo

Uma spec deve explicar com clareza o que sera construido, por que isso importa e como a entrega sera considerada concluida.

## Principios

- escrever para reduzir ambiguidade
- priorizar clareza sobre volume
- separar problema, solucao proposta e execucao
- registrar decisoes importantes e seus impactos
- tornar a leitura rapida e a implementacao previsivel

## Estrutura recomendada

Toda spec deve, sempre que fizer sentido, cobrir:

- contexto do problema
- objetivo da funcionalidade
- escopo
- fora de escopo
- requisitos funcionais
- requisitos nao funcionais
- proposta de solucao
- plano de implementacao em etapas
- riscos e pontos de atencao
- criterios de aceite

## Boas praticas

- comecar pelo resultado esperado
- usar linguagem objetiva e verificavel
- explicitar premissas e dependencias
- listar trade-offs quando houver mais de uma abordagem valida
- definir convencoes de nomes, formatos e comportamento
- descrever o fluxo principal e casos de borda relevantes
- incluir criterios de aceite que possam ser testados
- manter a spec atualizada quando a decisao mudar

## Padronizacao

- titulos curtos e descritivos
- secoes em ordem logica: contexto, decisao, execucao, validacao
- listas numeradas para passos e prioridades
- bullets para regras, requisitos e riscos
- termos consistentes do inicio ao fim
- uma ideia por item

## O que evitar

- texto vago ou promocional
- excesso de detalhe irrelevante para a decisao
- misturar requisito com implementacao sem sinalizar
- omitir restricoes importantes
- deixar criterios de aceite subjetivos
- escrever specs que dependem de conhecimento tacito

## Definicao de boa spec

Uma boa spec permite que outra pessoa entenda rapidamente:

- o problema real
- a abordagem escolhida
- a ordem de execucao
- os riscos principais
- como validar que a entrega esta pronta
