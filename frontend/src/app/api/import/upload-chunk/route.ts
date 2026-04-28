import { NextRequest, NextResponse } from "next/server";
import { mkdir, appendFile, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { getSession } from "@/lib/auth";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const UPLOAD_DIR = path.join(PROJECT_ROOT, "uploads");

export async function POST(req: NextRequest) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
    if (session.role !== "super_admin" && session.role !== "admin") {
      return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
    }

    const uploadId = req.headers.get("x-upload-id") || "";
    const chunkIndex = parseInt(req.headers.get("x-chunk-index") || "-1", 10);
    const totalChunks = parseInt(req.headers.get("x-total-chunks") || "0", 10);
    const filename = req.headers.get("x-filename") || "";

    if (!/^[0-9a-f-]{36}$/i.test(uploadId)) {
      return NextResponse.json({ error: "X-Upload-Id invalide" }, { status: 400 });
    }
    if (chunkIndex < 0 || totalChunks <= 0 || chunkIndex >= totalChunks) {
      return NextResponse.json({ error: "Headers chunk invalides" }, { status: 400 });
    }
    if (!filename.toLowerCase().endsWith(".accdb") && !filename.toLowerCase().endsWith(".mdb")) {
      return NextResponse.json({ error: "Format non supporté" }, { status: 400 });
    }

    const ext = filename.toLowerCase().endsWith(".mdb") ? ".mdb" : ".accdb";
    const accdbPath = path.join(UPLOAD_DIR, `${uploadId}${ext}`);
    await mkdir(UPLOAD_DIR, { recursive: true });

    const buf = Buffer.from(await req.arrayBuffer());

    // Premier chunk : on écrase, sinon on append
    if (chunkIndex === 0) {
      await writeFile(accdbPath, buf);
    } else {
      await appendFile(accdbPath, buf);
    }

    const stats = await stat(accdbPath);
    return NextResponse.json({
      ok: true,
      chunk_received: chunkIndex,
      bytes_so_far: stats.size,
      done: chunkIndex === totalChunks - 1,
    });
  } catch (e) {
    console.error("[/api/import/upload-chunk] error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erreur upload" },
      { status: 500 },
    );
  }
}
