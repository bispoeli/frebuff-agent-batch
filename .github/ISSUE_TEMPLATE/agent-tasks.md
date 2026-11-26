---
name: Agent Tasks
about: Dispara a fazenda de agentes OpenCode via GitHub Actions
title: '[Agent Batch] '
labels: ['agent-batch', 'automation']
assignees: ''

body:
  - type: textarea
    id: tasks
    attributes:
      label: Tarefas
      description: |
        Lista uma tarefa por linha. Cada tarefa será executada por um agente OpenCode
        em uma VM Linux isolada e descartável via GitHub Actions.
        Exemplo:
        - Refatorar o módulo de gestão de risco
        - Adicionar testes unitários para o parser de candles
        - Corrigir o bug de sincronização do MT5 bridge
      placeholder: |
        - Tarefa 1
        - Tarefa 2
        - Tarefa 3
    validations:
      required: true

  - type: dropdown
    id: model
    attributes:
      label: Modelo LLM
      description: Modelo usado pelos agentes na fazenda
      options:
        - opencode/deepseek-v4.1-flash-free
        - nemotron-3-super-120b-a12b
        - llama-3.1-70b-instruct
        - qwen2.5-72b-instruct
      default: 0
    validations:
      required: false

  - type: checkboxes
    id: options
    attributes:
      label: Opções
      options:
        - label: Criar PR automático para cada tarefa
          required: false
          value: true
        - label: Usar contexto limpo (sem histórico de sessão)
          required: false
          value: true