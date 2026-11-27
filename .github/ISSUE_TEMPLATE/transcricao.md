---
name: Transcrição YouTube
about: Dispara agente de transcrição de vídeo para eBook HTML
title: '[Transcrição] '
labels: ['transcricao']
assignees: ''

body:
  - type: textarea
    id: tarefas
    attributes:
      label: Tarefas de Transcrição
      description: |
        Liste uma tarefa por linha. Cada tarefa será processada por um agente separado.
        Inclua URLs de vídeos do YouTube.
        Exemplo:
        - https://www.youtube.com/watch?v=...
        - Transcrever vídeo de trading e gerar eBook
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
      description: Modelo usado para transcrição
      options:
        - nvidia/nemotron-3.5-lightning-30b-a3b
        - opencode/deepseek-v4-flash-free
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
        - label: Usar contexto limpo
          required: false
          value: true