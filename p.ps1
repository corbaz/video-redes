Clear-Host
Write-Host "Matando procesos Python existentes..."
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "pythonw" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Procesos Python terminados."
Write-Host ""
Write-Host "Iniciando servidor..."
python server.py
Read-Host "Presione Enter para continuar..."
