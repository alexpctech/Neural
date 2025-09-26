import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Avatar,
  Paper,
  Menu,
  MenuItem,
  Snackbar,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  History as HistoryIcon,
  Clear as ClearIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Restore as RestoreIcon,
  FileDownload as ExportIcon,
  FileUpload as ImportIcon,
} from '@mui/icons-material';
import useChatSessions, { ChatMessage } from '../../hooks/useChatSessions';

interface ChatProps {
  onClose?: () => void;
  minimized?: boolean;
}

export const TradingChat: React.FC<ChatProps> = ({ onClose, minimized = false }) => {
  const [inputText, setInputText] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [importStatus, setImportStatus] = useState<'idle' | 'importing' | 'success' | 'error'>('idle');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    sessions,
    currentSession,
    currentSessionId,
    createNewSession,
    updateCurrentSession,
    deleteSession: deleteSessionById,
    restoreSession: restoreSessionById,
    exportSessions,
    importSessions,
  } = useChatSessions();

  const messages = currentSession?.messages || [];

  // Scroll automático para última mensagem
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    const newMessages = [...messages, userMessage];
    updateCurrentSession(newMessages);
    setInputText('');

    // Simular resposta do bot após um delay
    setTimeout(() => {
      const botResponse = generateBotResponse(inputText);
      const botMessage: ChatMessage = {
        id: `bot_${Date.now()}`,
        text: botResponse,
        sender: 'bot',
        timestamp: new Date(),
      };
      
      const updatedMessages = [...newMessages, botMessage];
      updateCurrentSession(updatedMessages);
    }, 1000);
  };

  const generateBotResponse = (userInput: string): string => {
    const input = userInput.toLowerCase();
    
    if (input.includes('preço') || input.includes('cotação')) {
      return 'Para consultar preços atualizados, você pode verificar na seção de monitoramento de ativos. Posso ajudar você a configurar alertas de preço também.';
    }
    
    if (input.includes('estratégia') || input.includes('trading')) {
      return 'Existem várias estratégias disponíveis como Média Móvel, RSI, MACD e Bollinger Bands. Qual estratégia você gostaria de discutir ou configurar?';
    }
    
    if (input.includes('risco') || input.includes('stop')) {
      return 'O gerenciamento de risco é fundamental. Recomendo definir um stop loss de 2-5% e nunca arriscar mais que 2% do capital por operação. Quer ajuda para configurar?';
    }
    
    if (input.includes('ajuda') || input.includes('help')) {
      return 'Posso ajudar você com:\\n• Configuração de estratégias de trading\\n• Gerenciamento de risco\\n• Análise de mercado\\n• Configuração de alertas\\n• Histórico de operações\\n\\nO que você gostaria de saber?';
    }
    
    return 'Interessante! Como assistente de trading, posso ajudar você com análises, estratégias e configurações. Em que posso ser útil?';
  };

  const handleRestoreSession = (sessionId: string) => {
    restoreSessionById(sessionId);
    setShowHistory(false);
  };

  const handleDeleteSession = (sessionId: string) => {
    deleteSessionById(sessionId);
  };

  const clearCurrentChat = () => {
    if (currentSession) {
      updateCurrentSession([]);
    }
    setAnchorEl(null);
  };

  const handleImportConversations = async (file: File) => {
    setImportStatus('importing');
    try {
      await importSessions(file);
      setImportStatus('success');
      setShowHistory(false);
      
      // Reset status após 3 segundos
      setTimeout(() => setImportStatus('idle'), 3000);
    } catch (error) {
      console.error('Erro ao importar conversas:', error);
      setImportStatus('error');
      
      // Reset status após 5 segundos
      setTimeout(() => setImportStatus('idle'), 5000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  if (minimized) {
    return (
      <Box sx={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<BotIcon />}
          onClick={() => setShowHistory(true)}
        >
          Chat Trading
        </Button>
      </Box>
    );
  }

  return (
    <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        avatar={<Avatar><BotIcon /></Avatar>}
        title="Assistente de Trading"
        subheader={`Sessão: ${currentSession?.name || 'Nova Sessão'}`}
        action={
          <Box>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <MoreVertIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={() => { setShowHistory(true); handleMenuClose(); }}>
                <HistoryIcon sx={{ mr: 1 }} />
                Restaurar Conversas
              </MenuItem>
              <MenuItem onClick={() => { createNewSession(); handleMenuClose(); }}>
                Nova Conversa
              </MenuItem>
              <MenuItem onClick={() => { clearCurrentChat(); handleMenuClose(); }}>
                <ClearIcon sx={{ mr: 1 }} />
                Limpar Chat
              </MenuItem>
              <MenuItem onClick={() => { exportSessions(); handleMenuClose(); }}>
                <ExportIcon sx={{ mr: 1 }} />
                Exportar Conversas
              </MenuItem>
              <MenuItem component="label">
                <ImportIcon sx={{ mr: 1 }} />
                Importar Conversas
                <input
                  type="file"
                  accept=".json,.chatreplay"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      handleImportConversations(file);
                    }
                    handleMenuClose();
                  }}
                />
              </MenuItem>
            </Menu>
            {onClose && (
              <IconButton onClick={onClose}>
                <ClearIcon />
              </IconButton>
            )}
          </Box>
        }
      />
      
      <CardContent sx={{ flexGrow: 1, overflow: 'auto', p: 1 }}>
        <List sx={{ maxHeight: '400px', overflow: 'auto' }}>
          {messages.map((message) => (
            <ListItem
              key={message.id}
              sx={{
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 1,
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  backgroundColor: message.sender === 'user' ? 'primary.light' : 'grey.100',
                  color: message.sender === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {message.sender === 'bot' ? <BotIcon sx={{ mr: 1, fontSize: 16 }} /> : <PersonIcon sx={{ mr: 1, fontSize: 16 }} />}
                  <Typography variant="caption">
                    {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.text}
                </Typography>
              </Paper>
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </CardContent>

      <Divider />
      
      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          multiline
          maxRows={3}
          placeholder="Digite sua mensagem..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          variant="outlined"
          size="small"
        />
        <Button
          variant="contained"
          onClick={sendMessage}
          disabled={!inputText.trim()}
          sx={{ minWidth: 'auto', px: 2 }}
        >
          <SendIcon />
        </Button>
      </Box>

      {/* Dialog para histórico de conversas */}
      <Dialog open={showHistory} onClose={() => setShowHistory(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <RestoreIcon sx={{ mr: 1 }} />
            Restaurar Conversas
          </Box>
        </DialogTitle>
        <DialogContent>
          {sessions.length === 0 ? (
            <Typography>Nenhuma conversa salva encontrada.</Typography>
          ) : (
            <List>
              {sessions.map((session) => (
                <React.Fragment key={session.id}>
                  <ListItem
                    button
                    onClick={() => handleRestoreSession(session.id)}
                    sx={{
                      border: currentSessionId === session.id ? '2px solid' : '1px solid',
                      borderColor: currentSessionId === session.id ? 'primary.main' : 'divider',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <ListItemText
                      primary={session.name}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            Criado: {session.createdAt.toLocaleString('pt-BR')}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Última atividade: {session.lastActivity.toLocaleString('pt-BR')}
                          </Typography>
                          <Chip 
                            label={`${session.messages.length} mensagens`} 
                            size="small" 
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      }
                    />
                    <IconButton
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      size="small"
                    >
                      <ClearIcon />
                    </IconButton>
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistory(false)}>Fechar</Button>
          <Button onClick={createNewSession} variant="contained">
            Nova Conversa
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar para status de importação */}
      <Snackbar 
        open={importStatus !== 'idle'} 
        autoHideDuration={importStatus === 'success' ? 3000 : 5000}
        onClose={() => setImportStatus('idle')}
      >
        <Alert 
          severity={importStatus === 'success' ? 'success' : importStatus === 'error' ? 'error' : 'info'}
          onClose={() => setImportStatus('idle')}
          icon={importStatus === 'importing' ? <CircularProgress size={20} /> : undefined}
        >
          {importStatus === 'importing' && 'Importando conversas...'}
          {importStatus === 'success' && 'Conversas importadas com sucesso!'}
          {importStatus === 'error' && 'Erro ao importar conversas. Verifique o formato do arquivo.'}
        </Alert>
      </Snackbar>
    </Card>
  );
};

export default TradingChat;