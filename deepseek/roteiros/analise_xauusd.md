# Roteiro de Análise XAUUSD - DeepSeek Gratuito

## Objetivo
Utilizar o modelo DeepSeek v4 Flash (gratuito via OpenCode) para gerar análises técnicas de XAUUSD (Ouro) baseadas em dados históricos e em tempo real.

## Fluxo de Trabalho

1. **Coleta de dados**: Obter dados OHLCV do XAUUSD (via MT5 ou API pública)
2. **Análise técnica**: Calcular indicadores (RSI, MACD, Bollinger Bands, Médias Móveis)
3. **Geração de sinal**: O agente DeepSeek analisa e sugere direção (BUY/SELL/NEUTRO)
4. **Relatório**: Gerar relatório em Markdown com recomendação e justificativa

## Exemplo de Prompt para o Agente DeepSeek

```
Você é um trader sênior especializado em XAUUSD (Ouro).

Analise os seguintes dados de mercado:
- Preço atual: 2650.50
- RSI(14): 65.50
- SMA(20): 2648.20
- Bollinger Superior: 2660.00
- Bollinger Inferior: 2635.00
- Volume: Alto

Responda em português com:
1. Direção (BUY/SELL/NEUTRO)
2. Nível de entrada sugerido
3. Stop Loss (pips)
4. Take Profit (pips)
5. Confiança (0-100%)
6. Justificativa técnica

Não execute ordens. Apenas analise e sugira.
```

## Exemplo de Saída Esperada

```
## Análise XAUUSD - M5

**Direção:** BUY
**Entrada:** 2650.50
**Stop Loss:** 2645.00 (50 pips)
**Take Profit:** 2665.00 (150 pips)
**Confiança:** 75%

**Justificativa:**
O preço está acima da Média Móvel de 20 períodos, indicando tendência de alta de curto prazo. O RSI de 65.50 mostra força compradora, mas ainda não está em zona de sobrecompra (acima de 70). O preço está respeitando a Banda Inferior de Bollinger como suporte dinâmico.

Recomendação: Entrada comprada com gestão de risco rigorosa.
```

## Como Usar na Fazenda

1. Abra issue com label `deepseek`
2. Cole os dados de mercado ou uma descrição da tarefa
3. O agente DeepSeek gratuito analisará e gerará o relatório
4. O resultado será salvo em `deepseek/codigos/`

## Limites do DeepSeek Gratuito

- Não use para execução automática de ordens
- Use com moderação (não crie dezenas de issues simultâneas)
- Para produção, considere assinar API paga do DeepSeek ou usar NVIDIA NIM