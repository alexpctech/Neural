import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Grid,
  Alert,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface ConfiguracaoSistema {
  modo_operacao: 'SIMULADO' | 'PRODUCAO';
  capital_inicial: number;
  log_nivel: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  auto_save: boolean;
  notificacoes: boolean;
  max_posicoes: number;
  risk_percentage: number;
}

export const ConfiguracaoGeral: React.FC = () => {
  const [config, setConfig] = useState<ConfiguracaoSistema>({
    modo_operacao: 'SIMULADO',
    capital_inicial: 500000,
    log_nivel: 'INFO',
    auto_save: true,
    notificacoes: true,
    max_posicoes: 5,
    risk_percentage: 2,
  });

  const [originalConfig, setOriginalConfig] = useState<ConfiguracaoSistema>(config);
  const [hasChanges, setHasChanges] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Carregar configuração salva do localStorage
    const savedConfig = localStorage.getItem('neural_config');
    if (savedConfig) {
      const parsed = JSON.parse(savedConfig);
      setConfig(parsed);
      setOriginalConfig(parsed);
    }
  }, []);

  useEffect(() => {
    // Detectar mudanças
    setHasChanges(JSON.stringify(config) !== JSON.stringify(originalConfig));
  }, [config, originalConfig]);

  const handleSave = () => {
    localStorage.setItem('neural_config', JSON.stringify(config));
    setOriginalConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setConfig(originalConfig);
  };

  const handleChange = (field: keyof ConfiguracaoSistema, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Configuração Geral
      </Typography>
      
      {saved && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Configurações salvas com sucesso!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações de Trading
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Modo de Operação</InputLabel>
                <Select
                  value={config.modo_operacao}
                  onChange={(e) => handleChange('modo_operacao', e.target.value)}
                >
                  <MenuItem value="SIMULADO">
                    <Chip label="Simulado" color="primary" size="small" sx={{ mr: 1 }} />
                    Simulado
                  </MenuItem>
                  <MenuItem value="PRODUCAO">
                    <Chip label="Produção" color="error" size="small" sx={{ mr: 1 }} />
                    Produção (Real)
                  </MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Capital Inicial"
                type="number"
                value={config.capital_inicial}
                onChange={(e) => handleChange('capital_inicial', Number(e.target.value))}
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: 'R$ ',
                }}
              />

              <TextField
                fullWidth
                label="Máximo de Posições"
                type="number"
                value={config.max_posicoes}
                onChange={(e) => handleChange('max_posicoes', Number(e.target.value))}
                sx={{ mb: 2 }}
                inputProps={{ min: 1, max: 20 }}
              />

              <TextField
                fullWidth
                label="Risco por Operação (%)"
                type="number"
                value={config.risk_percentage}
                onChange={(e) => handleChange('risk_percentage', Number(e.target.value))}
                sx={{ mb: 2 }}
                inputProps={{ min: 0.1, max: 10, step: 0.1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações do Sistema
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Nível de Log</InputLabel>
                <Select
                  value={config.log_nivel}
                  onChange={(e) => handleChange('log_nivel', e.target.value)}
                >
                  <MenuItem value="DEBUG">Debug</MenuItem>
                  <MenuItem value="INFO">Info</MenuItem>
                  <MenuItem value="WARNING">Warning</MenuItem>
                  <MenuItem value="ERROR">Error</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={config.auto_save}
                    onChange={(e) => handleChange('auto_save', e.target.checked)}
                  />
                }
                label="Salvamento Automático"
                sx={{ mb: 2, display: 'block' }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.notificacoes}
                    onChange={(e) => handleChange('notificacoes', e.target.checked)}
                  />
                }
                label="Notificações"
                sx={{ mb: 2, display: 'block' }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          onClick={handleReset}
          disabled={!hasChanges}
          startIcon={<RefreshIcon />}
        >
          Resetar
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!hasChanges}
          startIcon={<SaveIcon />}
        >
          Salvar Configurações
        </Button>
      </Box>
    </Box>
  );
};
