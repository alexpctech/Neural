import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Snackbar,
  Slider,
  Chip,
  Divider,
  Fab,
  Dialog,
} from '@mui/material';
import { Chat as ChatIcon } from '@mui/icons-material';
import TradingChat from './TradingChat';

interface TradingConfig {
  maxPositions: number;
  maxRiskPerTrade: number;
  stopLossPercentage: number;
  takeProfitPercentage: number;
  tradingMode: 'manual' | 'semi-auto' | 'auto';
  enabledStrategies: string[];
  paperTrading: boolean;
  maxDailyLoss: number;
  minBalance: number;
  defaultOrderSize: number;
}

const availableStrategies = [
  'Media Móvel',
  'RSI',
  'MACD',
  'Bollinger Bands',
  'Momentum',
  'Mean Reversion',
  'Breakout',
  'Arbitragem',
];

export const TradingConfigurator: React.FC = () => {
  const [config, setConfig] = useState<TradingConfig>({
    maxPositions: 5,
    maxRiskPerTrade: 2,
    stopLossPercentage: 5,
    takeProfitPercentage: 10,
    tradingMode: 'manual',
    enabledStrategies: ['Media Móvel', 'RSI'],
    paperTrading: true,
    maxDailyLoss: 1000,
    minBalance: 10000,
    defaultOrderSize: 100,
  });
  const [showAlert, setShowAlert] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const handleSave = () => {
    localStorage.setItem('tradingConfig', JSON.stringify(config));
    setShowAlert(true);
  };

  const handleStrategyToggle = (strategy: string) => {
    setConfig(prev => ({
      ...prev,
      enabledStrategies: prev.enabledStrategies.includes(strategy)
        ? prev.enabledStrategies.filter(s => s !== strategy)
        : [...prev.enabledStrategies, strategy]
    }));
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Configurações de Trading
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Gerenciamento de Risco
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Máximo de Posições Simultâneas</Typography>
                <Slider
                  value={config.maxPositions}
                  onChange={(_, value) => setConfig({ ...config, maxPositions: value as number })}
                  min={1}
                  max={20}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Risco Máximo por Trade (%)</Typography>
                <Slider
                  value={config.maxRiskPerTrade}
                  onChange={(_, value) => setConfig({ ...config, maxRiskPerTrade: value as number })}
                  min={0.5}
                  max={10}
                  step={0.5}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <TextField
                fullWidth
                label="Stop Loss Padrão (%)"
                type="number"
                value={config.stopLossPercentage}
                onChange={(e) => setConfig({ ...config, stopLossPercentage: Number(e.target.value) })}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Take Profit Padrão (%)"
                type="number"
                value={config.takeProfitPercentage}
                onChange={(e) => setConfig({ ...config, takeProfitPercentage: Number(e.target.value) })}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Perda Máxima Diária (R$)"
                type="number"
                value={config.maxDailyLoss}
                onChange={(e) => setConfig({ ...config, maxDailyLoss: Number(e.target.value) })}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Saldo Mínimo (R$)"
                type="number"
                value={config.minBalance}
                onChange={(e) => setConfig({ ...config, minBalance: Number(e.target.value) })}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações de Execução
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Modo de Trading</InputLabel>
                <Select
                  value={config.tradingMode}
                  onChange={(e) => setConfig({ ...config, tradingMode: e.target.value as any })}
                >
                  <MenuItem value="manual">Manual</MenuItem>
                  <MenuItem value="semi-auto">Semi-Automático</MenuItem>
                  <MenuItem value="auto">Automático</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Tamanho Padrão da Ordem (R$)"
                type="number"
                value={config.defaultOrderSize}
                onChange={(e) => setConfig({ ...config, defaultOrderSize: Number(e.target.value) })}
                sx={{ mb: 2 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.paperTrading}
                    onChange={(e) => setConfig({ ...config, paperTrading: e.target.checked })}
                  />
                }
                label="Paper Trading (Simulação)"
              />

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Estratégias Ativas
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {availableStrategies.map((strategy) => (
                  <Chip
                    key={strategy}
                    label={strategy}
                    clickable
                    color={config.enabledStrategies.includes(strategy) ? 'primary' : 'default'}
                    onClick={() => handleStrategyToggle(strategy)}
                    variant={config.enabledStrategies.includes(strategy) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Resumo das Configurações
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Modo:</strong> {config.tradingMode === 'manual' ? 'Manual' : 
                                      config.tradingMode === 'semi-auto' ? 'Semi-Automático' : 'Automático'}
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Máx. Posições:</strong> {config.maxPositions}
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Risco por Trade:</strong> {config.maxRiskPerTrade}%
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Stop Loss:</strong> {config.stopLossPercentage}%
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Take Profit:</strong> {config.takeProfitPercentage}%
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Estratégias Ativas:</strong> {config.enabledStrategies.length}
              </Typography>
              
              <Typography variant="body2">
                <strong>Paper Trading:</strong> {config.paperTrading ? 'Ativo' : 'Inativo'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" onClick={handleSave}>
          Salvar Configurações
        </Button>
        <Button variant="outlined" onClick={() => window.location.reload()}>
          Resetar para Padrão
        </Button>
      </Box>

      <Snackbar
        open={showAlert}
        autoHideDuration={3000}
        onClose={() => setShowAlert(false)}
      >
        <Alert severity="success" onClose={() => setShowAlert(false)}>
          Configurações de trading salvas com sucesso!
        </Alert>
      </Snackbar>

      {/* Botão flutuante do chat */}
      <Fab
        color="primary"
        aria-label="chat"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1000,
        }}
        onClick={() => setShowChat(true)}
      >
        <ChatIcon />
      </Fab>

      {/* Dialog do chat */}
      <Dialog
        open={showChat}
        onClose={() => setShowChat(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { height: '80vh', maxHeight: '700px' }
        }}
      >
        <TradingChat onClose={() => setShowChat(false)} />
      </Dialog>
    </Box>
  );
};