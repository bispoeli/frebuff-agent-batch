#!/usr/bin/env python3
"""
Transcrição Agent - YouTube → HTML/Livro
Gera eBooks técnicos em HTML a partir de vídeos do YouTube.
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
    print("║  Fazenda de Agentes - Transcrição YouTube → HTML/Livro            ║")
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

    # Extrair URLs do YouTube e tarefas
    urls = re.findall(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', issue_body)
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

    if urls:
        print(f"🔗 {len(urls)} URL(s) do YouTube detectada(s)")
        for i, u in enumerate(urls):
            print(f"   {i+1}. https://www.youtube.com/watch?v={u}")

    if not tasks and not urls:
        print("❌ Nenhuma tarefa ou URL válida encontrada")
        exit(1)

    os.makedirs("transcricao/ebooks", exist_ok=True)

    for idx, task in enumerate(tasks):
        print(f"\n🤖 [{idx+1}] Iniciando: {task[:60]}...")

        # Extrair URL da YouTube se houver na tarefa
        url_match = re.search(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', task)
        video_url = f"https://www.youtube.com/watch?v={url_match.group(1)}" if url_match else None

        system_prompt = """Você é um especialista em transcrição e criação de eBooks técnicos.
Sua função é transformar conteúdo de vídeo do YouTube em um eBook completo em HTML.

Inclua:
- Título do eBook
- Sumário
- Resumo executivo
- Capítulos organizados
- Citações importantes
- Conclusão
- Recursos adicionais

O HTML deve ser semanticamente correto, responsivo e com design profissional."""

        user_prompt = f"""Tarefa: {task}
        {"Vídeo YouTube: " + video_url if video_url else ""}

Crie um eBook completo em HTML baseado nesta tarefa/vídeo."""

        llm_response = call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], nvidia_key)

        if not llm_response:
            print(f"❌ [{idx+1}] Sem resposta do LLM")
            continue

        print(f"   📝 Resposta ({len(llm_response)} chars)")

        safe_name = re.sub(r'[^a-z0-9\s-]', '', task.lower().replace(' ', '-')[:40])
        ebook_file = f"transcricao/ebooks/ebook_{idx+1}_{safe_name}.html"

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBook - {task[:60]}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; }}
        h3 {{ color: #16a085; }}
        .highlight {{ background: #f9e79f; padding: 2px 5px; border-radius: 3px; }}
        code {{ background: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #3498db; margin: 20px 0; padding-left: 20px; font-style: italic; }}
        .footer {{ margin-top: 50px; border-top: 1px solid #bdc3c7; padding-top: 20px; font-size: 0.9em; color: #7f8c8d; }}
    </style>
</head>
<body>
<h1>eBook: {task[:80]}</h1>

{llm_response}

<div class="footer">
    <p>Gerado pela Fazenda de Agentes OpenCode - NVIDIA NIM</p>
    <p>Fonte: {video_url if video_url else 'Tarefa via issue'}</p>
</div>
</body>
</html>"""

        with open(ebook_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"   💾 eBook salvo em: {ebook_file}")

        # Commit
        subprocess.run(['git', 'add', '-A'], capture_output=True)
        commit_msg = f"feat(agent-{idx+1}): eBook - {task[:50]}"
        subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        subprocess.run(['git', 'push', 'origin', f"agent-{idx+1}-{safe_name}"], capture_output=True, text=True)

    print("\n✅ Transcrição concluída!")
    print("📚 Verifique a pasta transcricao/ebooks/ para os eBooks gerados.")


if __name__ == '__main__':
    main()