@echo off
echo ========================================================
echo   RADAR AMBIENTAL DE IGUATU - ATUALIZACAO MENSAL
echo ========================================================
echo.
echo Iniciando conexao com a Receita Federal...
echo Isso pode demorar algumas horas dependendo da internet.
echo Nao feche essa janela.
echo.

cd /d "C:\Users\breno\.gemini\antigravity\scratch\radar_ambiental_iguatu"
python receita_worker.py

echo.
echo ========================================================
echo   PROCESSO FINALIZADO!
echo ========================================================
pause
