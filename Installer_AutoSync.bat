@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Installation synchro automatique Multirex

echo ============================================================
echo    Installation de la synchro automatique Multirex
echo ============================================================
echo.

rem --- 1) Chemin de la base Access ---------------------------------------
rem    - soit glisse-depose le .accdb sur ce .bat (passe en argument)
rem    - soit saisis le chemin quand c'est demande
set "ACCDB=%~1"
if "%ACCDB%"=="" (
  echo Indique le chemin COMPLET de la base Access ^(Achats_donnees.accdb^).
  echo Astuce : tu peux aussi glisser-deposer le fichier .accdb sur ce .bat.
  echo.
  set /p "ACCDB=Chemin de la base : "
)
rem enleve d'eventuels guillemets
set "ACCDB=%ACCDB:"=%"

if not exist "%ACCDB%" (
  echo.
  echo [ERREUR] Fichier introuvable : "%ACCDB%"
  echo Verifie le chemin puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

set "EXE=%~dp0MultirexDMS_AutoSync.exe"
set "PS1=%~dp0install_autosync_task.ps1"
if not exist "%EXE%" (
  echo [ERREUR] MultirexDMS_AutoSync.exe est absent de ce dossier.
  pause
  exit /b 1
)
if not exist "%PS1%" (
  echo [ERREUR] install_autosync_task.ps1 est absent de ce dossier.
  pause
  exit /b 1
)

echo.
echo [1/3] Deblocage de l'exe ^(securite Windows^)...
powershell -NoProfile -Command "Unblock-File -LiteralPath '%EXE%'" 2>nul

echo [2/3] Installation de la tache planifiee...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -ExePath "%EXE%" -AccdbPath "%ACCDB%" -DailyTime "12:30"
if errorlevel 1 (
  echo.
  echo [ERREUR] L'installation de la tache a echoue ^(voir ci-dessus^).
  pause
  exit /b 1
)

echo.
echo [3/3] Test de synchronisation maintenant...
echo        La PREMIERE synchro peut durer plusieurs minutes
echo        ^(elle rattrape tout le retard^). Patiente sans fermer.
echo ------------------------------------------------------------
"%EXE%" "%ACCDB%"
set "RC=%errorlevel%"
echo ------------------------------------------------------------
if "%RC%"=="0" (
  echo RESULTAT : succes ^(code 0^).
) else (
  echo RESULTAT : code retour %RC% ^( 1=table en echec, 2=base introuvable,
  echo           3=driver Access manquant, 4=tables manquantes ^). Voir le journal.
)

echo.
echo C'est installe. Desormais la synchro se lance toute seule :
echo   - a chaque ouverture de session ^(demarrage du PC^)
echo   - une fois par jour a 12:30, avec rattrapage si le PC etait eteint.
echo.
echo Journal detaille : "%~dp0logs\autosync.log"
echo Etat de la tache : Get-ScheduledTaskInfo -TaskName "MultirexDMS AutoSync"
echo.
pause
endlocal
