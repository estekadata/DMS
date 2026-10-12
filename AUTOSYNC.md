# Synchro automatique Multirex (AutoSync)

Objectif : **la base se synchronise toute seule**, sans que Karine ou Olivier aient
à lancer quoi que ce soit. Fini le « plus aucune synchro depuis X jours ».

## Comment ça marche

- Un petit programme **`MultirexDMS_AutoSync.exe`** (sans fenêtre) lit la base
  `Achats_données.accdb` et pousse les nouveautés vers Supabase — exactement la
  même logique que l'updater manuel, mais silencieuse.
- Une **tâche planifiée Windows** le lance automatiquement :
  - **à chaque ouverture de session** (donc chaque matin quand le PC démarre) ;
  - **une fois par jour** à une heure choisie (si le PC reste allumé) ;
  - avec **rattrapage** : si le PC était éteint à l'heure prévue, ça part dès qu'il rallume.
- Chaque exécution est tracée dans **`import_log`** (visible sur la page
  *Synchronisation* du site) **et** dans un **journal local** `logs/autosync.log`.

> La base `.accdb` ne quitte pas le PC : la synchro se fait depuis le PC du client,
> seuls les changements partent vers Supabase (connexion chiffrée).

---

## 1. Construire l'exe (une seule fois, sur une machine Windows)

```powershell
# dans le dossier Script\
pip install pyinstaller pyodbc pandas sqlalchemy psycopg2-binary
pyinstaller --onefile --name MultirexDMS_AutoSync auto_sync.py
# -> génère dist\MultirexDMS_AutoSync.exe
```

`auto_sync.py` importe `sync_access.py` : pyinstaller l'embarque automatiquement.
Il faut **construire l'exe sur Windows** (le driver Access `pyodbc` est Windows).

## 2. Déployer sur le PC du client

1. Créer un dossier, p. ex. `C:\Multirex\`.
2. Y copier **`MultirexDMS_AutoSync.exe`**.
3. Repérer le chemin exact de la base, p. ex. `C:\Multirex\Achats_données.accdb`.
   - Pré-requis PC : le **driver Access** (Microsoft Access Database Engine 2016
     Redistributable, version x64) doit être installé. C'est déjà le cas si
     l'updater manuel fonctionnait sur ce PC.

## 3. Installer la tâche planifiée

Copier aussi `install_autosync_task.ps1` dans `C:\Multirex\`, puis :

```powershell
powershell -ExecutionPolicy Bypass -File C:\Multirex\install_autosync_task.ps1 `
    -ExePath "C:\Multirex\MultirexDMS_AutoSync.exe" `
    -AccdbPath "C:\Multirex\Achats_données.accdb" `
    -DailyTime "12:30"
```

Pas besoin d'être administrateur : la tâche tourne pour l'utilisateur courant.
Choisir une **heure de journée** (ex. 12:30) où le PC est normalement allumé —
l'ouverture de session couvre déjà le démarrage du matin.

## 4. Tester tout de suite

```powershell
Start-ScheduledTask -TaskName "MultirexDMS AutoSync"
# patienter 1-3 min, puis :
Get-Content "C:\Multirex\logs\autosync.log" -Tail 20
```

Ligne attendue : `OK — N ajoutées, M modifiées, ...`.
Puis vérifier la page **Synchronisation** du site : la date doit être « à l'instant ».

---

## Dépannage

| Symptôme (dans `autosync.log`) | Cause / solution |
|---|---|
| `base Access introuvable` | Mauvais chemin : corriger `accdb_path.txt` (à côté de l'exe) ou relancer l'installateur avec le bon `-AccdbPath`. |
| `driver Access (pyodbc)` | Installer *Microsoft Access Database Engine 2016 Redistributable* (x64). |
| `tables manquantes dans le .accdb` | Le fichier choisi n'est pas la bonne base Multirex. |
| `TERMINÉ AVEC ERREURS … table(s) en échec` | Une table a un souci de données ; le détail est dans le log et dans `import_log`. Les autres tables sont quand même synchronisées. |

Commandes utiles :

```powershell
Get-ScheduledTaskInfo -TaskName "MultirexDMS AutoSync"   # dernière exécution + prochain déclenchement + code retour
Get-ScheduledTask     -TaskName "MultirexDMS AutoSync"   # état (Ready / Running)
```

Désinstaller :

```powershell
powershell -ExecutionPolicy Bypass -File C:\Multirex\install_autosync_task.ps1 -Unregister
```

---

## Notes

- **Codes retour de l'exe** : `0` succès · `1` au moins une table en échec ·
  `2` base introuvable · `3` driver Access manquant · `4` tables manquantes.
- L'updater manuel (`MultirexDMS_Updater.exe`) **reste utilisable** quand on veut
  forcer une synchro avec aperçu ; les deux écrivent dans `import_log` sans conflit.
- L'incrémental empêche les doublons (UPSERT par clé) : lancer la tâche plusieurs
  fois par jour ne casse rien.
