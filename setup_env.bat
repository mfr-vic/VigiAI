@echo off
setlocal
echo ===============================================
echo   VigiAI - setup de ambiente (Windows + venv)
echo ===============================================

python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Exemplos de uso:
echo   set EE_PROJECT_ID=aps-vigiai
echo   python main.py --download --config config.manaus.json
echo   python main.py --ndvi
echo   python main.py --train
echo   python main.py --predict
echo   python main.py --dashboard
echo.
pause
endlocal
