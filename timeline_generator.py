import markdown
import pdfkit
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class TimelineHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('TIMELINE_VIEW.md'):
            convert_to_pdf()

def convert_to_pdf():
    # Lê o arquivo markdown
    with open('TIMELINE_VIEW.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Converte markdown para HTML
    html_content = markdown.markdown(md_content, extensions=['extra'])
    
    # Adiciona estilos CSS
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
            }}
            h3 {{
                color: #7f8c8d;
            }}
            li {{
                margin: 5px 0;
            }}
            .concluido {{
                color: #27ae60;
            }}
            .andamento {{
                color: #f39c12;
            }}
            .planejado {{
                color: #3498db;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Salva como HTML temporário
    with open('timeline_temp.html', 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    # Converte HTML para PDF
    pdfkit.from_file('timeline_temp.html', 'TIMELINE.pdf', options={
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': 'UTF-8'
    })
    
    # Remove o arquivo HTML temporário
    Path('timeline_temp.html').unlink()
    print("Timeline atualizada em TIMELINE.pdf")

if __name__ == "__main__":
    # Faz a primeira conversão
    convert_to_pdf()
    
    # Configura o observador para atualizações automáticas
    observer = Observer()
    observer.schedule(TimelineHandler(), '.', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()