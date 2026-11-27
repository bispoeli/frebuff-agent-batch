/**
 * Dashboard da Fazenda de Agentes OpenCode
 * Gerencia todas as funcionalidades do dashboard
 */

// Configurações do repositório
const CONFIG = {
    owner: 'eli',
    repo: 'frebuff-agent-batch',
    baseURL: 'https://api.github.com/repos/bispoeli/frebuff-agent-batch',
    // Token será obtido do GitHub Actions ou pode ser adicionado manualmente
    token: null // Será preenchido via variável de ambiente ou input do usuário
};

// Estado da aplicação
const estado = {
    issues: [],
    workflows: [],
    estatisticas: {}
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    inicializarDashboard();
    configurarEventos();
});

function inicializarDashboard() {
    carregarDados();
    setInterval(carregarDados, 60000); // Atualizar a cada minuto
}

function configurarEventos() {
    // Formulário de nova issue
    const form = document.getElementById('form-nova-issue');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await criarIssue();
    });

    // Fechar modal ao clicar fora
    document.getElementById('modal-nova-issue').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modal-nova-issue')) {
            fecharModal();
        }
    });
}

// Carregar dados da API
async function carregarDados() {
    try {
        const [issuesResp, workflowsResp] = await Promise.all([
            fetch(`${CONFIG.API_BASE}/issues?state=all&per_page=50&sort=updated&direction=desc`, {
                headers: {
                    'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            }),
            fetch(`${CONFIG.API_BASE}/actions/workflows`, {
                headers: {
                    'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            })
        ]);

        if (!respostaOk(resposta)) throw new Error('Erro ao carregar issues');
        
        const issues = await resposta.json();
        const workflows = await (await fetch(`${CONFIG.API_BASE}/actions/workflows`, {
            headers: {
                'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        })).json();

        estado.issues = issues;
        estado.workflows = workflows;
        
        renderizarDashboard();
    } catch (erro) {
        console.error('Erro ao carregar dados:', erro);
        mostrarNotificacao('Erro ao carregar dados do GitHub', 'error');
    }
}

// Renderizar dashboard completo
function renderizarDashboard() {
    renderizarEstatisticas();
    renderizarIssues();
    renderizarWorkflows();
    renderizarAtividadeRecente();
}

// Renderizar estatísticas
function renderizarEstatisticas() {
    const total = estado.issues.length;
    const completas = estado.issues.filter(i => i.state === 'closed').length;
    const andamento = estado.issues.filter(i => i.state === 'open').length;
    const falhas = estado.issues.filter(i => 
        i.state === 'closed' && 
        i.labels.some(l => l.name.includes('erro') || l.name.includes('falha'))
    ).length;
    
    // Buscar PRs
    fetch(`${CONFIG.API_BASE}/pulls?state=all&per_page=100`, {
        headers: {
            'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
            'Accept': 'application/vnd.github.v3+json'
        }
    }).then(res => res.json()).then(prs => {
        document.getElementById('stat-prs').textContent = prs.length;
    }).catch(() => {});
    
    document.getElementById('stat-total-tarefas').textContent = total;
    document.getElementById('stat-concluidas').textContent = completas;
    document.getElementById('stat-andamento').textContent = andamento;
    document.getElementById('stat-falhas').textContent = falhas;
}

// Renderizar issues
function renderizarIssues() {
    const container = document.getElementById('issues-container');
    container.innerHTML = '';
    
    if (estado.issues.length === 0) {
        container.innerHTML = `
            <div class="estado-vazio">
                <i class="fas fa-inbox"></i>
                <p>Nenhuma issue encontrada</p>
            </div>
        `;
        return;
    }
    
    estado.issues.forEach(issue => {
        const item = document.createElement('div');
        item.className = 'item-issue';
        
        const data = new Date(issue.created_at).toLocaleDateString('pt-BR');
        const estadoEmoji = issue.state === 'open' ? '🟡' : '✅';
        const labelCor = obterCorLabel(issue.labels);
        
        item.innerHTML = `
            <div class="info-issue">
                <span class="badge estado-${issue.state}">${issue.state === 'open' ? 'ABERTO' : 'FECHADO'}</span>
                <h4>${issue.title}</h4>
                <div class="meta-issue">
                    <span><i class="fas fa-user"></i> ${issue.user.login}</span>
                    <span><i class="fas fa-calendar"></i> ${data}</span>
                    <span><i class="fas fa-comments"></i> ${issue.comments}</span>
                </div>
                <div class="etiquetas-issue">
                    ${issue.labels.map(l => `<span class="etiqueta" style="background-color:${l.color}; color:${obterCorTexto(l.color)}">${l.name}</span>`).join('')}
                </div>
            </div>
            <a href="${issue.html_url}" target="_blank" class="btn-link">Ver Issue <i class="fas fa-external-link-alt"></i></a>
        `;
        
        container.appendChild(item);
    });
}

// Renderizar workflows
function renderizarWorkflows() {
    const container = document.getElementById('workflows-container');
    container.innerHTML = '';
    
    if (estado.workflows.length === 0) {
        container.innerHTML = '<div class="estado-vazio"><i class="fas fa-tasks"></i><p>Nenhum workflow encontrado</p></div>';
        return;
    }
    
    estado.workflows.forEach(workflow => {
        const item = document.createElement('div');
        item.className = 'item-workflow';
        
        item.innerHTML = `
            <div class="info-workflow">
                <div class="info-workflow-info">
                    <h4>${workflow.name}</h4>
                    <span class="badge estado-${workflow.state}">${workflow.state}</span>
                </div>
                <div class="info-workflow-actions">
                    <a href="${workflow.html_url}" target="_blank" class="btn-link">Ver</a>
                    <button class="btn btn-small" onclick="executarWorkflow('${workflow.id}')">Executar</button>
                </div>
            </div>
        `;
        
        container.appendChild(item);
    });
}

// Renderizar atividade recente
function renderizarAtividadeRecente() {
    const container = document.getElementById('atividade-recente');
    const recentes = estado.issues.slice(0, 5);
    
    container.innerHTML = recentes.map(issue => `
        <div class="item-atividade">
            <div class="icone-atividade">
                <i class="fas ${issue.state === 'open' ? 'fa-plus-circle' : 'fa-check-circle'}"></i>
            </div>
            <div class="info-atividade">
                <div class="titulo-atividade">${issue.title}</div>
                <div class="meta-atividade">
                    <span>#${issue.number}</span>
                    <span>${new Date(issue.created_at).toLocaleDateString('pt-BR')}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Criar nova issue
async function criarIssue() {
    const titulo = document.getElementById('issue-titulo').value;
    const pilar = document.getElementById('issue-pilar').value;
    const modelo = document.getElementById('issue-modelo').value;
    const textoTarefas = document.getElementById('issue-tarefas').value;
    
    if (!titulo || !tarefasTexto) {
        mostrarNotificacao('Preencha todos os campos obrigatórios', 'error');
        return;
    }
    
    const corpo = `## Tarefas\n${tarefasTexto}\n\n## Modelo\n${modelo}\n\n## Opções\n- [x] Criar PR automático para cada tarefa\n- [x] Usar contexto limpo`;
    
    try {
        const resposta = await fetch(`${CONFIG.API_BASE}/issues`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: titulo,
                body: corpo,
                labels: [pilar]
            })
        });
        
        if (resposta.ok) {
            mostrarNotificacao('Issue criada com sucesso!', 'sucesso');
            document.getElementById('form-nova-issue').reset();
            fecharModal();
            carregarDados();
        } else {
            mostrarNotificacao('Erro ao criar issue', 'error');
        }
    } catch (erro) {
        mostrarNotificacao('Erro ao criar issue', 'error');
    }
}

// Executar workflow manualmente
async function executarWorkflow(workflowId) {
    try {
        const resposta = await fetch(`${CONFIG.API_BASE}/actions/workflows/${workflowId}/dispatches`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${CONFIG.GITHUB_TOKEN || ''}`,
                'Accept': 'application/vnd.github.v3+json'
            },
            body: JSON.stringify({})
        });
        
        if (resposta.ok) {
            mostrarNotificacao('Workflow executado com sucesso!', 'sucesso');
            carregarDados();
        } else {
            mostrarNotificacao('Erro ao executar workflow', 'error');
        }
    } catch (erro) {
        mostrarNotificacao('Erro ao executar workflow', 'error');
    }
}

// Auxiliares
function obterCorLabel(labels) {
    if (labels.length === 0) return '#6b7280';
    return labels[0].color ? `#${labels[0].color}` : '#6b7280';
}

function obterCorTexto(corHex) {
    if (!corHex) return '#ffffff';
    const r = parseInt(corHex.substring(0, 2), 16);
    const g = parseInt(corHex.substring(2, 4), 16);
    const b = parseInt(corHex.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

function respostaOk(response) {
    return response.ok;
}

function mostrarNotificacao(mensagem, tipo = 'sucesso') {
    const toast = document.getElementById('toast');
    const texto = document.getElementById('toast-msg');
    texto.textContent = mensagem;
    toast.className = `toast ${tipo}`;
    toast.classList.add('mostrar');
    
    setTimeout(() => {
        toast.classList.remove('mostrar');
    }, 3000);
}

function abrirModalNovaIssue() {
    document.getElementById('modal-nova-issue').style.display = 'block';
}

function fecharModal() {
    document.getElementById('modal-nova-issue').style.display = 'none';
    document.getElementById('form-nova-issue').reset();
}