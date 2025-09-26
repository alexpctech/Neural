import { useState, useEffect, useCallback } from 'react';

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: Date;
  lastActivity: Date;
}

const STORAGE_KEY = 'tradingChatSessions';

export const useChatSessions = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  // Carregar sessões do localStorage
  const loadSessions = useCallback(() => {
    try {
      const savedSessions = localStorage.getItem(STORAGE_KEY);
      if (savedSessions) {
        const parsedSessions = JSON.parse(savedSessions).map((session: any) => ({
          ...session,
          createdAt: new Date(session.createdAt),
          lastActivity: new Date(session.lastActivity),
          messages: session.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        setSessions(parsedSessions);
        
        // Se não há sessão atual, usar a mais recente
        if (!currentSessionId && parsedSessions.length > 0) {
          setCurrentSessionId(parsedSessions[0].id);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar sessões do chat:', error);
    }
  }, [currentSessionId]);

  // Salvar sessões no localStorage
  const saveSessions = useCallback((sessionsToSave: ChatSession[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionsToSave));
    } catch (error) {
      console.error('Erro ao salvar sessões do chat:', error);
    }
  }, []);

  // Criar nova sessão
  const createNewSession = useCallback(() => {
    const newSessionId = `session_${Date.now()}`;
    const newSession: ChatSession = {
      id: newSessionId,
      name: `Chat ${new Date().toLocaleDateString('pt-BR')} ${new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`,
      messages: [],
      createdAt: new Date(),
      lastActivity: new Date(),
    };

    const updatedSessions = [newSession, ...sessions];
    setSessions(updatedSessions);
    setCurrentSessionId(newSessionId);
    saveSessions(updatedSessions);
    
    return newSession;
  }, [sessions, saveSessions]);

  // Atualizar sessão atual
  const updateCurrentSession = useCallback((messages: ChatMessage[]) => {
    if (!currentSessionId) return;

    const updatedSessions = sessions.map(session => 
      session.id === currentSessionId 
        ? { ...session, messages, lastActivity: new Date() }
        : session
    );
    
    setSessions(updatedSessions);
    saveSessions(updatedSessions);
  }, [currentSessionId, sessions, saveSessions]);

  // Deletar sessão
  const deleteSession = useCallback((sessionId: string) => {
    const updatedSessions = sessions.filter(s => s.id !== sessionId);
    setSessions(updatedSessions);
    saveSessions(updatedSessions);
    
    // Se deletou a sessão atual, criar uma nova
    if (currentSessionId === sessionId) {
      if (updatedSessions.length > 0) {
        setCurrentSessionId(updatedSessions[0].id);
      } else {
        // Criar nova sessão se não há mais nenhuma
        setTimeout(() => createNewSession(), 100);
      }
    }
  }, [sessions, currentSessionId, saveSessions, createNewSession]);

  // Restaurar sessão
  const restoreSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      return session;
    }
    return null;
  }, [sessions]);

  // Renomear sessão
  const renameSession = useCallback((sessionId: string, newName: string) => {
    const updatedSessions = sessions.map(session => 
      session.id === sessionId 
        ? { ...session, name: newName }
        : session
    );
    
    setSessions(updatedSessions);
    saveSessions(updatedSessions);
  }, [sessions, saveSessions]);

  // Limpar todas as sessões
  const clearAllSessions = useCallback(() => {
    setSessions([]);
    setCurrentSessionId('');
    localStorage.removeItem(STORAGE_KEY);
    createNewSession();
  }, [createNewSession]);

  // Exportar conversas
  const exportSessions = useCallback(() => {
    const dataStr = JSON.stringify(sessions, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat-sessions-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [sessions]);

  // Importar conversas
  const importSessions = useCallback((file: File) => {
    return new Promise<void>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;
          let validatedSessions: ChatSession[] = [];

          // Verifica se é um arquivo de replay do Copilot
          if (content.includes('exportedAt') && content.includes('totalPrompts')) {
            // Importa do arquivo de replay do Copilot
            const { convertReplayToSessions } = await import('../utils/copilotImporter');
            validatedSessions = await convertReplayToSessions(file);
          } else {
            // Importação normal de sessões
            const importedSessions = JSON.parse(content);
            validatedSessions = importedSessions.map((session: any) => ({
              ...session,
              createdAt: new Date(session.createdAt),
              lastActivity: new Date(session.lastActivity),
              messages: session.messages.map((msg: any) => ({
                ...msg,
                timestamp: new Date(msg.timestamp)
              }))
            }));
          }
          
          setSessions(prev => [...validatedSessions, ...prev]);
          saveSessions([...validatedSessions, ...sessions]);
          resolve();
        } catch (error) {
          reject(error);
        }
      };
      reader.readAsText(file);
    });
  }, [sessions, saveSessions]);

  // Inicializar
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Criar sessão inicial se não existir
  useEffect(() => {
    if (sessions.length === 0 && !currentSessionId) {
      createNewSession();
    }
  }, [sessions.length, currentSessionId, createNewSession]);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  return {
    sessions,
    currentSession,
    currentSessionId,
    createNewSession,
    updateCurrentSession,
    deleteSession,
    restoreSession,
    renameSession,
    clearAllSessions,
    exportSessions,
    importSessions,
    setCurrentSessionId,
  };
};

export default useChatSessions;