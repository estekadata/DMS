import { NextRequest, NextResponse } from "next/server";
import { spawn } from "node:child_process";
import { stat } from "node:fs/promises";
import path from "node:path";
import { getSession } from "@/lib/auth";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const SCRIPT_PATH = path.join(PROJECT_ROOT, "sync_access.py");
const UPLOAD_DIR = path.join(PROJECT_ROOT, "uploads");
const PYTHON_BIN = process.env.PYTHON_BIN || "python3";

type SyncResult = {
  ok: boolean;
  mode: string;
  tables?: Array<{
    table: string;
    access_table: string;
    strategy: string;
    rows_read: number;
    new: number;
    updated: number;
    total: number;
    errors: number;
    last_sync: string | null;
    applied: boolean;
  }>;
  totals?: { new: number; updated: number; errors: number };
  errors?: Array<{ stage: string; message: string }>;
  validation?: { tables_found: number; missing: string[] };
  upload_id?: string;
};

function runSync(accdbPath: string, mode: "preview" | "apply", user: string | null) {
  return new Promise<SyncResult>((resolve, reject) => {
    const args = [SCRIPT_PATH, "--accdb", accdbPath, "--mode", mode];
    if (user) args.push("--user", user);

    const proc = spawn(PYTHON_BIN, args, {
      cwd: PROJECT_ROOT,
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (b) => (stdout += b.toString()));
    proc.stderr.on("data", (b) => (stderr += b.toString()));

    proc.on("error", (err) => reject(err));
    proc.on("close", () => {
      try {
        const trimmed = stdout.trim();
        const lastBrace = trimmed.lastIndexOf("\n");
        const jsonStr = lastBrace === -1 ? trimmed : trimmed.slice(lastBrace + 1);
        const parsed = JSON.parse(jsonStr) as SyncResult;
        resolve(parsed);
      } catch {
        reject(
          new Error(
            `Impossible de parser la sortie du script.\nstdout: ${stdout}\nstderr: ${stderr}`,
          ),
        );
      }
    });
  });
}

export async function POST(req: NextRequest) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
    if (session.role !== "super_admin" && session.role !== "admin") {
      return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
    }

    const { upload_id, ext } = (await req.json()) as { upload_id: string; ext?: string };
    if (!upload_id || !/^[0-9a-f-]{36}$/i.test(upload_id)) {
      return NextResponse.json({ error: "upload_id invalide" }, { status: 400 });
    }
    const fileExt = ext === "mdb" ? ".mdb" : ".accdb";
    const accdbPath = path.join(UPLOAD_DIR, `${upload_id}${fileExt}`);

    // Sanity check : fichier présent et non vide
    const stats = await stat(accdbPath).catch(() => null);
    if (!stats || stats.size === 0) {
      return NextResponse.json(
        { error: `Fichier upload introuvable ou vide (${accdbPath})` },
        { status: 400 },
      );
    }
    console.log(
      `[/api/import/preview] running on ${accdbPath} (${stats.size} bytes)`,
    );

    const result = await runSync(accdbPath, "preview", session.email || null);
    result.upload_id = upload_id;
    return NextResponse.json(result);
  } catch (e) {
    console.error("[/api/import/preview] error:", e);
    const msg = e instanceof Error ? e.message : "Erreur inconnue";
    return NextResponse.json(
      {
        error: msg,
        hint:
          "Vérifie : (1) mdbtools installé, " +
          "(2) PYTHON_BIN configuré dans .env.local, " +
          "(3) le venv contient pandas+sqlalchemy+psycopg2",
      },
      { status: 500 },
    );
  }
}
