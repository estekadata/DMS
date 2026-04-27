"use client";

import { useRef, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

type TableStat = {
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
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setApplyResult(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  async function runPreview() {
    if (!file) return;
    setPreview(null);
    setApplyResult(null);
    setPreviewing(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch("/api/import/preview", { method: "POST", body: fd });
      const data: SyncResult = await r.json();
      if (!r.ok) {
        throw new Error((data as unknown as { error?: string }).error || "Erreur preview");
      }
      setPreview(data);
      if (!data.ok) {
        toast.error("Validation échouée — vérifie les erreurs ci-dessous");
      } else {
        toast.success("Preview généré — vérifie avant de confirmer");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur preview");
    } finally {
      setPreviewing(false);
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
    try {
      const ext = file.name.toLowerCase().endsWith(".mdb") ? "mdb" : "accdb";
      const r = await fetch("/api/import/apply", {
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
              {previewing ? "Analyse en cours..." : "→ Lancer la validation"}
            </Button>
            {(file || preview) && (
              <Button variant="outline" onClick={reset}>
                Réinitialiser
              </Button>
            )}
          </div>
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

      {/* Étape 3 : Résultat */}
      {applyResult && (
        <Card>
          <CardContent className="p-6">
            <h2 className="font-heading font-bold text-lg mb-3">3. Résultat de l&apos;import</h2>
            <div className="text-sm">
              <Badge variant={applyResult.ok ? "default" : "destructive"} className="mb-3">
                {applyResult.ok ? "✅ Succès" : "⚠️ Partiel"}
              </Badge>
              <p className="text-text-dim">
                {applyResult.totals?.new ?? 0} ajout(s) • {applyResult.totals?.updated ?? 0}{" "}
                modif(s) • {applyResult.totals?.errors ?? 0} erreur(s)
              </p>
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
