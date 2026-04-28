# DMS Sync Access Worker

Service FastAPI qui expose `sync_access.py` en HTTP, déployable sur Railway.

## Architecture

```
[Browser] ──upload chunks──> [Railway worker] ──UPSERT──> [Supabase]
                                  ▲
                                  │ POST /preview, /apply
                                  │
[Browser] ──direct call──────────┘
```

Le frontend Vercel parle **directement** au worker (pas de proxy via Vercel).
Cela évite la limite de 4,5 MB sur les Serverless Functions Vercel.

## Endpoints

- `GET  /health` — healthcheck (Railway s'en sert)
- `POST /upload-chunk` — upload un morceau de fichier (chunked)
- `POST /preview` — analyse dry-run du .accdb (renvoie new/updated par table)
- `POST /apply` — effectue l'UPSERT vers Supabase

## Variables d'environnement nécessaires

| Var | Valeur | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres.xxx:pwd@aws-1-eu-west-1.pooler.supabase.com:6543/postgres` | URL pooler Supabase |
| `CORS_ORIGINS` | `https://dms-frontend-phi-six.vercel.app,http://localhost:3000` | Domaines autorisés |
| `PORT` | `8080` (Railway le set automatiquement) | Port d'écoute |

## Déployer sur Railway (5 minutes)

### 1. Push le code sur GitHub
```bash
cd /home/valentin/DMS/Script
git add worker/ sync_access.py
git commit -m "Add FastAPI worker for Railway"
git push origin main
```

### 2. Créer un projet Railway
1. Va sur https://railway.com/new
2. "Deploy from GitHub repo" → sélectionne `estekadata/DMS`
3. Railway détecte le `Dockerfile` dans `worker/`
4. Si Railway demande un dossier de build, mets : **`Script/`** (parent de `worker/`)
   - Le Dockerfile copie `sync_access.py` ET `worker/main.py` depuis `Script/`

### 3. Configurer les variables d'env Railway
Dans Railway → ton service → Variables :
- `DATABASE_URL` : copie depuis ton fichier `Script/Transfert_supabase.py` ou Supabase dashboard
- `CORS_ORIGINS` : `https://dms-frontend-phi-six.vercel.app,http://localhost:3000`

### 4. Récupérer l'URL publique du worker
Railway → ton service → Settings → "Generate domain"
→ Tu obtiens une URL du genre `https://dms-worker-production.up.railway.app`

### 5. Tester l'URL
```bash
curl https://dms-worker-production.up.railway.app/health
# Doit renvoyer : {"ok":true,"script":"/app/sync_access.py","upload_dir":"/tmp/uploads"}
```

### 6. Configurer Vercel
Vercel dashboard → ton projet → Settings → Environment Variables :
- Nom : `NEXT_PUBLIC_WORKER_URL`
- Valeur : `https://dms-worker-production.up.railway.app` (sans slash final)
- Environments : Production + Preview

Puis redéploie (`git push` ou bouton "Redeploy").

### 7. C'est en ligne !
Va sur `https://dms-frontend-phi-six.vercel.app/admin/import-donnees`,
le bouton "Lancer la validation" appellera maintenant Railway.

## Tester en local

Tu peux aussi lancer le worker en local :
```bash
cd /home/valentin/DMS/Script
pip install -r worker/requirements.txt
DATABASE_URL="postgresql://..." uvicorn worker.main:app --reload --port 8080
```

Puis en plus, dans `Script/frontend/.env.local` :
```
NEXT_PUBLIC_WORKER_URL=http://localhost:8080
```
→ le frontend appellera ton worker local au lieu de Vercel/Railway.

## Coûts estimés

Railway gratuit jusqu'à 5$ de crédit/mois. Pour ce worker :
- Au repos : ~0.50$/mois (idle)
- Pendant un import : ~5 min de CPU, négligeable
- Total : largement dans le free tier
