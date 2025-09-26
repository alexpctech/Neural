import fs from 'fs';
import path from 'path';

interface CopilotLog {
  id: string;
  kind: string;
  tool?: string;
  args?: string;
  time?: string;
  response?: any;
}

interface CopilotPrompt {
  prompt: string;
  hasSeen: boolean;
  logCount: number;
  logs: CopilotLog[];
}

interface CopilotReplay {
  exportedAt: string;
  totalPrompts: number;
  totalLogEntries: number;
  prompts: CopilotPrompt[];
}

// Função para extrair e mostrar conversas do arquivo replay
export const extractAndDisplayConversations = (replayData: CopilotReplay) => {
  console.log(`\n=== CONVERSAS PERDIDAS DO COPILOT ===`);
  console.log(`Exportado em: ${new Date(replayData.exportedAt).toLocaleString('pt-BR')}`);
  console.log(`Total de prompts: ${replayData.totalPrompts}`);
  console.log(`Total de logs: ${replayData.totalLogEntries}`);
  console.log(`\n${'='.repeat(80)}\n`);

  replayData.prompts.forEach((prompt, index) => {
    if (!prompt.prompt || prompt.prompt.trim() === '') {
      return; // Pula prompts vazios
    }

    console.log(`\n📝 CONVERSA ${index + 1}:`);
    console.log(`Status: ${prompt.hasSeen ? '✅ Vista' : '❌ Não vista'}`);
    console.log(`Logs: ${prompt.logCount} entradas`);
    console.log(`\n👤 USUÁRIO:`);
    console.log(`"${prompt.prompt}"`);

    // Extrai respostas dos logs
    const responses = extractResponsesFromLogs(prompt.logs);
    
    if (responses.length > 0) {
      console.log(`\n🤖 RESPOSTAS DO COPILOT:`);
      responses.forEach((response, responseIndex) => {
        console.log(`\n--- Resposta ${responseIndex + 1} ---`);
        console.log(response);
      });
    }

    // Mostra ações executadas
    const actions = extractActionsFromLogs(prompt.logs);
    if (actions.length > 0) {
      console.log(`\n🔧 AÇÕES EXECUTADAS:`);
      actions.forEach((action, actionIndex) => {
        console.log(`${actionIndex + 1}. ${action.tool}: ${action.description}`);
        if (action.result) {
          console.log(`   Resultado: ${action.result.substring(0, 100)}${action.result.length > 100 ? '...' : ''}`);
        }
      });
    }

    console.log(`\n${'-'.repeat(80)}`);
  });

  console.log(`\n✨ FIM DAS CONVERSAS RECUPERADAS ✨\n`);
};

const extractResponsesFromLogs = (logs: CopilotLog[]): string[] => {
  const responses: string[] = [];

  logs.forEach(log => {
    if (log.kind === 'request' && log.response) {
      try {
        // Tenta extrair texto da resposta
        let responseText = '';
        
        if (typeof log.response === 'string') {
          responseText = log.response;
        } else if (log.response && typeof log.response === 'object') {
          // Procura por campos de texto na resposta
          if (log.response.text) {
            responseText = log.response.text;
          } else if (log.response.content) {
            responseText = log.response.content;
          } else if (log.response.message) {
            responseText = log.response.message;
          } else {
            // Tenta converter objeto para string legível
            responseText = JSON.stringify(log.response, null, 2);
          }
        }

        if (responseText && responseText.trim()) {
          responses.push(responseText);
        }
      } catch (error) {
        console.error('Erro ao processar resposta:', error);
      }
    }
  });

  return responses;
};

const extractActionsFromLogs = (logs: CopilotLog[]): Array<{tool: string, description: string, result?: string}> => {
  const actions: Array<{tool: string, description: string, result?: string}> = [];

  logs.forEach(log => {
    if (log.kind === 'toolCall' && log.tool) {
      let description = '';
      let result = '';

      try {
        if (log.args) {
          const args = JSON.parse(log.args);
          
          // Extrai descrição baseada na ferramenta
          switch (log.tool) {
            case 'run_in_terminal':
              description = args.explanation || args.command || 'Comando executado no terminal';
              break;
            case 'create_file':
              description = `Criou arquivo: ${args.filePath}`;
              break;
            case 'replace_string_in_file':
              description = `Editou arquivo: ${args.filePath}`;
              break;
            case 'read_file':
              description = `Leu arquivo: ${args.filePath}`;
              break;
            case 'install_python_packages':
              description = `Instalou pacotes Python: ${args.packageList?.join(', ')}`;
              break;
            default:
              description = `Executou: ${log.tool}`;
          }
        }

        if (log.response) {
          if (Array.isArray(log.response)) {
            result = log.response.join('\n');
          } else if (typeof log.response === 'string') {
            result = log.response;
          }
        }

        actions.push({
          tool: log.tool,
          description,
          result
        });
      } catch (error) {
        actions.push({
          tool: log.tool,
          description: `Executou: ${log.tool}`,
        });
      }
    }
  });

  return actions;
};

// Função principal para processar o arquivo
export const processReplayFile = (filePath: string) => {
  try {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const replayData: CopilotReplay = JSON.parse(fileContent);
    extractAndDisplayConversations(replayData);
  } catch (error) {
    console.error('Erro ao processar arquivo de replay:', error);
  }
};

// Se executado diretamente
if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('Por favor, forneça o caminho do arquivo .chatreplay.json');
    process.exit(1);
  }
  
  processReplayFile(filePath);
}