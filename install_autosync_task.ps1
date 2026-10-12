<#
    install_autosync_task.ps1
    ---------------------------------------------------------------------------
    Installe (ou désinstalle) la tâche planifiée Windows qui lance la synchro
    Access -> Supabase automatiquement, SANS que personne ait à y penser.

    Déclencheurs posés :
      * À l'ouverture de session de l'utilisateur  (=> chaque matin au démarrage du PC)
      * Tous les jours à l'heure choisie            (=> si le PC reste allumé)
    Avec "StartWhenAvailable" : si le PC était éteint à l'heure prévue, la tâche
    se lance dès qu'il est rallumé (rattrapage). => peu importe que le PC dorme la nuit.

    EXEMPLES
      # Installation standard (adapter les chemins) :
      powershell -ExecutionPolicy Bypass -File .\install_autosync_task.ps1 `
          -ExePath "C:\Multirex\MultirexDMS_AutoSync.exe" `
          -AccdbPath "C:\Multirex\Achats_données.accdb" `
          -DailyTime "12:30"

      # Désinstaller :
      powershell -ExecutionPolicy Bypass -File .\install_autosync_task.ps1 -Unregister

    N'exige PAS de droits administrateur : la tâche tourne pour l'utilisateur courant.
#>

param(
    [string]$ExePath = "",
    [string]$AccdbPath = "",
    [string]$DailyTime = "12:30",
    [string]$TaskName = "MultirexDMS AutoSync",
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"

function Fail($msg) { Write-Host "ERREUR: $msg" -ForegroundColor Red; exit 1 }

# --- Désinstallation ---------------------------------------------------------
if ($Unregister) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Tâche « $TaskName » supprimée." -ForegroundColor Green
    } else {
        Write-Host "Aucune tâche « $TaskName » à supprimer."
    }
    exit 0
}

# --- Résolution des chemins par défaut --------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ExePath)) {
    $ExePath = Join-Path $scriptDir "MultirexDMS_AutoSync.exe"
}
if (-not (Test-Path $ExePath)) {
    Fail "Exe introuvable: $ExePath`n   Construis-le d'abord (voir AUTOSYNC.md) ou passe -ExePath."
}

if ([string]::IsNullOrWhiteSpace($AccdbPath)) {
    Fail "Chemin de la base Access manquant. Passe -AccdbPath `"C:\...\Achats_données.accdb`""
}
if (-not (Test-Path $AccdbPath)) {
    Write-Host "ATTENTION: la base $AccdbPath n'existe pas encore (la tâche échouera tant qu'elle manque)." -ForegroundColor Yellow
}

# On écrit le chemin de la base à côté de l'exe (l'exe le relit tout seul).
$exeDir = Split-Path -Parent $ExePath
$cfg = Join-Path $exeDir "accdb_path.txt"
Set-Content -Path $cfg -Value $AccdbPath -Encoding UTF8
Write-Host "Chemin de la base enregistré dans $cfg"

# --- Construction de la tâche ------------------------------------------------
$action = New-ScheduledTaskAction -Execute $ExePath -Argument ('"{0}"' -f $AccdbPath) -WorkingDirectory $exeDir

$trigLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$trigDaily = New-ScheduledTaskTrigger -Daily -At $DailyTime

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Ancienne tâche remplacée."
}

Register-ScheduledTask -TaskName $TaskName `
    -Action $action -Trigger @($trigLogon, $trigDaily) `
    -Settings $settings -Principal $principal `
    -Description "Synchronise la base Access Multirex vers Supabase (ouverture de session + quotidienne, avec rattrapage)." | Out-Null

Write-Host ""
Write-Host "✅ Tâche « $TaskName » installée." -ForegroundColor Green
Write-Host "   - Se lance à chaque ouverture de session et chaque jour à $DailyTime"
Write-Host "   - Rattrape automatiquement si le PC était éteint"
Write-Host ""
Write-Host "TESTER MAINTENANT (lance la synchro tout de suite) :" -ForegroundColor Cyan
Write-Host "   Start-ScheduledTask -TaskName `"$TaskName`""
Write-Host "VOIR LE JOURNAL LOCAL :"
Write-Host "   Get-Content `"$exeDir\logs\autosync.log`" -Tail 20"
Write-Host "ÉTAT DE LA DERNIÈRE EXÉCUTION :"
Write-Host "   Get-ScheduledTaskInfo -TaskName `"$TaskName`""
