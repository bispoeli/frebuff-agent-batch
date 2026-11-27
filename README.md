# 🚀 OpenCode Browser Automation Dashboard

Este é o painel de controle da Fazenda de Agentes OpenCode - uma automação completa de agentes de IA usando OpenCode + NVIDIA NIM + GitHub Actions.

## 📊 Dashboard

Acesse o dashboard em: **[https://eli.github.io/frebuff-agent-batch/](https://eli.github.io/frebuff-agent-batch/)**

## 🏗️ Estrutura

```
.github/
├── dashboard/
│   ├── index.html          # Interface do dashboard
│   ├── style.css           # Estilos
│   └── dashboard.js        # Lógica JavaScript
├── scripts/
│   ├── maestro_agent.py    # Motor principal dos agentes
│   ├── trading_agent.py    # Agente de trading MT5
│   ├── transcricao_agent.py # Agente de transcrição
│   ├── apps_agent.py       # Agente de criação de apps
│   └── deepseek_agent.py   # Agente DeepSeek gratuito
├── workflows/
│   ├── maestro.yml         # Orquestrador principal
│   └── agent-batch.yml     # Workflow alternativo
└── ISSUE_TEMPLATE/
    ├── trading.md
    ├── transcricao.md
    ├── app.md
    └── deepseek.md

trading/
├── risco.md
└── mq5/sinais_xauusd.mq5

transcricao/
└── ebook-template.html

apps/
├── musica/spec.md
└── orcamentos/spec.md

deepseek/
├── codigos/analise_mercado.py
└── roteiros/analise_xauusd.md
```

---

## 🚀 Como Usar

### 1. Configurar Token do GitHub

O dashboard precisa de um Personal Access Token do GitHub para funcionar:

1. Acesse [github.com/settings/tokens](https://github.com/settings/tokens)
2. Crie um novo token com escopo `repo`
3. No dashboard, clique no ícone de chave (ícone de chave no canto superior direito)
4. Insira seu token

### 2. Criar uma Issue

Abra uma issue no repositório com uma das seguintes labels:
- `trading` - Análise XAUUSD MT5
- `transcricao` - Transcrição YouTube
- `app` - Criação de app/APK
- `deepseek` - Código com DeepSeek

Exemplo de issue:

```
## Tarefas
- Analisar XAUUSD no M5 e sugerir entrada com SL/TP

## Modelo
nvidia/nemotron-3.5-lightning-30b-a3b

## Opções
- [x] Criar PR automático para cada tarefa
- [x] Usar contexto limpo
```

---

## 🛠️ Tecnologias

- **OpenCode** - Agente de IA
- **NVIDIA NIM** - Modelos Nemotron 3.5
- **DeepSeek** - Modelo gratuito alternativo
- **GitHub Actions** - Automação CI/CD
- **GitHub Pages** - Hospedagem do dashboard

---

## 📄 Licença

MIT License