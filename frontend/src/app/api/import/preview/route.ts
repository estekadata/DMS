import { NextRequest, NextResponse } from "next/server";
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { getSession } from "@/lib/auth";

// On ne veut surtout pas le caching pour cette route
export const dynamic = "force-dynamic";
// Augmente la limite par défaut (lecture .accdb >50 MB)
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
        // Le script écrit son JSON sur la dernière ligne stdout
        const trimmed = stdout.trim();
        const lastBrace = trimmed.lastIndexOf("\n");
        const jsonStr = lastBrace === -1 ? trimmed : trimmed.slice(lastBrace + 1);
        const parsed = JSON.parse(jsonStr) as SyncResult;
        resolve(parsed);
      } catch (e) {
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
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }
  if (session.role !== "super_admin" && session.role !== "admin") {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const formData = await req.formData();
  const file = formData.get("file") as File | null;
  if (!file) {
    return NextResponse.json({ error: "Fichier .accdb manquant" }, { status: 400 });
  }
  if (!file.name.toLowerCase().endsWith(".accdb") && !file.name.toLowerCase().endsWith(".mdb")) {
    return NextResponse.json(
      { error: "Format non supporté (attendu .accdb ou .mdb)" },
      { status: 400 },
    );
  }

  // Sauvegarde sur disque (dans Script/uploads/)
  const uploadId = randomUUID();
  const ext = file.name.toLowerCase().endsWith(".mdb") ? ".mdb" : ".accdb";
  const accdbPath = path.join(UPLOAD_DIR, `${uploadId}${ext}`);
  await mkdir(UPLOAD_DIR, { recursive: true });
  const buf = Buffer.from(await file.arrayBuffer());
  await writeFile(accdbPath, buf);

  try {
    const result = await runSync(accdbPath, "preview", session.email || null);
    result.upload_id = uploadId;
    return NextResponse.json(result);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erreur sync" },
      { status: 500 },
    );
  }
}
