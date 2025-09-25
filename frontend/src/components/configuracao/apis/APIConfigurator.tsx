import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  Alert,
  Snackbar,
  Grid,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import apiConfig from './api_config.json';
import {
  ApiConfigs,
  ApiKeys,
  NotificationState,
  ShowSecretsState,
} from './types';

const apiConfigs = apiConfig.apis as ApiConfigs;

const APIConfigurator: React.FC = () => {
  const [apis, setApis] = useState<ApiKeys>({});
  const [notification, setNotification] = useState<NotificationState>({
    open: false,
    message: '',
    severity: 'info'
  });
  const [showSecrets, setShowSecrets] = useState<ShowSecretsState>({});

  useEffect(() => {
    // Carrega configurações salvas
    const loadSavedApis = async () => {
      try {
        const saved = localStorage.getItem('api_keys');
        if (saved) {
          setApis(JSON.parse(saved));
        }
      } catch (error) {
        console.error('Erro ao carregar APIs:', error);
      }
    };
    loadSavedApis();
  }, []);

  const validateApiKey = async (apiName: string, apiKey: string, secretKey: string | null = null): Promise<boolean> => {
    const config = apiConfigs[apiName];
    
    if (!config) {
      throw new Error('Configuração de API não encontrada');
    }

    // Validação do formato usando regex
    const keyFormat = new RegExp(config.campos.api_key.formato);
    if (!keyFormat.test(apiKey)) {
      throw new Error('Formato da API key inválido');
    }

    if (secretKey && config.campos.api_secret) {
      const secretFormat = new RegExp(config.campos.api_secret.formato);
      if (!secretFormat.test(secretKey)) {
        throw new Error('Formato da API secret inválido');
      }
    }

    // Aqui você implementaria a validação real com o serviço
    // Este é apenas um exemplo
    try {
      switch (apiName) {
        case 'alpha_vantage':
          // Exemplo de validação Alpha Vantage
          const response = await fetch(
            `https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=${apiKey}`
          );
          if (!response.ok) throw new Error('API key inválida');
          break;

        case 'finnhub':
          // Exemplo de validação Finnhub
          const finnResponse = await fetch(
            'https://finnhub.io/api/v1/quote?symbol=AAPL&token=' + apiKey
          );
          if (!finnResponse.ok) throw new Error('API key inválida');
          break;

        // Adicione validações para outras APIs aqui
      }
      return true;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error('Falha na validação da API: ' + error.message);
      }
      throw new Error('Falha na validação da API');
    }
  };

  const handleSaveApi = async (apiName: string) => {
    try {
      const apiKey = apis[apiName]?.api_key;
      const secretKey = apis[apiName]?.api_secret;

      if (!apiKey && apiConfigs[apiName].campos.api_key.obrigatorio) {
        throw new Error('API key é obrigatória');
      }

      if (apiKey) {
        await validateApiKey(apiName, apiKey, secretKey);
        
        // Salva no localStorage
        localStorage.setItem('api_keys', JSON.stringify({
          ...apis,
          [apiName]: { api_key: apiKey, api_secret: secretKey }
        }));

        setNotification({
          open: true,
          message: 'API validada e salva com sucesso!',
          severity: 'success'
        });
      }
    } catch (error) {
      setNotification({
        open: true,
        message: error instanceof Error ? `Erro: ${error.message}` : 'Erro desconhecido',
        severity: 'error'
      });
    }
  };

  const toggleShowSecret = (apiName: string) => {
    setShowSecrets((prev: ShowSecretsState) => ({
      ...prev,
      [apiName]: !prev[apiName]
    }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Configuração de APIs
      </Typography>

      <Grid container spacing={3}>
        {Object.entries(apiConfigs).map(([apiName, config]) => (
          <Grid item xs={12} md={6} key={apiName}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {config.nome}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {config.descricao}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="API Key"
                    variant="outlined"
                    value={apis[apiName]?.api_key || ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApis((prev: ApiKeys) => ({
                      ...prev,
                      [apiName]: { ...prev[apiName], api_key: e.target.value }
                    }))}
                    type={showSecrets[apiName] ? 'text' : 'password'}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton onClick={() => toggleShowSecret(apiName)}>
                            {showSecrets[apiName] ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    helperText={`Exemplo: ${config.campos.api_key.exemplo}`}
                  />
                </Box>

                {config.campos.api_secret && (
                  <Box sx={{ mb: 2 }}>
                    <TextField
                      fullWidth
                      label="API Secret"
                      variant="outlined"
                      value={apis[apiName]?.api_secret || ''}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApis((prev: ApiKeys) => ({
                        ...prev,
                        [apiName]: { ...prev[apiName], api_secret: e.target.value }
                      }))}
                      type={showSecrets[apiName] ? 'text' : 'password'}
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton onClick={() => toggleShowSecret(apiName)}>
                              {showSecrets[apiName] ? <VisibilityOff /> : <Visibility />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                      helperText={`Exemplo: ${config.campos.api_secret.exemplo}`}
                    />
                  </Box>
                )}

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Plano Gratuito: {config.plano_gratuito ? 'Sim' : 'Não'}
                    {config.limites_gratuito && ` - ${config.limites_gratuito}`}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Link
                    href={config.url_cadastro}
                    target="_blank"
                    rel="noopener"
                    underline="hover"
                  >
                    Obter API Key
                  </Link>
                  
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleSaveApi(apiName)}
                  >
                    Salvar e Validar
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert severity={notification.severity} variant="filled">
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default APIConfigurator;