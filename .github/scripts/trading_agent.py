#!/usr/bin/env python3
"""
Trading Agent - Análise XAUUSD MT5 via NVIDIA Nemotron 3.5 Lightning.
Gera sinais de entrada, stop loss e take profit baseado em análise técnica.
"""

import os
import re
import json
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def call_nvidia_llm(messages: list, api_key: str) -> str:
    """Chama a API NVIDIA NIM (Nemotron 3.5 Lightning)."""
    data = json.dumps({
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 4000
    }).encode()

    req = Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        resp = urlopen(req, timeout=120)
        result = json.loads(resp.read())
        choice = result['choices'][0]['message']
        content = choice.get('content') or choice.get('reasoning_content') or ''
        return content
    except HTTPError as e:
        print(f"   ⚠️  LLM API error: {e.code} {e.read()[:200]}")
        return None
    except URLError as e:
        print(f"   ⚠️  LLM network error: {e}")
        return None


def main():
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  Fazenda de Agentes - Trading XAUUSD MT5                           ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    nvidia_key = os.environ.get('NVIDIA_API_KEY', '')
    if not nvidia_key:
        print("❌ NVIDIA_API_KEY não configurada!")
        exit(1)

    print(f"⚙️  Modelo: nvidia/nemotron-3.5-lightning-30b-a3b")
    print(f"⚙️  Provedor: NVIDIA NIM")
    print()

    # Ler tarefas do arquivo de issue
    issue_body = os.environ.get('ISSUE_BODY', '')
    issue_number = os.environ.get('ISSUE_NUMBER', '0')

    if not issue_body:
        event_path = os.environ.get('GITHUB_EVENT_PATH', '')
        if event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            issue_body = event_data.get('issue', {}).get('body', '')
            issue_number = str(event_data.get('issue', {}).get('number', '0'))

    # Extrair tarefas
    tasks = []
    for line in issue_body.split('\n'):
        stripped = line.strip()
        if re.match(r'^[-*] ', stripped):
            task = re.sub(r'^[-*] ', '', stripped)
            if task and not task.startswith('#') and not task.startswith('##') and not task.startswith('---'):
                tasks.append(task.strip())

    print(f"📋 {len(tasks)} tarefa(s) de trading encontrada(s)")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")

    if not tasks:
        print("❌ Nenhuma tarefa válida encontrada")
        exit(1)

    # Loop por cada tarefa
    for idx, task in enumerate(tasks):
        print(f"\n🤖 [{idx+1}] Iniciando: {task[:60]}...")

        system_prompt = """Você é um trader sênior especializado em XAUUSD (Ouro) no MetaTrader 5.
Sua função é APENAS ANALISAR mercados e gerar sinais de entrada. NÃO EXECUTE ordens.

Você deve:
1. Analisar o timeframe M5 (5 minutos) do XAUUSD
2. Identificar níveis de suporte e resistência
3. Calcular stop loss e take profit baseado em ATR
4. Sugerir direção (BUY/SELL) com nível de confiança
5. Justificar a análise com indicadores (RSI, MACD, Donchian Channel)

IMPORTANTE: Nunca envie ordens de execução. Apenas analise e sugira."""

        user_prompt = f"""Tarefa: {task}

Forneça uma análise completa de XAUUSD no M5 com:
- Direção (BUY/SELL/NEUTRO)
- Nível de entrada sugerido
- Stop loss (pips)
- Take profit (pips)
- Confiança (0-100%)
- Justificativa técnica

Responda em português."""

        llm_response = call_nvidia_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], nvidia_key)

        if not llm_response:
            print(f"❌ [{idx+1}] Sem resposta do LLM")
            continue

        print(f"   📝 Resposta ({len(llm_response)} chars)")

        # Salvar sinal em arquivo
        safe_name = re.sub(r'[^a-z0-9\s-]', '', task.lower().replace(' ', '-')[:40])
        signal_file = f"trading/sinais/sinal_{idx+1}_{safe_name}.md"

        os.makedirs("trading/sinais", exist_ok=True)

        with open(signal_file, 'w', encoding='utf-8') as f:
            f.write(f"# Sinal de Trading - Agente {idx+1}\n\n")
            f.write(f"**Tarefa:** {task}\n\n")
            f.write(f"**Modelo:** nvidia/nemotron-3.5-lightning-30b-a3b\n\n")
            f.write(f"**Análise:**\n\n{llm_response}\n\n")
            f.write(f"---\n*Gerado pela Fazenda de Agentes OpenCode - NVIDIA NIM*\n")

        print(f"   💾 Sinal salvo em: {signal_file}")

        # Commit da análise
        subprocess.run(['git', 'add', '-A'], capture_output=True)
        commit_msg = f"feat(agent-{idx+1}): sinal XAUUSD - {task[:50]}"
        subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        subprocess.run(['git', 'push', 'origin', f"agent-{idx+1}-{safe_name}"], capture_output=True, text=True)

    print("\n✅ Análise de trading concluída!")
    print("📊 Verifique a pasta trading/sinais/ para os sinais gerados.")


if __name__ == '__main__':
    main()