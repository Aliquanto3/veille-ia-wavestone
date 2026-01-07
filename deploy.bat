@echo off
set /p START_DATE="Date de debut (ex: 05/01) : "
set /p END_DATE="Date de fin (ex: 12/01) : "
set FILE_NAME=Veille_IA_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.html

echo --- 1/3 Generation de la veille ---
python generate_veille.py --date-start %START_DATE% --date-end %END_DATE% -o %FILE_NAME%

echo --- 2/3 Mise a jour du portail ---
python generate_portal.py

echo --- 3/3 Publication sur GitHub ---
git add .
git commit -m "Ajout veille hebdo %START_DATE% au %END_DATE%"
git push origin main

echo Done!
pause