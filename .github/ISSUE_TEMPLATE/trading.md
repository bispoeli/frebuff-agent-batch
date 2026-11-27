---
name: Trading XAUUSD MT5
about: Dispara agente de análise técnica no XAUUSD
title: '[Trading] '
labels: ['trading']
assignees: ''

body:
  - type: textarea
    id: tarefas
    attributes:
      label: Tarefas de Trading
      description: |
        Liste uma tarefa por linha. Cada tarefa será analisada por um agente separado.
        Exemplo:
        - Analisar XAUUSD no M5 e sugerir entrada com SL/TP
        - Identificar níveis de suporte e resistência
      placeholder: |
        - Tarefa 1
        - Tarefa 2
        - Tarefa 3
    validations:
      required: true

  - type: dropdown
    id: modelo
    attributes:
      label: Modelo LLM
      description: Modelo usado para análise
      options:
        - nvidia/nemotron-3.5-lightning-30b-a3b
      default: 0
    validations:
      required: false

  - type: checkboxes
    id: opcoes
    attributes:
      label: Opções
      options:
        - label: Criar PR automático para cada tarefa
          required: false
          value: true
        - label: Usar contexto limpo (sem histórico de sessão)
          required: false
          value: true