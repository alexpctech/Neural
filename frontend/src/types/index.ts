import { MouseEvent } from 'react';

export interface Estrategia {
  id: string;
  nome: string;
  tipo: string;
  status: 'ativa' | 'inativa' | 'em_teste';
  performance: {
    retorno_total: number;
    drawdown_maximo: number;
    sharpe_ratio: number;
    win_rate: number;
    trades_total: number;
  };
  parametros: Record<string, any>;
  ultima_atualizacao: string;
}

export interface Operacao {
  id: string;
  estrategia_id: string;
  tipo: 'compra' | 'venda';
  ativo: string;
  quantidade: number;
  preco_entrada: number;
  preco_saida?: number;
  stop_loss: number;
  take_profit: number;
  status: 'aberta' | 'fechada' | 'cancelada';
  data_entrada: string;
  data_saida?: string;
  resultado?: number;
}

export interface Ativo {
  simbolo: string;
  nome: string;
  tipo: string;
  preco_atual: number;
  variacao_dia: number;
  volume: number;
  indicadores: {
    rsi: number;
    tendencia: 'alta' | 'baixa' | 'lateral';
    suporte?: number;
    resistencia?: number;
  };
}

export interface AlertaOperacao {
  id: string;
  tipo: 'info' | 'warning' | 'error' | 'success';
  mensagem: string;
  data: string;
  lido: boolean;
  acao_requerida: boolean;
}

export interface EstatisticasCarteira {
  valor_total: number;
  resultado_dia: number;
  resultado_mes: number;
  exposicao_atual: number;
  num_operacoes_abertas: number;
  distribuicao_ativos: Array<{
    ativo: string;
    percentual: number;
  }>;
}

export interface FiltroEstrategias {
  status?: 'ativa' | 'inativa' | 'em_teste';
  tipo?: string;
  performance_minima?: number;
  ordem?: 'retorno' | 'sharpe' | 'trades';
}

export interface ConfiguracoesGrafico {
  timeframe: string;
  indicadores: string[];
  tipo_grafico: 'candles' | 'linha';
  mostrar_volume: boolean;
}

export interface EventoCalendario {
  id: string;
  titulo: string;
  tipo: 'economico' | 'corporativo' | 'sistema';
  data: string;
  impacto: 'alto' | 'medio' | 'baixo';
  descricao: string;
}

export interface MenuContextoGrafico {
  x: number;
  y: number;
  mostrar: boolean;
  ativo?: string;
  preco?: number;
  data?: string;
}

export type ManipuladorMenuContexto = (
  event: MouseEvent,
  ativo?: string,
  preco?: number,
  data?: string
) => void;