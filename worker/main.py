"""
FastAPI worker — wraps sync_access.py for Railway deployment.

Le frontend Vercel parle directement à ce worker via les endpoints :
  - POST /upload-chunk : upload chunké du .accdb
  - POST /preview      : analyse dry-run (renvoie new/updated par table)
  - POST /apply        : effectue l'UPSERT
  - GET  /health       : healthcheck

Auth : pas d'auth pour l'instant, on se base sur le CORS pour limiter l'accès au domaine Vercel.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# ============================================
# Config
# ============================================

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/tmp/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_PATH = os.environ.get("SYNC_SCRIPT", "/app/sync_access.py")
PYTHON_BIN = os.environ.get("PYTHON_BIN", sys.executable)

# Liste de domaines autorisés (séparés par virgules)
# Ex: "https://dms-frontend-phi-six.vercel.app,http://localhost:3000"
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS",
        "https://dms-frontend-phi-six.vercel.app,http://localhost:3000",
    ).split(",")
    if o.strip()
]

UUID_RE = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

# ============================================
# App
# ============================================

app = FastAPI(title="DMS Sync Access Worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "script": SCRIPT_PATH, "upload_dir": str(UPLOAD_DIR)}


@app.post("/upload-chunk")
async def upload_chunk(
    request: Request,
    x_upload_id: str = Header(..., alias="X-Upload-Id"),
    x_chunk_index: int = Header(..., alias="X-Chunk-Index"),
    x_total_chunks: int = Header(..., alias="X-Total-Chunks"),
    x_filename: str = Header(..., alias="X-Filename"),
):
    # Validation
    import re

    if not re.match(UUID_RE, x_upload_id):
        raise HTTPException(400, "X-Upload-Id invalide (UUID requis)")
    if x_chunk_index < 0 or x_total_chunks <= 0 or x_chunk_index >= x_total_chunks:
        raise HTTPException(400, "Headers chunk invalides")
    fname_low = x_filename.lower()
    if not (fname_low.endswith(".accdb") or fname_low.endswith(".mdb")):
        raise HTTPException(400, "Format non supporté (attendu .accdb ou .mdb)")

    ext = ".mdb" if fname_low.endswith(".mdb") else ".accdb"
    file_path = UPLOAD_DIR / f"{x_upload_id}{ext}"

    body = await request.body()

    # Premier chunk : on écrase, sinon on append
    mode = "wb" if x_chunk_index == 0 else "ab"
    with open(file_path, mode) as f:
        f.write(body)

    size = file_path.stat().st_size
    return {
        "ok": True,
        "chunk_received": x_chunk_index,
        "bytes_so_far": size,
        "done": x_chunk_index == x_total_chunks - 1,
    }


@app.post("/preview")
async def preview(payload: dict):
    return await _run(payload, "preview")


@app.post("/apply")
async def apply(payload: dict):
    result = await _run(payload, "apply")
    # Cleanup du fichier après apply réussi
    upload_id = payload.get("upload_id")
    ext = ".mdb" if payload.get("ext") == "mdb" else ".accdb"
    file_path = UPLOAD_DIR / f"{upload_id}{ext}"
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass
    return result


async def _run(payload: dict, mode: str):
    import re

    upload_id = payload.get("upload_id", "")
    if not re.match(UUID_RE, upload_id):
        raise HTTPException(400, "upload_id invalide")

    ext = ".mdb" if payload.get("ext") == "mdb" else ".accdb"
    file_path = UPLOAD_DIR / f"{upload_id}{ext}"

    if not file_path.exists():
        raise HTTPException(
            400, f"Fichier upload introuvable: {file_path.name} (re-uploade)"
        )
    if file_path.stat().st_size == 0:
        raise HTTPException(400, "Fichier upload vide")

    args = [PYTHON_BIN, SCRIPT_PATH, "--accdb", str(file_path), "--mode", mode]
    if payload.get("user"):
        args += ["--user", str(payload["user"])]

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    stderr_text = stderr.decode("utf-8", errors="replace")
    stdout_text = stdout.decode("utf-8", errors="replace")

    # Le script écrit son JSON sur la dernière ligne stdout
    try:
        last_line = stdout_text.strip().rsplit("\n", 1)[-1]
        result = json.loads(last_line)
        result["upload_id"] = upload_id
        return result
    except Exception as e:
        raise HTTPException(
            500,
            detail={
                "error": f"Sortie sync_access.py invalide: {e}",
                "stdout_tail": stdout_text[-500:],
                "stderr_tail": stderr_text[-1000:],
                "exit_code": proc.returncode,
            },
        )
