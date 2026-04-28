import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { getSession } from "@/lib/auth";

export const dynamic = "force-dynamic";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
);

/**
 * Renvoie l'état d'avancement du dernier import (mode='apply').
 * Le client poll cet endpoint pendant que l'apply tourne.
 */
export async function GET(req: NextRequest) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  if (session.role !== "super_admin" && session.role !== "admin") {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const uploadId = req.nextUrl.searchParams.get("upload_id");

  let query = supabase
    .from("import_log")
    .select(
      "table_name, started_at, finished_at, rows_read, rows_inserted, rows_updated, rows_skipped, mode, source_file",
    )
    .eq("mode", "apply")
    .order("started_at", { ascending: false })
    .limit(50);

  // Filtre sur le upload_id (présent dans le nom du fichier sur disque, ex: <uuid>.accdb)
  if (uploadId && /^[0-9a-f-]{36}$/i.test(uploadId)) {
    query = query.like("source_file", `${uploadId}%`);
  } else {
    // Fallback : on ne montre que les apply des 30 dernières minutes
    const since = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    query = query.gte("started_at", since);
  }

  const { data, error } = await query;
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // Garde la dernière entrée par table_name
  const seen = new Set<string>();
  const latest = (data || []).filter((r) => {
    if (seen.has(r.table_name)) return false;
    seen.add(r.table_name);
    return true;
  });

  return NextResponse.json({
    rows: latest.sort((a, b) =>
      a.started_at < b.started_at ? -1 : 1,
    ),
  });
}
