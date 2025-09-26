import { ChatMessage, ChatSession } from '../hooks/useChatSessions';

interface CopilotPrompt {
  prompt: string;
  hasSeen: boolean;
  logCount: number;
  logs: any[];
}

interface CopilotReplay {
  exportedAt: string;
  totalPrompts: number;
  totalLogEntries: number;
  prompts: CopilotPrompt[];
}

export const importCopilotConversations = (replayData: CopilotReplay): ChatSession[] => {
  const sessions: ChatSession[] = [];

  replayData.prompts.forEach((prompt, index) => {
    if (!prompt.prompt || prompt.prompt.trim() === '') {
      return; // Pula prompts vazios
    }

    const sessionId = `copilot_${Date.now()}_${index}`;
    const messages: ChatMessage[] = [];

    // Adiciona a pergunta do usuário
    messages.push({
      id: `user_${sessionId}_0`,
      text: prompt.prompt,
      sender: 'user',
      timestamp: new Date(replayData.exportedAt),
    });

    // Tenta extrair respostas dos logs
    const responses = extractResponsesFromLogs(prompt.logs);
    responses.forEach((response, responseIndex) => {
      messages.push({
        id: `bot_${sessionId}_${responseIndex + 1}`,
        text: response,
        sender: 'bot',
        timestamp: new Date(replayData.exportedAt),
      });
    });

    // Se não há resposta específica, adiciona uma resposta genérica
    if (responses.length === 0) {
      messages.push({
        id: `bot_${sessionId}_1`,
        text: `Prompt processado com ${prompt.logCount} logs de ação.`,
        sender: 'bot',
        timestamp: new Date(replayData.exportedAt),
      });
    }

    const session: ChatSession = {
      id: sessionId,
      name: `Copilot: ${prompt.prompt.substring(0, 50)}${prompt.prompt.length > 50 ? '...' : ''}`,
      messages,
      createdAt: new Date(replayData.exportedAt),
      lastActivity: new Date(replayData.exportedAt),
    };

    sessions.push(session);
  });

  return sessions;
};

const extractResponsesFromLogs = (logs: any[]): string[] => {
  const responses: string[] = [];

  logs.forEach(log => {
    if (log.response && typeof log.response === 'string') {
      responses.push(log.response);
    } else if (log.response && Array.isArray(log.response)) {
      responses.push(...log.response.filter((r: any) => typeof r === 'string'));
    } else if (log.kind === 'request' && log.response) {
      // Tenta extrair texto da resposta
      const responseText = extractTextFromResponse(log.response);
      if (responseText) {
        responses.push(responseText);
      }
    }
  });

  return responses;
};

const extractTextFromResponse = (response: any): string | null => {
  if (typeof response === 'string') {
    return response;
  }

  if (response && typeof response === 'object') {
    // Procura por campos comuns de texto
    const textFields = ['text', 'content', 'message', 'body'];
    for (const field of textFields) {
      if (response[field] && typeof response[field] === 'string') {
        return response[field];
      }
    }

    // Se é um array, tenta extrair strings
    if (Array.isArray(response)) {
      const textItems = response.filter(item => typeof item === 'string');
      if (textItems.length > 0) {
        return textItems.join('\n');
      }
    }
  }

  return null;
};

export const convertReplayToSessions = async (file: File): Promise<ChatSession[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const replayData: CopilotReplay = JSON.parse(e.target?.result as string);
        const sessions = importCopilotConversations(replayData);
        resolve(sessions);
      } catch (error) {
        reject(new Error('Erro ao processar arquivo de replay: ' + error));
      }
    };

    reader.onerror = () => {
      reject(new Error('Erro ao ler arquivo'));
    };

    reader.readAsText(file);
  });
};