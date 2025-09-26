import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, Typography, Tabs, Tab } from '@mui/material';
import { ConfiguracaoGeral } from './components/configuracao/ConfiguracaoGeral';
import { ThemeConfigurator } from './components/configuracao/ThemeConfigurator';
import TradingChat from './components/configuracao/TradingChat';

// Tema personalizado
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(10px)',
        },
      },
    },
  },
});

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl">
        <Box sx={{ py: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom align="center">
            🧠 Sistema Neural Trading v4.0
          </Typography>
          
          <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
            Sistema de Trading Automatizado com Múltiplos Agentes
          </Typography>

          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="configurações">
              <Tab label="Configuração Geral" />
              <Tab label="Configuração de Tema" />
              <Tab label="Chat de Suporte" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <ConfiguracaoGeral />
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <ThemeConfigurator />
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" gutterBottom>
                Chat de Suporte Implementado
              </Typography>
              <Typography color="text.secondary">
                O sistema de chat com restauração de conversas foi implementado com sucesso!
                Verifique o componente TradingChat.tsx para mais detalhes.
              </Typography>
            </Box>
          </TabPanel>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;