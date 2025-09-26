import subprocess
from pathlib import Path

def convert_to_pdf():
    try:
        # Usando pandoc para converter MD para PDF
        subprocess.run([
            'pandoc',
            'TIMELINE_VIEW.md',
            '-o', 'TIMELINE.pdf',
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=1in',
            '-V', 'mainfont:Arial',
            '-V', 'monofont:Consolas',
            '--highlight-style=tango'
        ], check=True)
        print("Timeline atualizada em TIMELINE.pdf")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar PDF: {e}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    convert_to_pdf()