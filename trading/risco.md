# Gestão de Risco - Trading XAUUSD

## Regras de Ouro

1. **Risco por operação**: Máximo 1-2% do capital por trade.
2. **Risco diário**: Máximo 5% do capital por dia. Se atingir, pare de operar.
3. **Drawdown máximo**: 10% do capital. Se atingir, pare o robô para revisão.
4. **Relação Risco/Retorno**: Mínimo 1:2 (arriscar 1 para ganhar 2).
5. **Nunca exceda o stop loss definido pelo agente.**

## Perfis de Execução

| Perfil | Execução | Uso |
|--------|----------|-----|
| `analyst` | Apenas leitura e análise | ✅ Recomendado para uso com agentes |
| `executor` | Pode enviar ordens | ⚠️ Apenas com supervisão humana |
| `full` | Controle completo | ❌ Não recomendado para automação |

## Exemplo de Sinal

```
Par: XAUUSD
Direção: BUY
Entrada: 2650.50
Stop Loss: 2645.00 (50 pips)
Take Profit: 2665.00 (150 pips)
Confiança: 75%
Justificativa: Suporte em Donchian Channel M5 + RSI oversold
```

## Aviso Legal

Esta ferramenta é para fins educacionais e de prototipagem. Não constitui recomendação de investimento. Operar no mercado financeiro envolve riscos de perda de capital. Use conta demo antes de operar com dinheiro real.