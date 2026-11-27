#!/usr/bin/env python3
"""
MAESTRO - Orquestrador de Agentes Autônomos
Suporta múltiplos provedores: NVIDIA NIM, OpenRouter/DeepSeek, Ollama
Executa tarefas em paralelo com rate limiting inteligente
"""

import os
import re
import json
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


PROVIDERS = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_env": "NVIDIA_API_KEY",
        "models": [
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "nvidia/nemotron-3-super-120b-a12b",
        ],
        "rate_limit_rpm": 40,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "models": [
            "deepseek/deepseek-chat",
            "deepseek/deepseek-coder",
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
        ],
        "rate_limit_rpm": 20,
    },
}

rate_limit_state = {
    "nvidia": {"last_reset": 0, "count": 0, "limit": 40},
    "openrouter": {"last_reset": 0, "count": 0, "limit": 20},
}


def get_provider_for_model(model: str) -> str:
    if model.startswith("nvidia/"):
        return "nvidia"
    return "openrouter"


def check_rate_limit(provider: str) -> bool:
    now = time.time()
    state = rate_limit_state[provider]
    if now - state["last_reset"] > 60:
        state["last_reset"] = now
        state["count"] = 0
    if state["count"] >= state["limit"]:
        return False
    state["count"] += 1
    return True


def wait_for_rate_limit(provider: str):
    while not check_rate_limit(provider):
        time.sleep(5)


def call_llm(messages: list, model: str, provider: str = None, api_key: str = None) -> str:
    if provider is None:
        provider = get_provider_for_model(model)
    config = PROVIDERS[provider]
    if not api_key:
        api_key = os.environ.get(config["api_key_env"], "")
    if not api_key:
        print(f"   ⚠️  API key não configurada para {provider}")
        return None
    wait_for_rate_limit(provider)
    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 8000,
    }).encode()
    req = Request(
        f"{config['base_url']}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        resp = urlopen(req, timeout=120)
        result = json.loads(resp.read())
        choice = result["choices"][0]["message"]
        content = choice.get("content") or choice.get("reasoning_content") or ""
        return content
    except HTTPError as e:
        print(f"   ⚠️  LLM API error ({provider}): {e.code} {e.read()[:200]}")
        return None
    except URLError as e:
        print(f"   ⚠️  LLM network error: {e}")
        return None


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:40]


def is_command_safe(cmd: str) -> bool:
    cmd_stripped = cmd.strip()
    FORBIDDEN = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+\*",
        r"dd\s+if=",
        r"mkfs",
        r">\s*/dev/",
        r"curl\s+.*\|\s*bash",
        r"wget\s+.*\|\s*bash",
        r"eval\s+",
        r"exec\s+",
    ]
    for pattern in FORBIDDEN:
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return False
    first_token = re.split(r"[\s|&;]", cmd_stripped)[0]
    if not first_token:
        return False
    ALLOWED = {
        "ls",
        "cat",
        "echo",
        "pwd",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "rm",
        "find",
        "grep",
        "sed",
        "awk",
        "python3",
        "pip",
        "npm",
        "node",
        "git",
        "chmod",
        "chown",
        "tar",
        "zip",
        "unzip",
        "curl",
        "wget",
        "head",
        "tail",
        "wc",
        "sort",
        "uniq",
        "cut",
        "tr",
        "xargs",
    }
    return first_token in ALLOWED


def sanitize_commit_message(msg: str) -> str:
    msg = msg.replace("\n", " ").replace("\r", " ")
    msg = re.sub(r"^-", "\\-", msg)
    return msg[:200]


def run_agent(task_data: tuple) -> dict:
    idx, task = task_data
    branch_name = f"agent-{idx+1}-{slugify(task)}"

    result = {
        "idx": idx + 1,
        "task": task,
        "branch": branch_name,
        "status": "failed",
        "error": None,
        "pr_url": None,
    }

    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"🌿 [{idx+1}] Branch: {branch_name}")

        system_prompt = """Você é um agente de software autônomo sênior. Sua tarefa é executar a solicitação do usuário escrevendo código, criando arquivos, modificando código existente e fazendo commits.

Você tem acesso a um ambiente Linux com permissões completas. Você pode:
- Criar e editar arquivos
- Executar comandos de shell (apenas comandos seguros: ls, cat, mkdir, touch, cp, mv, python3, pip, git, etc.)
- Instalar pacotes
- Fazer commits e push para branches

Seja proativo, completo e escreva código de qualidade. Quando terminar, faça commit de todas as mudanças."""

        user_prompt = f"""Tarefa: {task}

Por favor, execute esta tarefa completamente. Crie arquivos, modifique código, instale dependências se necessário, e faça commit de todas as mudanças no final."""

        print(f"🤖 [{idx+1}] Iniciando: {task[:60]}...")

        llm_response = call_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model,
            provider,
            api_key,
        )

        if not llm_response:
            print(f"❌ [{idx+1}] Sem resposta do LLM")
            result["error"] = "Sem resposta do LLM"
            return result

        print(f"   📝 Resposta ({len(llm_response)} chars)")

        shell_commands = re.findall(r"```(?:bash|sh|shell)?\n(.*?)\n```", llm_response, re.DOTALL)

        for cmd in shell_commands[:10]:
            cmd = cmd.strip()
            if not cmd:
                continue

            if not is_command_safe(cmd):
                print(f"   🚫 [{idx+1}] Comando bloqueado: {cmd[:80]}...")
                continue

            print(f"   🔧 [{idx+1}] Executando: {cmd[:80]}...")
            cmd_result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            if cmd_result.returncode == 0:
                output = cmd_result.stdout[:200] if cmd_result.stdout else "(sem output)"
                print(f"      ✅ {output}")
            else:
                err = cmd_result.stderr[:200] if cmd_result.stderr else "(sem erro)"
                print(f"      ⚠️  {err}")

        subprocess.run(["git", "add", "-A"], capture_output=True)
        safe_commit_msg = sanitize_commit_message(f"feat(agent-{idx+1}): {task}")
        commit_result = subprocess.run(
            ["git", "commit", "-m", safe_commit_msg],
            capture_output=True,
            text=True,
        )

        if "nothing to commit" not in commit_result.stdout:
            push_result = subprocess.run(
                ["git", "push", "origin", branch_name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if push_result.returncode == 0:
                print(f"📤 [{idx+1}] Enviado para {branch_name}")
                result["branch"] = branch_name
            else:
                print(f"⚠️  [{idx+1}] Falha no push: {push_result.stderr[:200]}")
        else:
            print(f"⚠️  [{idx+1}] Nenhuma mudança para commitar")

        if create_prs:
            pr_data = json.dumps(
                {
                    "title": f"🤖 Agent {idx+1}: {task[:70]}",
                    "head": branch_name,
                    "base": "main",
                    "body": (
                        f"## 🤖 Agente OpenCode #{idx+1}\n\n"
                        f"**Tarefa:** {task}\n\n"
                        f"**Modelo:** {model}\n\n"
                        f"**Provedor:** {provider}\n\n"
                        f"**Branch:** `{branch_name}`\n\n"
                        f"---\n"
                        f"Este PR foi criado automaticamente pela **Fazenda de Agentes OpenCode** "
                        f"via GitHub Actions.\n\n"
                        f"Cada agente executa em uma **VM Linux isolada e descartável**, "
                        f"com contexto limpo.\n\n"
                        f"---\n*Executado via GitHub Actions - Fazenda de Agentes (FREE TIER)*"
                    ),
                }).encode()

            req = Request(
                f"https://api.github.com/repos/{repo}/pulls",
                data=pr_data,
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                resp = urlopen(req, timeout=30)
                pr = json.loads(resp.read())
                result["pr_url"] = pr["html_url"]
                print(f"🔗 [{idx+1}] PR: {pr['html_url']}")
            except HTTPError as e:
                print(f"⚠️  [{idx+1}] Falha ao criar PR: {e.code} {e.read()[:200]}")
            except URLError as e:
                print(f"⚠️  [{idx+1}] Erro de rede: {e}")

        result["status"] = "success"

    except subprocess.TimeoutExpired:
        result["error"] = "Timeout (5 min)"
        print(f"⏱️  [{idx+1}] Timeout")
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ [{idx+1}] Erro: {e}")

    return result


def main():
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  Fazenda de Agentes OpenCode - GitHub Actions (FREE TIER)          ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_number = os.environ.get("ISSUE_NUMBER", "0")

    if not issue_body:
        event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        if event_name == "issues" and event_path and os.path.exists(event_path):
            with open(event_path, "r") as f:
                event_data = json.load(f)
            issue_body = event_data.get("issue", {}).get("body", "")
            issue_number = str(event_data.get("issue", {}).get("number", "0"))

    tasks = []
    for line in issue_body.split("\n"):
        stripped = line.strip()
        if re.match(r"^[-*] ", stripped):
            task = re.sub(r"^[-*] ", "", stripped)
            if task and not task.startswith("#") and not task.startswith("##") and not task.startswith("---"):
                task = task.strip()
                if len(task) >= 3:
                    tasks.append(task)

    print(f"📋 {len(tasks)} tarefa(s) encontrada(s)")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")

    if not tasks:
        if event_name == "issues":
            print("❌ Nenhuma tarefa válida encontrada na issue")
            exit(1)
        else:
            print("ℹ️  Nenhuma tarefa para processar.")
            exit(0)

    model = os.environ.get("INPUT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    max_parallel = int(os.environ.get("INPUT_PARALLEL", "5"))
    create_prs = os.environ.get("INPUT_CREATE_PRS", "true").lower() == "true"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    provider = get_provider_for_model(model)
    api_key = os.environ.get(PROVIDERS[provider]["api_key_env"], "")

    print(f"⚙️  Modelo: {model}")
    print(f"⚙️  Provedor: {provider}")
    print(f"⚙️  Max paralelo: {max_parallel}")
    print(f"⚙️  Criar PRs: {create_prs}")
    print(f"⚙️  Repositório: {repo}")
    print()

    if not api_key:
        print(f"❌ API key não configurada para {provider}!")
        exit(1)

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

    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  RESUMO DA FAZENDA DE AGENTES                                      ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"  ✅ Sucessos:  {success}")
    print(f"  ❌ Falhas:    {failed}")
    print(f"  📦 Total:     {len(results)}")
    print()
    print("  Detalhes:")
    for r in sorted(results, key=lambda x: x["idx"]):
        icon = "✅" if r["status"] == "success" else "❌"
        pr_info = f" | PR: {r['pr_url']}" if r.get("pr_url") else ""
        print(f"  {icon} Agente {r['idx']}: {r['task'][:50]}{pr_info}")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    if failed > 0:
        print("\n⚠️  Alguns agentes falharam, mas o workflow continua.")


if __name__ == "__main__":
    main()
