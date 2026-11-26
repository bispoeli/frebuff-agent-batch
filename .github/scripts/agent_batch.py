#!/usr/bin/env python3
"""
Fazenda de Agentes OpenCode - GitHub Actions
Executa múltiplos agentes OpenCode em paralelo via GitHub Actions.
"""

import os
import re
import json
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def main():
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  Fazenda de Agentes OpenCode - GitHub Actions                      ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    # Obter tarefas da issue
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
                tasks.append(task.strip())

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

    # Configurações
    model = os.environ.get('INPUT_MODEL', 'opencode/deepseek-v4.1-flash-free')
    max_parallel = int(os.environ.get('INPUT_PARALLEL', '5'))
    create_prs = os.environ.get('INPUT_CREATE_PRS', 'true').lower() == 'true'
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    token = os.environ.get('GITHUB_TOKEN', '')

    print(f"⚙️  Modelo: {model}")
    print(f"⚙️  Max paralelo: {max_parallel}")
    print(f"⚙️  Criar PRs: {create_prs}")
    print(f"⚙️  Repositório: {repo}")
    print()

    # Configurar Hermes Agent
    print("⚙️  Configurando Hermes Agent...")
    setup_result = subprocess.run([
        'hermes', 'setup', '--non-interactive',
        '--provider', 'openrouter',
        '--model', 'opencode/deepseek-v4.1-flash-free',
        '--api-key', os.environ.get('OPENROUTER_API_KEY', '')
    ], capture_output=True, text=True)
    if setup_result.returncode != 0:
        print(f"   ⚠️  Aviso na configuração: {setup_result.stderr[:200]}")
    else:
        print("   ✅ Hermes configurado")

    def slugify(text):
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:40]

    def run_agent(task_data):
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
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                          check=True, capture_output=True, text=True)
            print(f"🌿 [{idx+1}] Branch: {branch_name}")
            
            print(f"🤖 [{idx+1}] Iniciando: {task[:60]}...")
            agent_result = subprocess.run([
                'hermes', 'chat', '--no-restore-cwd', '--yolo',
                '-m', model, task
            ], capture_output=True, text=True, timeout=300)
            
            if agent_result.returncode == 0:
                print(f"✅ [{idx+1}] Concluído com sucesso")
            else:
                print(f"⚠️  [{idx+1}] Código {agent_result.returncode}")
                if agent_result.stderr:
                    print(f"   stderr: {agent_result.stderr[:200]}")
            
            subprocess.run(['git', 'add', '-A'], capture_output=True)
            commit_msg = f"feat(agent-{idx+1}): {task}"
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
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
            
            if create_prs:
                pr_data = json.dumps({
                    'title': f'🤖 Agent {idx+1}: {task[:70]}',
                    'head': branch_name,
                    'base': 'main',
                    'body': (
                        f'## 🤖 Agente OpenCode #{idx+1}\n\n'
                        f'**Tarefa:** {task}\n\n'
                        f'**Modelo:** {model}\n\n'
                        f'**Branch:** `{branch_name}`\n\n'
                        f'---\n'
                        f'Este PR foi criado automaticamente pela **Fazenda de Agentes OpenCode** '
                        f'via GitHub Actions.\n\n'
                        f'Cada agente executa em uma **VM Linux isolada e descartável**, '
                        f'com contexto limpo.\n\n'
                        f'---\n'
                        f'*Executado via GitHub Actions*'
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

    # Executar agentes em paralelo
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

    # Resumo final
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