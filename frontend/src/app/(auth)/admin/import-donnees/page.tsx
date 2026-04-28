"use client";

import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

type LiveProgress = {
  table_name: string;
  started_at: string;
  finished_at: string | null;
  rows_read: number;
  rows_inserted: number;
  rows_updated: number;
  rows_skipped: number;
  source_file: string;
};

type TableStat = {
  table: string;
  access_table: string;
  strategy: string;
  rows_read: number;
  new: number;
  updated: number;
  total: number;
  errors: number;
  error_samples?: string[];
  last_sync: string | null;
  applied: boolean;
};

type SyncResult = {
  ok: boolean;
  mode: string;
  tables: TableStat[];
  totals?: { new: number; updated: number; errors: number };
  errors?: Array<{ stage: string; message: string }>;
  validation?: { tables_found: number; missing: string[] };
  upload_id?: string;
};

const STRATEGY_LABEL: Record<string, string> = {
  incremental_datemodif: "Incrémental (DateModif)",
  incremental_date_metier: "Incrémental (date métier)",
  full_reload: "Référentiel (full reload)",
};

export default function ImportDonneesPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<SyncResult | null>(null);
  const [applying, setApplying] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [applyResult, setApplyResult] = useState<SyncResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);
  const [liveProgress, setLiveProgress] = useState<LiveProgress[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // 4 MB pour rester sous la limite Vercel (4.5 MB) si le worker n'est pas configuré
  const CHUNK_SIZE = 4 * 1024 * 1024;
  const TOTAL_TABLES = 14;

  // Si NEXT_PUBLIC_WORKER_URL est défini (en prod sur Vercel) → on parle direct au worker.
  // Sinon → on passe par les routes Next.js locales (qui spawn Python en local).
  const WORKER_URL = process.env.NEXT_PUBLIC_WORKER_URL || "";
  const apiUrl = (path: string) =>
    WORKER_URL ? `${WORKER_URL}${path}` : `/api/import${path}`;

  // Pendant l'apply, poll l'endpoint /status toutes les 2s pour voir l'avancement
  useEffect(() => {
    if (!applying) return;
    const uploadId = preview?.upload_id;
    let cancelled = false;

    async function tick() {
      try {
        const url = uploadId
          ? `/api/import/status?upload_id=${uploadId}`
          : `/api/import/status`;
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) return;
        const data = await r.json();
        if (!cancelled) setLiveProgress(data.rows || []);
      } catch {
        // silencieux
      }
    }

    tick(); // 1er fetch immédiat
    const interval = setInterval(tick, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [applying, preview?.upload_id]);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setApplyResult(null);
    setLiveProgress([]);
    if (inputRef.current) inputRef.current.value = "";
  };

  async function runPreview() {
    if (!file) return;
    setPreview(null);
    setApplyResult(null);
    setPreviewing(true);
    try {
      // 1. Upload chunké du fichier (la limite Next/Turbopack est ~10 MB par requête)
      const uploadId = crypto.randomUUID();
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      setUploadProgress({ current: 0, total: totalChunks });

      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);
        const cr = await fetch(apiUrl("/upload-chunk"), {
          method: "POST",
          headers: {
            "X-Upload-Id": uploadId,
            "X-Chunk-Index": String(i),
            "X-Total-Chunks": String(totalChunks),
            "X-Filename": file.name,
            "Content-Type": "application/octet-stream",
          },
          body: chunk,
        });
        if (!cr.ok) {
          const txt = await cr.text();
          throw new Error(`Chunk ${i + 1}/${totalChunks} échoué : ${txt.slice(0, 200)}`);
        }
        setUploadProgress({ current: i + 1, total: totalChunks });
      }

      // 2. Lancer le preview sur le fichier reconstitué
      const ext = file.name.toLowerCase().endsWith(".mdb") ? "mdb" : "accdb";
      const r = await fetch(apiUrl("/preview"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: uploadId, ext }),
      });
      // Lire la réponse en texte d'abord (au cas où ce ne serait pas du JSON)
      const raw = await r.text();
      let data: SyncResult & { error?: string; hint?: string };
      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error(
          `Réponse non-JSON du serveur (HTTP ${r.status}). ` +
            `Premiers caractères: ${raw.slice(0, 200)}`,
        );
      }
      if (!r.ok) {
        const hint = data.hint ? `\n💡 ${data.hint}` : "";
        throw new Error((data.error || "Erreur preview") + hint);
      }
      setPreview(data);
      if (!data.ok) {
        toast.error("Validation échouée — vérifie les erreurs ci-dessous");
      } else {
        toast.success("Preview généré — vérifie avant de confirmer");
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erreur preview";
      toast.error(msg, { duration: 15000, style: { whiteSpace: "pre-wrap" } });
    } finally {
      setPreviewing(false);
      setUploadProgress(null);
    }
  }

  async function runApply() {
    if (!preview?.upload_id || !file) return;
    if (
      !confirm(
        "Confirmer l'import ? Les données Supabase vont être mises à jour.\n" +
          "Cette opération est irréversible (mais loggée).",
      )
    )
      return;
    setApplying(true);
    setLiveProgress([]);
    try {
      const ext = file.name.toLowerCase().endsWith(".mdb") ? "mdb" : "accdb";
      const r = await fetch(apiUrl("/apply"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: preview.upload_id, ext }),
      });
      const data: SyncResult = await r.json();
      if (!r.ok) {
        throw new Error((data as unknown as { error?: string }).error || "Erreur import");
      }
      setApplyResult(data);
      if (data.ok) toast.success("Import terminé avec succès");
      else toast.error("Import partiel — vérifie les erreurs");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur import");
    } finally {
      setApplying(false);
    }
  }

  const showStats = applyResult ?? preview;

  return (
    <div>
      <PageHeader
        title="Import des données depuis Access"
        description="Met à jour Supabase à partir d'un fichier .accdb (ou .mdb)"
      />

      {/* Étape 1 : Upload */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <h2 className="font-heading font-bold text-lg mb-1">
            1. Sélectionner le fichier Access
          </h2>
          <p className="text-sm text-text-dim mb-4">
            Le fichier doit contenir au minimum les tables :{" "}
            <code className="text-xs bg-surface-alt px-1 rounded">tbl MOTEURS</code>,{" "}
            <code className="text-xs bg-surface-alt px-1 rounded">tbl BOITES</code>,{" "}
            <code className="text-xs bg-surface-alt px-1 rounded">tbl RECEPTIONS</code>, etc.
          </p>
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="file"
              accept=".accdb,.mdb"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setPreview(null);
                setApplyResult(null);
              }}
              className="block text-sm file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-brand file:text-white file:cursor-pointer hover:file:bg-brand/90"
            />
            {file && (
              <span className="text-sm text-text-dim">
                {file.name} • {(file.size / 1024 / 1024).toFixed(1)} MB
              </span>
            )}
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={runPreview} disabled={!file || previewing}>
              {previewing
                ? uploadProgress
                  ? `Upload ${uploadProgress.current}/${uploadProgress.total}...`
                  : "Analyse en cours..."
                : "→ Lancer la validation"}
            </Button>
            {(file || preview) && (
              <Button variant="outline" onClick={reset}>
                Réinitialiser
              </Button>
            )}
          </div>
          {uploadProgress && (
            <div className="mt-3">
              <div className="h-2 w-full bg-surface-alt rounded overflow-hidden">
                <div
                  className="h-full bg-brand transition-all"
                  style={{
                    width: `${(uploadProgress.current / uploadProgress.total) * 100}%`,
                  }}
                />
              </div>
              <p className="text-xs text-text-dim mt-1">
                {Math.round((uploadProgress.current / uploadProgress.total) * 100)}% —
                chunk {uploadProgress.current}/{uploadProgress.total}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Étape 2 : Validation + preview */}
      {preview && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="font-heading font-bold text-lg mb-3">
              2. Validation & aperçu des changements
            </h2>

            {preview.validation && (
              <div className="mb-4 text-sm">
                <Badge variant={preview.validation.missing.length === 0 ? "default" : "destructive"}>
                  {preview.validation.missing.length === 0
                    ? `✅ ${preview.validation.tables_found} tables détectées`
                    : `⛔ ${preview.validation.missing.length} table(s) manquante(s)`}
                </Badge>
                {preview.validation.missing.length > 0 && (
                  <p className="text-red-600 mt-2 text-xs">
                    Manquant : {preview.validation.missing.join(", ")}
                  </p>
                )}
              </div>
            )}

            {preview.errors && preview.errors.length > 0 && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm">
                <p className="font-semibold text-red-700 mb-1">Erreurs :</p>
                <ul className="list-disc ml-5 text-red-700">
                  {preview.errors.map((e, i) => (
                    <li key={i}>
                      <strong>{e.stage}</strong> : {e.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {preview.totals && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <Card>
                  <CardContent className="p-3">
                    <p className="text-xs text-text-dim font-semibold uppercase">
                      Nouvelles lignes
                    </p>
                    <p className="text-2xl font-bold text-emerald-600">
                      {preview.totals.new}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3">
                    <p className="text-xs text-text-dim font-semibold uppercase">
                      Lignes modifiées
                    </p>
                    <p className="text-2xl font-bold text-amber-600">
                      {preview.totals.updated}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3">
                    <p className="text-xs text-text-dim font-semibold uppercase">
                      Erreurs détectées
                    </p>
                    <p className="text-2xl font-bold text-red-600">
                      {preview.totals.errors}
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            <TableStatsTable rows={showStats?.tables ?? []} />

            {preview.ok && (preview.totals?.new || preview.totals?.updated) ? (
              <div className="mt-5 flex gap-2">
                <Button onClick={runApply} disabled={applying || !!applyResult}>
                  {applying
                    ? "Import en cours..."
                    : applyResult
                      ? "✅ Import effectué"
                      : "✅ Confirmer et importer"}
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Live progress pendant l'apply */}
      {applying && (
        <Card className="mb-6 border-amber-300">
          <CardContent className="p-6">
            <h2 className="font-heading font-bold text-lg mb-3">
              ⏳ Import en cours — {liveProgress.length}/{TOTAL_TABLES} tables traitées
            </h2>
            <div className="h-2 w-full bg-surface-alt rounded overflow-hidden mb-4">
              <div
                className="h-full bg-amber-500 transition-all"
                style={{
                  width: `${(liveProgress.length / TOTAL_TABLES) * 100}%`,
                }}
              />
            </div>
            <div className="overflow-x-auto rounded border border-border">
              <table className="w-full text-sm">
                <thead className="bg-surface-alt text-text-dim">
                  <tr>
                    <th className="text-left p-2 font-semibold">Table</th>
                    <th className="text-right p-2 font-semibold">Lignes lues</th>
                    <th className="text-right p-2 font-semibold text-emerald-600">
                      ⊕ Nouvelles
                    </th>
                    <th className="text-right p-2 font-semibold text-amber-600">
                      ✎ Modifiées
                    </th>
                    <th className="text-right p-2 font-semibold text-red-600">
                      ⚠ Erreurs
                    </th>
                    <th className="text-left p-2 font-semibold">Heure</th>
                  </tr>
                </thead>
                <tbody>
                  {liveProgress.map((r) => (
                    <tr key={r.table_name} className="border-t border-border">
                      <td className="p-2 font-mono text-xs">{r.table_name}</td>
                      <td className="p-2 text-right">{r.rows_read}</td>
                      <td className="p-2 text-right text-emerald-600 font-semibold">
                        {r.rows_inserted || "—"}
                      </td>
                      <td className="p-2 text-right text-amber-600 font-semibold">
                        {r.rows_updated || "—"}
                      </td>
                      <td className="p-2 text-right text-red-600">
                        {r.rows_skipped || "—"}
                      </td>
                      <td className="p-2 text-xs text-text-dim">
                        {new Date(r.started_at).toLocaleTimeString("fr-FR")}
                      </td>
                    </tr>
                  ))}
                  {liveProgress.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        className="p-4 text-center text-text-dim text-xs"
                      >
                        Initialisation... (la 1re table apparaîtra dans quelques secondes)
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Étape 3 : Résultat */}
      {applyResult && (
        <Card>
          <CardContent className="p-6">
            <h2 className="font-heading font-bold text-lg mb-3">3. Résultat de l&apos;import</h2>
            <div className="text-sm">
              <Badge variant={applyResult.ok ? "default" : "destructive"} className="mb-3">
                {applyResult.ok ? "✅ Succès" : "⚠️ Partiel"}
              </Badge>
              <p className="text-text-dim mb-3">
                {applyResult.totals?.new ?? 0} ajout(s) • {applyResult.totals?.updated ?? 0}{" "}
                modif(s) • {applyResult.totals?.errors ?? 0} erreur(s)
              </p>
              {applyResult.errors && applyResult.errors.length > 0 && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md mb-3">
                  <p className="font-semibold text-red-700 mb-1">
                    Erreurs globales ({applyResult.errors.length}) :
                  </p>
                  <ul className="list-disc ml-5 text-red-700 text-xs space-y-1">
                    {applyResult.errors.map((e, i) => (
                      <li key={i}>
                        <strong>{e.stage}</strong> : {e.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {applyResult.tables &&
                applyResult.tables
                  .filter((t) => t.error_samples && t.error_samples.length > 0)
                  .map((t) => (
                    <div
                      key={t.table}
                      className="p-3 bg-amber-50 border border-amber-200 rounded-md mb-2"
                    >
                      <p className="font-semibold text-amber-800 mb-1">
                        ⚠️ {t.table} : {t.errors} ligne(s) en échec — exemples :
                      </p>
                      <ul className="list-disc ml-5 text-amber-900 text-xs space-y-1 font-mono">
                        {t.error_samples!.slice(0, 5).map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TableStatsTable({ rows }: { rows: TableStat[] }) {
  if (!rows.length) return null;
  return (
    <div className="overflow-x-auto rounded border border-border">
      <table className="w-full text-sm">
        <thead className="bg-surface-alt text-text-dim">
          <tr>
            <th className="text-left p-2 font-semibold">Table</th>
            <th className="text-left p-2 font-semibold">Stratégie</th>
            <th className="text-right p-2 font-semibold">Lues</th>
            <th className="text-right p-2 font-semibold text-emerald-600">Nouvelles</th>
            <th className="text-right p-2 font-semibold text-amber-600">Modifiées</th>
            <th className="text-right p-2 font-semibold text-red-600">Erreurs</th>
            <th className="text-left p-2 font-semibold">Dernière sync</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.table} className="border-t border-border">
              <td className="p-2 font-mono text-xs">{r.table}</td>
              <td className="p-2 text-xs">{STRATEGY_LABEL[r.strategy] ?? r.strategy}</td>
              <td className="p-2 text-right">{r.rows_read}</td>
              <td className="p-2 text-right text-emerald-600 font-semibold">
                {r.new || "—"}
              </td>
              <td className="p-2 text-right text-amber-600 font-semibold">
                {r.updated || "—"}
              </td>
              <td className="p-2 text-right text-red-600">{r.errors || "—"}</td>
              <td className="p-2 text-xs text-text-dim">
                {r.last_sync
                  ? new Date(r.last_sync).toLocaleString("fr-FR", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })
                  : "jamais"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
