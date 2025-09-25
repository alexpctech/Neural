import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { 
  Estrategia,
  Operacao,
  Ativo,
  AlertaOperacao,
  EstatisticasCarteira 
} from '../../types';

interface DashboardProps {
  estatisticas: EstatisticasCarteira;
  estrategias_ativas: Estrategia[];
  operacoes_abertas: Operacao[];
  ativos_monitorados: Ativo[];
  alertas: AlertaOperacao[];
}

const formatarMoeda = (valor: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor);
};

const formatarPercentual = (valor: number): string => {
  return `${(valor * 100).toFixed(2)}%`;
};

const Dashboard: React.FC<DashboardProps> = ({
  estatisticas,
  estrategias_ativas,
  operacoes_abertas,
  ativos_monitorados,
  alertas,
}) => {
  const handleRefresh = () => {
    // Implementar atualização dos dados
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Grid container spacing={3}>
        {/* Resumo da Carteira */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">Resumo da Carteira</Typography>
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Box>
            <List>
              <ListItem>
                <ListItemText
                  primary="Valor Total"
                  secondary={formatarMoeda(estatisticas.valor_total)}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Resultado do Dia"
                  secondary={
                    <Typography
                      color={estatisticas.resultado_dia >= 0 ? 'success.main' : 'error.main'}
                    >
                      {formatarMoeda(estatisticas.resultado_dia)}
                      {' '}
                      <Chip
                        size="small"
                        icon={estatisticas.resultado_dia >= 0 ? <TrendingUp /> : <TrendingDown />}
                        label={formatarPercentual(estatisticas.resultado_dia / estatisticas.valor_total)}
                        color={estatisticas.resultado_dia >= 0 ? 'success' : 'error'}
                      />
                    </Typography>
                  }
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* Estratégias Ativas */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Estratégias Ativas"
              action={
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <CardContent>
              <List>
                {estrategias_ativas.map((estrategia) => (
                  <React.Fragment key={estrategia.id}>
                    <ListItem>
                      <ListItemText
                        primary={estrategia.nome}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              Win Rate: {formatarPercentual(estrategia.performance.win_rate)}
                            </Typography>
                            <Typography variant="body2">
                              Retorno: {formatarPercentual(estrategia.performance.retorno_total)}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={estrategia.status}
                        color={
                          estrategia.status === 'ativa'
                            ? 'success'
                            : estrategia.status === 'em_teste'
                            ? 'warning'
                            : 'default'
                        }
                        size="small"
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Operações Abertas */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Operações Abertas"
              action={
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <CardContent>
              <List>
                {operacoes_abertas.map((operacao) => (
                  <React.Fragment key={operacao.id}>
                    <ListItem>
                      <ListItemText
                        primary={`${operacao.ativo} - ${operacao.tipo.toUpperCase()}`}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              Entrada: {formatarMoeda(operacao.preco_entrada)}
                            </Typography>
                            <Typography variant="body2">
                              Stop: {formatarMoeda(operacao.stop_loss)}
                            </Typography>
                            <Typography variant="body2">
                              Alvo: {formatarMoeda(operacao.take_profit)}
                            </Typography>
                          </Box>
                        }
                      />
                      <Box>
                        <Typography variant="h6" color="primary">
                          {formatarMoeda(operacao.quantidade * operacao.preco_entrada)}
                        </Typography>
                      </Box>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Ativos Monitorados */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Ativos Monitorados"
              action={
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <CardContent>
              <List>
                {ativos_monitorados.map((ativo) => (
                  <React.Fragment key={ativo.simbolo}>
                    <ListItem>
                      <ListItemText
                        primary={ativo.simbolo}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              RSI: {ativo.indicadores.rsi.toFixed(2)}
                            </Typography>
                            <Typography variant="body2">
                              Tendência: {ativo.indicadores.tendencia}
                            </Typography>
                          </Box>
                        }
                      />
                      <Box textAlign="right">
                        <Typography variant="h6">
                          {formatarMoeda(ativo.preco_atual)}
                        </Typography>
                        <Typography
                          variant="body2"
                          color={ativo.variacao_dia >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatarPercentual(ativo.variacao_dia)}
                        </Typography>
                      </Box>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Alertas */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Alertas"
              action={
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <CardContent>
              <List>
                {alertas.map((alerta) => (
                  <React.Fragment key={alerta.id}>
                    <ListItem>
                      <ListItemText
                        primary={alerta.mensagem}
                        secondary={new Date(alerta.data).toLocaleString()}
                      />
                      <Chip
                        label={alerta.tipo}
                        color={
                          alerta.tipo === 'error'
                            ? 'error'
                            : alerta.tipo === 'warning'
                            ? 'warning'
                            : alerta.tipo === 'success'
                            ? 'success'
                            : 'default'
                        }
                        size="small"
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;