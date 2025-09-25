"""
Gerenciador de Timeline do Projeto
Atualiza automaticamente o status do projeto na timeline do VS Code
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class TimelineManager:
    def __init__(self):
        self.timeline_path = os.path.join('.vscode', 'neural.timeline-custom.json')
        self.current_data = self._load_timeline()
        
    def _load_timeline(self) -> Dict:
        """Carrega os dados atuais da timeline"""
        if os.path.exists(self.timeline_path):
            with open(self.timeline_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def _save_timeline(self):
        """Salva as alterações na timeline"""
        os.makedirs(os.path.dirname(self.timeline_path), exist_ok=True)
        with open(self.timeline_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_data, f, indent=4, ensure_ascii=False)
            
    def update_milestone_status(self, name: str, status: str, 
                              description: Optional[str] = None):
        """
        Atualiza o status de um marco na timeline
        
        Args:
            name: Nome do marco
            status: Status ('completed', 'in-progress', 'pending')
            description: Nova descrição (opcional)
        """
        if not self.current_data or 'milestones' not in self.current_data:
            return
            
        for milestone in self.current_data['milestones']:
            if milestone['name'] == name:
                milestone['status'] = status
                if status == 'completed':
                    milestone['completedDate'] = datetime.now().strftime('%Y-%m-%d')
                    milestone['color'] = '#22C55E'  # Verde
                elif status == 'in-progress':
                    milestone['color'] = '#FB923C'  # Laranja
                else:
                    milestone['color'] = '#60A5FA'  # Azul
                    
                if description:
                    milestone['description'] = description
                    
                self._save_timeline()
                break
                
    def add_milestone(self, name: str, description: str, due_date: str,
                     status: str = 'pending', icon: str = 'rocket'):
        """
        Adiciona um novo marco à timeline
        
        Args:
            name: Nome do marco
            description: Descrição detalhada
            due_date: Data prevista (YYYY-MM-DD)
            status: Status inicial
            icon: Ícone do VS Code
        """
        if 'milestones' not in self.current_data:
            self.current_data['milestones'] = []
            
        new_milestone = {
            'name': name,
            'status': status,
            'description': description,
            'dueDate': due_date,
            'icon': icon,
            'color': '#60A5FA'  # Azul (pendente)
        }
        
        if status == 'completed':
            new_milestone['completedDate'] = datetime.now().strftime('%Y-%m-%d')
            new_milestone['color'] = '#22C55E'  # Verde
        elif status == 'in-progress':
            new_milestone['color'] = '#FB923C'  # Laranja
            
        self.current_data['milestones'].append(new_milestone)
        self._save_timeline()
        
    def get_progress_report(self) -> Dict:
        """Retorna um relatório do progresso do projeto"""
        if not self.current_data or 'milestones' not in self.current_data:
            return {}
            
        total = len(self.current_data['milestones'])
        completed = sum(1 for m in self.current_data['milestones'] 
                       if m['status'] == 'completed')
        in_progress = sum(1 for m in self.current_data['milestones'] 
                         if m['status'] == 'in-progress')
        
        return {
            'total_milestones': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': total - completed - in_progress,
            'progress_percentage': (completed / total) * 100 if total > 0 else 0
        }
        
    def sync_with_files(self):
        """
        Sincroniza a timeline com o estado real dos arquivos e diretórios
        do projeto para manter sempre atualizada
        """
        # TODO: Implementar verificação automática do progresso
        # baseada em arquivos modificados, commits, etc.
        pass

# Exemplo de uso
if __name__ == '__main__':
    timeline = TimelineManager()
    
    # Atualiza status do frontend
    timeline.update_milestone_status(
        'Interface do Usuário',
        'in-progress',
        '''Concluído:
✓ Estrutura React/TypeScript configurada
✓ Layout base implementado
✓ Dashboard inicial criado

Pendente:
➤ Finalizar componentes de configuração
➤ Implementar sistema de temas'''
    )
    
    # Obtém relatório de progresso
    progress = timeline.get_progress_report()
    print(f"\nProgresso do Projeto:")
    print(f"Total de marcos: {progress['total_milestones']}")
    print(f"Concluídos: {progress['completed']}")
    print(f"Em andamento: {progress['in_progress']}")
    print(f"Pendentes: {progress['pending']}")
    print(f"Porcentagem concluída: {progress['progress_percentage']:.1f}%")