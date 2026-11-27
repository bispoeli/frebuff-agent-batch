#!/usr/bin/env python3
"""
Script de Análise de Mercado - Gerado pela Fazenda de Agentes OpenCode
Usa DeepSeek v4 Flash (gratuito) para análise de dados financeiros.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class AnalisadorMercado:
    """Classe para análise de dados de mercado (XAUUSD, ações, criptomoedas)."""

    def __init__(self, dados: pd.DataFrame):
        """
        Inicializa o analisador com dados OHLCV.
        
        Args:
            dados: DataFrame com colunas: open, high, low, close, volume
        """
        self.dados = dados.copy()
        self._calcular_indicadores()

    def _calcular_indicadores(self):
        """Calcula indicadores técnicos básicos."""
        # Média Móvel Simples (20 períodos)
        self.dados['SMA20'] = self.dados['close'].rolling(window=20).mean()

        # RSI (14 períodos)
        delta = self.dados['close'].diff()
        ganho = delta.where(delta > 0, 0)
        perda = -delta.where(delta < 0, 0)
        media_ganho = ganho.rolling(window=14).mean()
        media_perda = perda.rolling(window=14).mean()
        rs = media_ganho / media_perda
        self.dados['RSI14'] = 100 - (100 / (1 + rs))

        # Bollinger Bands (20, 2)
        self.dados['BB_superior'] = self.dados['SMA20'] + (self.dados['close'].rolling(window=20).std() * 2)
        self.dados['BB_inferior'] = self.dados['SMA20'] - (self.dados['close'].rolling(window=20).std() * 2)

    def sinal_compra(self, indice: int) -> bool:
        """Verifica se há sinal de compra no índice especificado."""
        linha = self.dados.iloc[indice]
        return (
            linha['close'] > linha['SMA20'] and
            linha['RSI14'] < 70 and
            linha['close'] > linha['BB_inferior']
        )

    def sinal_venda(self, indice: int) -> bool:
        """Verifica se há sinal de venda no índice especificado."""
        linha = self.dados.iloc[indice]
        return (
            linha['close'] < linha['SMA20'] and
            linha['RSI14'] > 30 and
            linha['close'] < linha['BB_superior']
        )

    def gerar_relatorio(self) -> str:
        """Gera relatório textual da análise."""
        ultima = self.dados.iloc[-1]
        sinal = "NEUTRO"
        if self.sinal_compra(len(self.dados) - 1):
            sinal = "COMPRA"
        elif self.sinal_venda(len(self.dados) - 1):
            sinal = "VENDA"

        relatorio = f"""
Relatório de Análise - XAUUSD
=============================
Último preço: {ultima['close']:.2f}
SMA20: {ultima['SMA20']:.2f}
RSI14: {ultima['RSI14']:.2f}
Bollinger Superior: {ultima['BB_superior']:.2f}
Bollinger Inferior: {ultima['BB_inferior']:.2f}

Sinal: {sinal}

Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return relatorio


if __name__ == "__main__":
    # Exemplo de uso com dados simulados
    np.random.seed(42)
    precos = 2650 + np.cumsum(np.random.randn(100) * 0.5)
    dados = pd.DataFrame({
        'open': precos,
        'high': precos + np.random.rand(100) * 2,
        'low': precos - np.random.rand(100) * 2,
        'close': precos + np.random.randn(100) * 0.5,
        'volume': np.random.randint(100, 1000, 100)
    })

    analisador = AnalisadorMercado(dados)
    print(analisador.gerar_relatorio())