export interface ApiField {
  tipo: string;
  formato: string;
  exemplo: string;
  obrigatorio: boolean;
}

export interface ApiConfig {
  nome: string;
  descricao: string;
  campos: {
    api_key: ApiField;
    api_secret?: ApiField;
    organization_id?: ApiField;
  };
  url_cadastro: string;
  plano_gratuito: boolean;
  limites_gratuito?: string;
  formato_validacao: string;
}

export interface ApiConfigs {
  [key: string]: ApiConfig;
}

export interface ApiData {
  api_key?: string;
  api_secret?: string;
  organization_id?: string;
}

export interface ApiKeys {
  [key: string]: ApiData;
}

export interface NotificationState {
  open: boolean;
  message: string;
  severity: 'success' | 'info' | 'warning' | 'error';
}

export interface ShowSecretsState {
  [key: string]: boolean;
}