# Especificação - App de Orçamento e Planilha Financeira

## Visão Geral
Aplicativo móvel para gestão financeira pessoal e empresarial. Permite cadastro de despesas, receitas, relatórios mensais e exportação de dados.

## Telas

### 1. Dashboard Financeiro
- Saldo atual
- Receitas do mês
- Despesas do mês
- Gráfico de pizza (categorias)
- Últimas transações

### 2. Cadastro de Receita
- Descrição
- Valor
- Categoria (salário, bônus, investimento, etc.)
- Data
- Forma de pagamento

### 3. Cadastro de Despesa
- Descrição
- Valor
- Categoria (alimentação, transporte, moradia, lazer, etc.)
- Data
- Forma de pagamento
- Comprovante (foto opcional)

### 4. Relatório Mensal
- Seleção de mês/ano
- Total de receitas
- Total de despesas
- Saldo líquido
- Gráfico de barras (receitas vs despesas)

### 5. Categorias
- Criar nova categoria
- Editar categoria existente
- Excluir categoria (se não houver transações vinculadas)

## Tecnologias Sugeridas
- Flutter (Android/iOS)
- SQLite (banco local)
- Provider (gerenciamento de estado)
- syncfusion_flutter_charts (gráficos)

## Regras de Negócio
- Saldo = Receitas - Despesas
- Categoria não pode ser excluída se houver transações
- Comprovante opcional para despesas
- Exportação em CSV/Excel

## Integração com Planilhas
- Importar do Excel/Google Sheets
- Exportar para Excel/Google Sheets
- Sincronização com Google Drive (opcional)