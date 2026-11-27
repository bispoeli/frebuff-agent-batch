#!/usr/bin/env python3
"""
Apps Agent - Criação de specs e código para APKs
Gera especificações detalhadas para apps de música, bandas, orquestras, orçamentos e finanças.
"""

import os
import re
import json
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def call_llm(messages: list, api_key: str, model: str = "nvidia/nemotron-3.5-lightning-30b-a3b") -> str:
    """Chama a API NVIDIA NIM."""
    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 8000
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
    print("║  Fazenda de Agentes - Criação de Apps/APKs                         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    nvidia_key = os.environ.get('NVIDIA_API_KEY', '')
    if not nvidia_key:
        print("❌ NVIDIA_API_KEY não configurada!")
        exit(1)

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

    print(f"📋 {len(tasks)} tarefa(s) encontrada(s)")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")

    if not tasks:
        print("❌ Nenhuma tarefa válida encontrada")
        exit(1)

    os.makedirs("apps/specs", exist_ok=True)
    os.makedirs("apps/codigo", exist_ok=True)

    for idx, task in enumerate(tasks):
        print(f"\n🤖 [{idx+1}] Iniciando: {task[:60]}...")

        system_prompt = """Você é um arquiteto de software especializado em aplicativos móveis (Android/iOS).
Sua função é criar especificações técnicas detalhadas e código inicial para apps móveis.

Inclua na especificação:
- Nome do app e descrição
- Telas (screens) com campos e botões
- Fluxo de navegação
- Banco de dados local (SQLite)
- Regras de negócio
- Módulos principais

Gere código em Flutter ou React Native quando solicitado."""

        user_prompt = f"""Tarefa: {task}

Crie uma especificação completa e código inicial para este app móvel."""

        llm_response = call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], nvidia_key)

        if not llm_response:
            print(f"❌ [{idx+1}] Sem resposta do LLM")
            continue

        print(f"   📝 Resposta ({len(llm_response)} chars)")

        safe_name = re.sub(r'[^a-z0-9\s-]', '', task.lower().replace(' ', '-')[:40])
        spec_file = f"apps/specs/spec_{idx+1}_{safe_name}.md"

        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(f"# Spec do App - Agente {idx+1}\n\n")
            f.write(f"**Tarefa:** {task}\n\n")
            f.write(f"**Modelo:** nvidia/nemotron-3.5-lightning-30b-a3b\n\n")
            f.write(f"**Especificação:**\n\n{llm_response}\n\n")
            f.write(f"---\n*Gerado pela Fazenda de Agentes OpenCode - NVIDIA NIM*\n")

        print(f"   💾 Spec salva em: {spec_file}")

        # Commit
        subprocess.run(['git', 'add', '-A'], capture_output=True)
        commit_msg = f"feat(agent-{idx+1}): spec app - {task[:50]}"
        subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        subprocess.run(['git', 'push', 'origin', f"agent-{idx+1}-{safe_name}"], capture_output=True, text=True)

    print("\n✅ Criação de apps concluída!")
    print("📱 Verifique a pasta apps/specs/ para as especificações geradas.")


if __name__ == '__main__':
    main()