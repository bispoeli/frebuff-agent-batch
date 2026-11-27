//+------------------------------------------------------------------+
//|                                              Sinais XAUUSD M5    |
//|                                                      OpenCode FA |
//+------------------------------------------------------------------+
#property copyright "OpenCode Agent Farm"
#property link      "https://github.com/bispoeli/frebuff-agent-batch"
#property version   "1.00"
#property strict

//--- Parâmetros de entrada
input int      InpMAPeriod   = 20;       // Período Média Móvel
input int      InpRSIPeriod  = 14;       // Período RSI
input double   InpLotSize    = 0.01;     // Tamanho do lote
input int      InpStopLoss   = 50;       // Stop Loss (pips)
input int      InpTakeProfit = 100;      // Take Profit (pips)
input int      InpMagicNumber= 123456;   // Número Mágico

//--- Variáveis globais
int     handleMA;
int     handleRSI;
double  bufferMA[];
double  bufferRSI[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   handleMA = iMA(_Symbol, PERIOD_M5, InpMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   handleRSI = iRSI(_Symbol, PERIOD_M5, InpRSIPeriod, PRICE_CLOSE);
   
   if(handleMA == INVALID_HANDLE || handleRSI == INVALID_HANDLE)
     {
      Print("Erro ao criar indicadores");
      return(INIT_FAILED);
     }
   
   ArraySetAsSeries(bufferMA, true);
   ArraySetAsSeries(bufferRSI, true);
   
   Print("Sinais XAUUSD M5 - Inicializado com sucesso");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   IndicatorRelease(handleMA);
   IndicatorRelease(handleRSI);
   Print("Sinais XAUUSD M5 - Finalizado");
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Copiar dados dos indicadores
   if(CopyBuffer(handleMA, 0, 0, 3, bufferMA) < 3) return;
   if(CopyBuffer(handleRSI, 0, 0, 3, bufferRSI) < 3) return;
   
   double ma_atual = bufferMA[1];
   double ma_anterior = bufferMA[2];
   double rsi_atual = bufferRSI[1];
   double preco_atual = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Lógica de sinal (exemplo simplificado)
   bool sinal_compra = (preco_atual > ma_atual) && (ma_atual > ma_anterior) && (rsi_atual < 70);
   bool sinal_venda  = (preco_atual < ma_atual) && (ma_atual < ma_anterior) && (rsi_atual > 30);
   
   if(sinal_compra && !PosicaoAberta())
     {
      EnviarOrdem(ORDER_TYPE_BUY, preco_atual);
     }
   
   if(sinal_venda && !PosicaoAberta())
     {
      EnviarOrdem(ORDER_TYPE_SELL, preco_atual);
     }
  }

//+------------------------------------------------------------------+
//| Verificar se já existe posição aberta                            |
//+------------------------------------------------------------------+
bool PosicaoAberta()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(PositionGetSymbol(i) == _Symbol)
        return(true);
     }
   return(false);
  }

//+------------------------------------------------------------------+
//| Enviar ordem para o mercado                                      |
//+------------------------------------------------------------------+
void EnviarOrdem(ENUM_ORDER_TYPE tipo, double preco)
  {
   MqlTradeRequest request;
   MqlTradeResult   result;
   
   ZeroMemory(request);
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = InpLotSize;
   request.type = tipo;
   request.price = preco;
   request.sl = (tipo == ORDER_TYPE_BUY) ? preco - InpStopLoss * _Point : preco + InpStopLoss * _Point;
   request.tp = (tipo == ORDER_TYPE_BUY) ? preco + InpTakeProfit * _Point : preco - InpTakeProfit * _Point;
   request.deviation = 10;
   request.magic = InpMagicNumber;
   request.comment = "OpenCode FA";
   
   if(OrderSend(request, result) == TRADE_RETCODE_DONE)
     {
      Print("Ordem enviada com sucesso: ", result.order);
     }
   else
     {
      Print("Erro ao enviar ordem: ", result.retcode);
     }
  }
//+------------------------------------------------------------------+