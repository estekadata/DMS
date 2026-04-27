"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function PrixPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [manualPrix, setManualPrix] = useState("");
  const [manualLoading, setManualLoading] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setStatus("idle");
    if (f) {
      setMessage(`Fichier sélectionné : ${f.name} (${(f.size / 1024).toFixed(1)} Ko)`);
    }
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("loading");
    setMessage("Traitement en cours...");
    const path = `prix_imports/${Date.now()}_${file.name}`;
    const { error } = await supabase.storage.from("imports").upload(path, file);
    if (error) {
      setStatus("error");
      setMessage(`Erreur upload : ${error.message}`);
      return;
    }
    setStatus("done");
    setMessage("Fichier uploadé avec succès. Le traitement sera effectué côté serveur.");
  }

  async function handleManualUpdate() {
    if (!manualCode || !manualPrix) return;
    setManualLoading(true);
    const { error } = await supabase
      .from("tbl_prix_moteurs")
      .upsert({ code_moteur: manualCode.toUpperCase(), prix_propose: parseFloat(manualPrix), date_maj: new Date().toISOString() }, { onConflict: "code_moteur" });
    if (error) {
      alert(`Erreur : ${error.message}`);
    } else {
      setManualCode("");
      setManualPrix("");
      alert("Prix mis à jour !");
    }
    setManualLoading(false);
  }

  return (
    <div>
      <PageHeader title="Mise à jour des prix" description="Import Excel et mise à jour manuelle des prix d'achat proposés" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold text-foreground mb-4">Import fichier Excel</h3>
            <p className="text-sm text-text-dim mb-4">
              Importez un fichier Excel (.xlsx) contenant les colonnes <code className="bg-surface-alt px-1 rounded text-brand">code_moteur</code> et <code className="bg-surface-alt px-1 rounded text-brand">prix_propose</code>.
            </p>
            <div className="space-y-4">
              <div>
                <Label htmlFor="file-input" className="text-text-dim">Fichier Excel</Label>
                <Input
                  id="file-input"
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                  className="mt-1 bg-surface-alt border-border text-foreground"
                />
              </div>
              {message && (
                <div className={`text-sm px-3 py-2 rounded-[10px] ${status === "error" ? "bg-[rgba(248,113,113,0.10)] text-red-600" : status === "done" ? "bg-[rgba(52,211,153,0.10)] text-emerald-600" : "bg-[rgba(96,165,250,0.10)] text-blue-600"}`}>
                  {message}
                </div>
              )}
              <Button
                onClick={handleUpload}
                disabled={!file || status === "loading"}
                className="bg-brand hover:bg-brand/80 text-white w-full rounded-[11px] h-10"
              >
                {status === "loading" ? "Upload en cours..." : "Importer le fichier"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold text-foreground mb-4">Mise à jour manuelle</h3>
            <p className="text-sm text-text-dim mb-4">
              Mettez à jour le prix d&apos;achat proposé pour une référence spécifique.
            </p>
            <div className="space-y-4">
              <div>
                <Label htmlFor="code" className="text-text-dim">Code moteur</Label>
                <Input
                  id="code"
                  placeholder="ex: N47D20A"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  className="mt-1 uppercase bg-surface-alt border-border text-foreground placeholder:text-text-muted"
                />
              </div>
              <div>
                <Label htmlFor="prix" className="text-text-dim">Prix proposé (€)</Label>
                <Input
                  id="prix"
                  type="number"
                  placeholder="ex: 450"
                  value={manualPrix}
                  onChange={(e) => setManualPrix(e.target.value)}
                  className="mt-1 bg-surface-alt border-border text-foreground placeholder:text-text-muted"
                />
              </div>
              <Button
                onClick={handleManualUpdate}
                disabled={!manualCode || !manualPrix || manualLoading}
                className="bg-brand hover:bg-brand/80 text-white w-full rounded-[11px] h-10"
              >
                {manualLoading ? "Mise à jour..." : "Enregistrer le prix"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-[rgba(96,165,250,0.20)] bg-[rgba(96,165,250,0.05)]">
        <CardContent className="p-5">
          <h4 className="font-semibold text-blue-600 mb-2">Format attendu pour l&apos;import Excel</h4>
          <div className="bg-surface border border-border rounded-[10px] overflow-hidden mt-3">
            <table className="text-sm w-full">
              <thead className="bg-surface-alt text-text-dim text-xs uppercase">
                <tr>
                  <th className="px-4 py-2 text-left">code_moteur</th>
                  <th className="px-4 py-2 text-right">prix_propose</th>
                  <th className="px-4 py-2 text-left">marque (optionnel)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { code: "N47D20A", prix: 450, marque: "BMW" },
                  { code: "K9K714", prix: 320, marque: "Renault" },
                  { code: "D4204T", prix: 510, marque: "Volvo" },
                ].map((row) => (
                  <tr key={row.code}>
                    <td className="px-4 py-2 font-mono text-foreground">{row.code}</td>
                    <td className="px-4 py-2 text-right text-text-dim">{row.prix} €</td>
                    <td className="px-4 py-2 text-text-dim">{row.marque}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
