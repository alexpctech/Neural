import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Grid,
  Alert,
  Slider,
  Paper,
  Stack,
} from '@mui/material';
import { 
  Palette as PaletteIcon, 
  DarkMode as DarkModeIcon, 
  LightMode as LightModeIcon,
  Save as SaveIcon 
} from '@mui/icons-material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
  fontSize: number;
  borderRadius: number;
  compactMode: boolean;
}

const COLOR_OPTIONS = [
  { name: 'Azul', value: '#2196f3' },
  { name: 'Verde', value: '#4caf50' },
  { name: 'Roxo', value: '#9c27b0' },
  { name: 'Laranja', value: '#ff9800' },
  { name: 'Vermelho', value: '#f44336' },
  { name: 'Ciano', value: '#00bcd4' },
];

export const ThemeConfigurator: React.FC = () => {
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>({
    mode: 'dark',
    primaryColor: '#2196f3',
    secondaryColor: '#f50057',
    fontSize: 14,
    borderRadius: 8,
    compactMode: false,
  });

  const [saved, setSaved] = useState(false);
  const [previewTheme, setPreviewTheme] = useState(createTheme());

  useEffect(() => {
    // Carregar configuração do tema do localStorage
    const savedTheme = localStorage.getItem('neural_theme');
    if (savedTheme) {
      setThemeConfig(JSON.parse(savedTheme));
    }
  }, []);

  useEffect(() => {
    // Atualizar preview do tema
    const theme = createTheme({
      palette: {
        mode: themeConfig.mode,
        primary: {
          main: themeConfig.primaryColor,
        },
        secondary: {
          main: themeConfig.secondaryColor,
        },
        background: {
          default: themeConfig.mode === 'dark' ? '#121212' : '#fafafa',
          paper: themeConfig.mode === 'dark' ? '#1e1e1e' : '#ffffff',
        },
      },
      typography: {
        fontSize: themeConfig.fontSize,
      },
      shape: {
        borderRadius: themeConfig.borderRadius,
      },
      components: {
        MuiCard: {
          styleOverrides: {
            root: {
              background: themeConfig.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.05)' 
                : 'rgba(0, 0, 0, 0.02)',
              backdropFilter: 'blur(10px)',
            },
          },
        },
        MuiButton: {
          styleOverrides: {
            root: {
              textTransform: 'none',
              fontWeight: 500,
            },
          },
        },
      },
    });
    setPreviewTheme(theme);
  }, [themeConfig]);

  const handleSave = () => {
    localStorage.setItem('neural_theme', JSON.stringify(themeConfig));
    // Aplicar tema globalmente
    document.documentElement.style.setProperty('--primary-color', themeConfig.primaryColor);
    document.documentElement.style.setProperty('--secondary-color', themeConfig.secondaryColor);
    
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleConfigChange = (field: keyof ThemeConfig, value: any) => {
    setThemeConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Configurador de Tema
      </Typography>

      {saved && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Tema salvo e aplicado com sucesso!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações de Aparência
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={themeConfig.mode === 'dark'}
                    onChange={(e) => handleConfigChange('mode', e.target.checked ? 'dark' : 'light')}
                    icon={<LightModeIcon />}
                    checkedIcon={<DarkModeIcon />}
                  />
                }
                label={`Modo ${themeConfig.mode === 'dark' ? 'Escuro' : 'Claro'}`}
                sx={{ mb: 3, display: 'block' }}
              />

              <Typography gutterBottom>Cor Primária</Typography>
              <Stack direction="row" spacing={1} sx={{ mb: 3 }}>
                {COLOR_OPTIONS.map((color) => (
                  <Box
                    key={color.value}
                    sx={{
                      width: 40,
                      height: 40,
                      backgroundColor: color.value,
                      borderRadius: 1,
                      cursor: 'pointer',
                      border: themeConfig.primaryColor === color.value ? '3px solid #fff' : 'none',
                      boxShadow: themeConfig.primaryColor === color.value ? '0 0 0 2px rgba(0,0,0,0.3)' : 'none',
                    }}
                    onClick={() => handleConfigChange('primaryColor', color.value)}
                    title={color.name}
                  />
                ))}
              </Stack>

              <Typography gutterBottom>Tamanho da Fonte: {themeConfig.fontSize}px</Typography>
              <Slider
                value={themeConfig.fontSize}
                onChange={(_, value) => handleConfigChange('fontSize', value)}
                min={12}
                max={18}
                step={1}
                marks
                sx={{ mb: 3 }}
              />

              <Typography gutterBottom>Arredondamento: {themeConfig.borderRadius}px</Typography>
              <Slider
                value={themeConfig.borderRadius}
                onChange={(_, value) => handleConfigChange('borderRadius', value)}
                min={0}
                max={20}
                step={2}
                marks
                sx={{ mb: 3 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={themeConfig.compactMode}
                    onChange={(e) => handleConfigChange('compactMode', e.target.checked)}
                  />
                }
                label="Modo Compacto"
                sx={{ mb: 2, display: 'block' }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <ThemeProvider theme={previewTheme}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                <PaletteIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Preview do Tema
              </Typography>
              
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" color="primary">
                    Card de Exemplo
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Este é um exemplo de como o tema ficará aplicado.
                  </Typography>
                  <Button variant="contained" size="small" sx={{ mt: 1 }}>
                    Botão Primário
                  </Button>
                  <Button variant="outlined" size="small" sx={{ mt: 1, ml: 1 }}>
                    Botão Secundário
                  </Button>
                </CardContent>
              </Card>

              <Alert severity="info" sx={{ mb: 2 }}>
                Informação de exemplo com o tema aplicado
              </Alert>

              <Alert severity="success">
                Sucesso! Tema configurado corretamente
              </Alert>
            </Paper>
          </ThemeProvider>
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={handleSave}
          startIcon={<SaveIcon />}
          size="large"
        >
          Salvar e Aplicar Tema
        </Button>
      </Box>
    </Box>
  );
};
