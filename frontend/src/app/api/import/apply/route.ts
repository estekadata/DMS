import { NextRequest, NextResponse } from "next/server";
import { spawn } from "node:child_process";
import { unlink } from "node:fs/promises";
import path from "node:path";
import { getSession } from "@/lib/auth";

export const dynamic = "force-dynamic";
export const maxDuration = 600;

const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const SCRIPT_PATH = path.join(PROJECT_ROOT, "sync_access.py");
const UPLOAD_DIR = path.join(PROJECT_ROOT, "uploads");
const PYTHON_BIN = process.env.PYTHON_BIN || "python3";

function runSync(accdbPath: string, user: string | null) {
  return new Promise<unknown>((resolve, reject) => {
    const args = [SCRIPT_PATH, "--accdb", accdbPath, "--mode", "apply"];
    if (user) args.push("--user", user);

    const proc = spawn(PYTHON_BIN, args, {
      cwd: PROJECT_ROOT,
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (b) => (stdout += b.toString()));
    proc.stderr.on("data", (b) => (stderr += b.toString()));
    proc.on("error", (e) => reject(e));
    proc.on("close", () => {
      try {
        const trimmed = stdout.trim();
        const lastBrace = trimmed.lastIndexOf("\n");
        const jsonStr = lastBrace === -1 ? trimmed : trimmed.slice(lastBrace + 1);
        resolve(JSON.parse(jsonStr));
      } catch {
        reject(
          new Error(
            `Sortie inattendue.\nstdout: ${stdout}\nstderr: ${stderr}`,
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

  const { upload_id, ext } = (await req.json()) as { upload_id: string; ext?: string };
  if (!upload_id || !/^[0-9a-f-]{36}$/i.test(upload_id)) {
    return NextResponse.json({ error: "upload_id invalide" }, { status: 400 });
  }
  const fileExt = ext === "mdb" ? ".mdb" : ".accdb";
  const accdbPath = path.join(UPLOAD_DIR, `${upload_id}${fileExt}`);

  try {
    const result = await runSync(accdbPath, session.email || null);
    // Cleanup : on ne garde pas les .accdb sur disque
    await unlink(accdbPath).catch(() => {});
    return NextResponse.json(result);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erreur sync" },
      { status: 500 },
    );
  }
}
