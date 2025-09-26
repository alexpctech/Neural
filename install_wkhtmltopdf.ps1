Write-Host "Instalando wkhtmltopdf..."
$url = "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe"
$output = "wkhtmltox-installer.exe"

# Download do instalador
Invoke-WebRequest -Uri $url -OutFile $output

# Executar instalador
Start-Process -FilePath $output -ArgumentList "/S" -Wait

# Limpar arquivo de instalação
Remove-Item $output

Write-Host "wkhtmltopdf instalado com sucesso!"