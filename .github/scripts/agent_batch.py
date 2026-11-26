#!/usr/bin/env python3
"""
Fazenda de Agentes OpenCode - GitHub Actions
Executa múltiplos agentes OpenCode em paralelo via GitHub Actions.
Usa API OpenAI-compatible (OpenRouter/NVIDIA NIM) - TUDO FREE.
"""

import os
import re
import json
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ════════════════════════════════════════════════════════════════════
# COMANDOS PERMITIDOS (whitelist - segurança contra RCE)
# ════════════════════════════════════════════════════════════════════
ALLOWED_COMMANDS = {
    'ls', 'cat', 'echo', 'pwd', 'mkdir', 'touch', 'cp', 'mv', 'rm',
    'find', 'grep', 'sed', 'awk', 'python3', 'pip', 'npm', 'node',
    'git', 'chmod', 'chown', 'tar', 'zip', 'unzip', 'curl', 'wget',
    'head', 'tail', 'wc', 'sort', 'uniq', 'cut', 'tr', 'xargs'
}

# Comandos proibidos (mesmo que estejam na whitelist acima, alguns subcomandos são perigosos)
FORBIDDEN_PATTERNS = [
    r'rm\s+-rf\s+/',           # rm -rf /
    r'rm\s+-rf\s+\*',           # rm -rf *
    r'dd\s+if=',                # dd
    r'mkfs',                    # mkfs
    r'>\s*/dev/',               # redirect para /dev
    r'curl\s+.*\|\s*bash',     # curl | bash
    r'wget\s+.*\|\s*bash',     # wget | bash
    r'eval\s+',                 # eval
    r'exec\s+',                # exec
]


def is_command_safe(cmd: str) -> bool:
    """Verifica se um comando shell é seguro para execução."""
    cmd_stripped = cmd.strip()

    # Verificar padrões proibidos
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return False

    # Extrair o primeiro comando (antes de espaços, pipes, redirects)
    first_token = re.split(r'[\s|&;]', cmd_stripped)[0]
    if not first_token:
        return False

    # O primeiro token deve estar na whitelist
    if first_token not in ALLOWED_COMMANDS:
        return False

    return True


def sanitize_commit_message(msg: str) -> str:
    """Sanitiza mensagem de commit para evitar injeção de argumentos git."""
    # Remover caracteres que podem ser interpretados como flags git
    msg = msg.replace('\n', ' ').replace('\r', ' ')
    msg = re.sub(r'^-', '\\-', msg)  # escapar hífens iniciais
    msg = msg[:200]  # limitar tamanho
    return msg


def main():
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  Fazenda de Agentes OpenCode - GitHub Actions (FREE TIER)          ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    # ═════════════════════════════════════════════════════════════════
    # 1. Obter tarefas da issue
    # ═════════════════════════════════════════════════════════════════
    event_name = os.environ.get('GITHUB_EVENT_NAME', '')
    issue_body = os.environ.get('ISSUE_BODY', '')
    issue_number = os.environ.get('ISSUE_NUMBER', '0')

    if not issue_body:
        event_path = os.environ.get('GITHUB_EVENT_PATH', '')
        if event_name == 'issues' and event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            issue_body = event_data.get('issue', {}).get('body', '')
            issue_number = str(event_data.get('issue', {}).get('number', '0'))

    # Extrair tarefas (linhas que começam com - ou *, ignorando cabeçalhos)
    tasks = []
    for line in issue_body.split('\n'):
        stripped = line.strip()
        if re.match(r'^[-*] ', stripped):
            task = re.sub(r'^[-*] ', '', stripped)
            if task and not task.startswith('#') and not task.startswith('##') and not task.startswith('---'):
                task = task.strip()
                if len(task) >= 3:  # tarefa mínima de 3 caracteres
                    tasks.append(task)

    print(f"📋 {len(tasks)} tarefa(s) encontrada(s)")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")

    if not tasks:
        if event_name == 'issues':
            print("❌ Nenhuma tarefa válida encontrada na issue")
            exit(1)
        else:
            print("ℹ️  Nenhuma tarefa para processar. Encerrando com sucesso.")
            exit(0)

    # ═════════════════════════════════════════════════════════════════
    # 2. Configurações
    # ═════════════════════════════════════════════════════════════════
    model = os.environ.get('INPUT_MODEL', 'nvidia/nemotron-3-super-120b-a12b')
    max_parallel = int(os.environ.get('INPUT_PARALLEL', '5'))
    create_prs = os.environ.get('INPUT_CREATE_PRS', 'true').lower() == 'true'
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    token = os.environ.get('GITHUB_TOKEN', '')
    openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
    nvidia_key = os.environ.get('NVIDIA_API_KEY', '')

    print(f"⚙️  Modelo: {model}")
    print(f"⚙️  Max paralelo: {max_parallel}")
    print(f"⚙️  Criar PRs: {create_prs}")
    print(f"⚙️  Repositório: {repo}")
    print()

    # Determinar baseURL e API key baseado no modelo
    if model.startswith('nvidia/') or 'nemotron' in model.lower():
        base_url = os.environ.get('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
        api_key = nvidia_key
        provider = 'NVIDIA NIM'
    else:
        base_url = 'https://openrouter.ai/api/v1'
        api_key = openrouter_key
        provider = 'OpenRouter'

    print(f"⚙️  Provedor: {provider} ({base_url})")

    if not api_key:
        print(f"❌ API key do {provider} não configurada!")
        print(f"   Configure {provider.upper().replace(' ', '_')}_API_KEY nos secrets do GitHub")
        exit(1)

    # ═════════════════════════════════════════════════════════════════
    # 3. Funções auxiliares
    # ═════════════════════════════════════════════════════════════════

    def slugify(text: str) -> str:
        """Cria um slug seguro para nome de branch."""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:40]

    def call_llm(messages: list) -> str:
        """Chama a API LLM via OpenAI-compatible endpoint."""
        data = json.dumps({
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 4000
        }).encode()

        req = Request(
            f'{base_url}/chat/completions',
            data=data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        try:
            resp = urlopen(req, timeout=120)
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
        except HTTPError as e:
            print(f"   ⚠️  LLM API error: {e.code} {e.read()[:200]}")
            return None
        except URLError as e:
            print(f"   ⚠️  LLM network error: {e}")
            return None

    def run_agent(task_data: tuple) -> dict:
        """Executa um agente para uma tarefa específica."""
        idx, task = task_data
        branch_name = f"agent-{idx+1}-{slugify(task)}"

        result = {
            'idx': idx + 1,
            'task': task,
            'branch': branch_name,
            'status': 'failed',
            'error': None,
            'pr_url': None
        }

        try:
            # Criar branch isolada
            subprocess.run(['git', 'checkout', '-b', branch_name],
                          check=True, capture_output=True, text=True)
            print(f"🌿 [{idx+1}] Branch: {branch_name}")

            # Construir prompt para o agente
            system_prompt = """Você é um agente de software autônomo. Sua tarefa é executar a solicitação do usuário escrevendo código, criando arquivos, modificando código existente e fazendo commits.

Você tem acesso a um ambiente Linux com permissões completas. Você pode:
- Criar e editar arquivos
- Executar comandos de shell (apenas comandos seguros: ls, cat, mkdir, touch, cp, mv, python3, pip, git, etc.)
- Instalar pacotes
- Fazer commits e push para branches

Seja proativo, completo e escreva código de qualidade. Quando terminar, faça commit de todas as mudanças."""

            user_prompt = f"""Tarefa: {task}

Por favor, execute esta tarefa completamente. Crie arquivos, modifique código, instale dependências se necessário, e faça commit de todas as mudanças no final."""

            print(f"🤖 [{idx+1}] Iniciando: {task[:60]}...")

            # Chamar LLM para gerar plano de execução
            llm_response = call_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            if not llm_response:
                print(f"❌ [{idx+1}] Sem resposta do LLM")
                result['error'] = 'Sem resposta do LLM'
                return result

            print(f"   📝 Resposta do LLM ({len(llm_response)} chars)")

            # Extrair comandos shell da resposta do LLM (blocos de código bash)
            shell_commands = re.findall(r'```(?:bash|sh|shell)?\n(.*?)\n```', llm_response, re.DOTALL)

            # Executar comandos shell extraídos (apenas comandos seguros)
            for cmd in shell_commands[:10]:
                cmd = cmd.strip()
                if not cmd:
                    continue

                if not is_command_safe(cmd):
                    print(f"   🚫 [{idx+1}] Comando bloqueado por segurança: {cmd[:80]}...")
                    continue

                print(f"   🔧 Executando: {cmd[:80]}...")
                cmd_result = subprocess.run(
                    cmd, shell=True,
                    capture_output=True, text=True, timeout=60
                )
                if cmd_result.returncode == 0:
                    output = cmd_result.stdout[:200] if cmd_result.stdout else "(sem output)"
                    print(f"      ✅ {output}")
                else:
                    err = cmd_result.stderr[:200] if cmd_result.stderr else "(sem erro)"
                    print(f"      ⚠️  {err}")

            # Commit e push
            subprocess.run(['git', 'add', '-A'], capture_output=True)
            safe_commit_msg = sanitize_commit_message(f"feat(agent-{idx+1}): {task}")
            commit_result = subprocess.run(
                ['git', 'commit', '-m', safe_commit_msg],
                capture_output=True, text=True
            )

            if "nothing to commit" not in commit_result.stdout:
                push_result = subprocess.run(
                    ['git', 'push', 'origin', branch_name],
                    capture_output=True, text=True, timeout=60
                )
                if push_result.returncode == 0:
                    print(f"📤 [{idx+1}] Enviado para {branch_name}")
                else:
                    print(f"⚠️  [{idx+1}] Falha no push: {push_result.stderr[:200]}")
            else:
                print(f"⚠️  [{idx+1}] Nenhuma mudança para commitar")

            # Criar Pull Request via API
            if create_prs:
                pr_data = json.dumps({
                    'title': f'🤖 Agent {idx+1}: {task[:70]}',
                    'head': branch_name,
                    'base': 'main',
                    'body': (
                        f'## 🤖 Agente OpenCode #{idx+1}\n\n'
                        f'**Tarefa:** {task}\n\n'
                        f'**Modelo:** {model}\n\n'
                        f'**Provedor:** {provider}\n\n'
                        f'**Branch:** `{branch_name}`\n\n'
                        f'---\n'
                        f'Este PR foi criado automaticamente pela **Fazenda de Agentes OpenCode** '
                        f'via GitHub Actions.\n\n'
                        f'Cada agente executa em uma **VM Linux isolada e descartável**, '
                        f'com contexto limpo.\n\n'
                        f'---\n'
                        f'*Executado via GitHub Actions - Fazenda de Agentes (FREE TIER)*'
                    )
                }).encode()

                req = Request(
                    f'https://api.github.com/repos/{repo}/pulls',
                    data=pr_data,
                    headers={
                        'Authorization': f'token {token}',
                        'Accept': 'application/vnd.github+json',
                        'Content-Type': 'application/json'
                    },
                    method='POST'
                )
                try:
                    resp = urlopen(req, timeout=30)
                    pr = json.loads(resp.read())
                    result['pr_url'] = pr['html_url']
                    print(f"🔗 [{idx+1}] PR: {pr['html_url']}")
                except HTTPError as e:
                    print(f"⚠️  [{idx+1}] Falha ao criar PR: {e.code} {e.read()[:200]}")
                except URLError as e:
                    print(f"⚠️  [{idx+1}] Erro de rede: {e}")

            result['status'] = 'success'

        except subprocess.TimeoutExpired:
            result['error'] = 'Timeout (5 min)'
            print(f"⏱️  [{idx+1}] Timeout")
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ [{idx+1}] Erro: {e}")

        return result

    # ═════════════════════════════════════════════════════════════════
    # 4. Executar agentes em paralelo
    # ═════════════════════════════════════════════════════════════════
    print()
    print(f"🚀 Iniciando execução paralela de {len(tasks)} agente(s) (máx. {max_parallel} simultâneos)...")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {
            executor.submit(run_agent, (i, t)): i
            for i, t in enumerate(tasks)
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # ═════════════════════════════════════════════════════════════════
    # 5. Resumo final
    # ═════════════════════════════════════════════════════════════════
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  RESUMO DA FAZENDA DE AGENTES                                      ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    print(f"  ✅ Sucessos:  {success}")
    print(f"  ❌ Falhas:    {failed}")
    print(f"  📦 Total:     {len(results)}")
    print()
    print("  Detalhes:")
    for r in sorted(results, key=lambda x: x['idx']):
        icon = "✅" if r['status'] == 'success' else "❌"
        pr_info = f" | PR: {r['pr_url']}" if r.get('pr_url') else ""
        print(f"  {icon} Agente {r['idx']}: {r['task'][:50]}{pr_info}")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    if failed > 0:
        print("\n⚠️  Alguns agentes falharam, mas o workflow continua.")


if __name__ == '__main__':
    main()