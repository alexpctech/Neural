/**
 * Serviço para comunicação com o backend
 */
import axios from 'axios';
import { 
  Estrategia,
  Operacao,
  Ativo,
  AlertaOperacao,
  EstatisticasCarteira 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Tipo genérico para respostas da API
interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    if (config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      config.headers = { Authorization: `Bearer ${token}` };
    }
  }
  return config;
});

// Serviços de Dashboard
export const dashboardService = {
  async obterEstatisticas(): Promise<EstatisticasCarteira> {
    const response = await api.get<ApiResponse<EstatisticasCarteira>>('/dashboard/estatisticas');
    return response.data.data;
  },

  async obterEstrategiasAtivas(): Promise<Estrategia[]> {
    const response = await api.get<ApiResponse<Estrategia[]>>('/dashboard/estrategias/ativas');
    return response.data.data;
  },

  async obterOperacoesAbertas(): Promise<Operacao[]> {
    const response = await api.get<ApiResponse<Operacao[]>>('/dashboard/operacoes/abertas');
    return response.data.data;
  },

  async obterAtivosMonitorados(): Promise<Ativo[]> {
    const response = await api.get<ApiResponse<Ativo[]>>('/dashboard/ativos/monitorados');
    return response.data.data;
  },

  async obterAlertas(): Promise<AlertaOperacao[]> {
    const response = await api.get<ApiResponse<AlertaOperacao[]>>('/dashboard/alertas');
    return response.data.data;
  }
};

// Serviços de Operações
export const operacoesService = {
  async listar(filtros?: Record<string, any>): Promise<Operacao[]> {
    const response = await api.get<ApiResponse<Operacao[]>>('/operacoes', { params: filtros });
    return response.data.data;
  },

  async obterDetalhes(id: string): Promise<Operacao> {
    const response = await api.get<ApiResponse<Operacao>>(`/operacoes/${id}`);
    return response.data.data;
  },

  async fecharOperacao(id: string, dados: {
    preco_saida: number;
    motivo?: string;
  }): Promise<Operacao> {
    const response = await api.post<ApiResponse<Operacao>>(`/operacoes/${id}/fechar`, dados);
    return response.data.data;
  }
};

// Serviços de Estratégias
export const estrategiasService = {
  async listar(): Promise<Estrategia[]> {
    const response = await api.get<ApiResponse<Estrategia[]>>('/estrategias');
    return response.data.data;
  },

  async obterDetalhes(id: string): Promise<Estrategia> {
    const response = await api.get<ApiResponse<Estrategia>>(`/estrategias/${id}`);
    return response.data.data;
  },

  async alterarStatus(id: string, status: 'ativa' | 'inativa' | 'em_teste'): Promise<Estrategia> {
    const response = await api.patch<ApiResponse<Estrategia>>(`/estrategias/${id}/status`, { status });
    return response.data.data;
  },

  async atualizarParametros(id: string, parametros: Record<string, any>): Promise<Estrategia> {
    const response = await api.patch<ApiResponse<Estrategia>>(`/estrategias/${id}/parametros`, { parametros });
    return response.data.data;
  }
};

// Serviços de Configuração
export const configService = {
  async salvarConfigAPI(nome: string, config: Record<string, any>): Promise<void> {
    await api.post('/config/api', { nome, config });
  },

  async obterConfigAPI(nome: string): Promise<Record<string, any>> {
    const response = await api.get<ApiResponse<Record<string, any>>>(`/config/api/${nome}`);
    return response.data.data;
  },

  async validarChaveAPI(nome: string, chave: string): Promise<boolean> {
    try {
      interface ValidacaoResponse {
        valida: boolean;
      }
      const response = await api.post<ApiResponse<ValidacaoResponse>>('/config/api/validar', { nome, chave });
      return response.data.data.valida;
    } catch {
      return false;
    }
  }
};

// Serviços de Autenticação
export const authService = {
  async login(email: string, senha: string): Promise<string> {
    interface LoginResponse {
      token: string;
    }
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', { email, senha });
    const { token } = response.data.data;
    localStorage.setItem('auth_token', token);
    return token;
  },

  async logout(): Promise<void> {
    localStorage.removeItem('auth_token');
    // Limpa estado da aplicação se necessário
  },

  async verificarToken(): Promise<boolean> {
    try {
      await api.get('/auth/verificar');
      return true;
    } catch {
      return false;
    }
  }
};

export default api;