#!/usr/bin/env python3
"""
DeepSeek Agent - Tarefas gerais de código com modelo gratuito.
Usa DeepSeek v4 Flash via OpenCode (opencode/deepseek-v4-flash-free).
"""

import os
import re
import json
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def call_deepseek_llm(messages: list, api_key: str) -> str:
    """Chama a API DeepSeek via OpenRouter."""
    data = json.dumps({
        "model": "deepseek/deepseek-chat",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 8000
    }).encode()

    req = Request(
        "https://openrouter.ai/api/v1/chat/completions",
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
        content = choice.get('content') or ''
        return content
    except HTTPError as e:
        print(f"   ⚠️  LLM API error: {e.code} {e.read()[:200]}")
        return None
    except URLError as e:
        print(f"   ⚠️  LLM network error: {e}")
        return None


def main():
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  Fazenda de Agentes - DeepSeek Gratuito                            ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not openrouter_key:
        print("⚠️  OPENROUTER_API_KEY não configurada!")
        print("   O DeepSeek gratuito requer uma chave OpenRouter.")
        print("   Ou use o modelo direto no OpenCode via /models → opencode/deepseek-v4-flash-free")
        print()
    else:
        print(f"⚙️  Modelo: deepseek/deepseek-chat")
        print(f"⚙️  Provedor: OpenRouter")
        print()

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

    os.makedirs("deepseek/codigos", exist_ok=True)
    os.makedirs("deepseek/roteiros", exist_ok=True)

    for idx, task in enumerate(tasks):
        print(f"\n🤖 [{idx+1}] Iniciando: {task[:60]}...")

        system_prompt = """Você é um desenvolvedor sênior especializado em múltiplas linguagens.
Gere código limpo, documentado e pronto para produção.

Inclua:
- Código completo e funcional
- Comentários explicativos
- Instruções de instalação e uso
- Exemplos de uso"""

        user_prompt = f"""Tarefa: {task}

Desenvolva a solução completa com código, documentação e exemplos de uso."""

        llm_response = None
        if openrouter_key:
            llm_response = call_deepseek_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], openrouter_key)

        if not llm_response:
            print(f"❌ [{idx+1}] Sem resposta do DeepSeek")
            continue

        print(f"   📝 Resposta ({len(llm_response)} chars)")

        safe_name = re.sub(r'[^a-z0-9\s-]', '', task.lower().replace(' ', '-')[:40])
        arquivo_saida = f"deepseek/codigos/codigo_{idx+1}_{safe_name}.md"

        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            f.write(f"# Código Gerado - Agente {idx+1}\n\n")
            f.write(f"**Tarefa:** {task}\n\n")
            f.write(f"**Modelo:** DeepSeek v4 Flash (via OpenRouter/OpenCode)\n\n")
            f.write(f"**Código:**\n\n{llm_response}\n\n")
            f.write(f"---\n*Gerado pela Fazenda de Agentes OpenCode - DeepSeek Gratuito*\n")

        print(f"   💾 Código salvo em: {arquivo_saida}")

        # Commit
        subprocess.run(['git', 'add', '-A'], capture_output=True)
        commit_msg = f"feat(agent-{idx+1}): código DeepSeek - {task[:50]}"
        subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        subprocess.run(['git', 'push', 'origin', f"agent-{idx+1}-{safe_name}"], capture_output=True, text=True)

    print("\n✅ Criação de código DeepSeek concluída!")
    print("💻 Verifique a pasta deepseek/codigos/ para os códigos gerados.")


if __name__ == '__main__':
    main()