# Especificação - App de Gestão para Bandas/Orquestras

## Visão Geral
Aplicativo móvel para gestão de bandas musicais, orquestras e grupos musicais. Permite cadastro de músicos, gerenciamento de repertório, controle de cache por show e agenda de ensaios.

## Telas

### 1. Tela Inicial (Dashboard)
- Lista de shows agendados
- Próximos eventos
- Estatísticas rápidas (total de músicos, shows no mês, faturamento)

### 2. Cadastro de Músicos
- Nome completo
- Instrumento
- Telefone
- Email
- Função (vocal, guitarra, bateria, etc.)

### 3. Repertório
- Nome da música
- Artista original
- Gênero
- Duração
- Acordes/link para partitura

### 4. Setlists
- Nome da setlist
- Músicas incluídas
- Show associado

### 5. Cache por Show
- Nome do evento
- Data e hora
- Local
- Valor acordado
- Status (pendente, realizado, cancelado)

### 6. Despesas
- Tipo (transporte, alimentação, equipamento)
- Valor
- Data
- Comprovante (foto)

## Tecnologias Sugeridas
- Flutter (Android/iOS)
- SQLite (banco local)
- Provider (gerenciamento de estado)

## Regras de Negócio
- Um músico pode tocar em múltiplas setlists
- Um show pode ter múltiplos músicos
- Cache por show deve somar automaticamente as despesas