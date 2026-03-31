"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

type PrixRow = { code_moteur: string; prix_achat_actuel: number; prix_propose: number; delta_pct: number; };

export default function PrixPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PrixRow[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [manualPrix, setManualPrix] = useState("");
  const [manualLoading, setManualLoading] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setPreview([]);
    setStatus("idle");
    if (f) {
      setMessage(`Fichier sélectionné : ${f.name} (${(f.size / 1024).toFixed(1)} Ko)`);
    }
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("loading");
    setMessage("Traitement en cours...");
    // Upload to Supabase Storage for server-side processing
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
      <PageHeader title="Mise à jour des prix" icon="💶" description="Import Excel et mise à jour manuelle des prix d'achat proposés" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Excel upload */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Import fichier Excel</h3>
            <p className="text-sm text-gray-500 mb-4">
              Importez un fichier Excel (.xlsx) contenant les colonnes <code className="bg-gray-100 px-1 rounded">code_moteur</code> et <code className="bg-gray-100 px-1 rounded">prix_propose</code>.
            </p>
            <div className="space-y-4">
              <div>
                <Label htmlFor="file-input">Fichier Excel</Label>
                <Input
                  id="file-input"
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                  className="mt-1"
                />
              </div>
              {message && (
                <div className={`text-sm px-3 py-2 rounded-lg ${status === "error" ? "bg-red-50 text-red-600" : status === "done" ? "bg-emerald-50 text-emerald-700" : "bg-blue-50 text-blue-600"}`}>
                  {message}
                </div>
              )}
              <Button
                onClick={handleUpload}
                disabled={!file || status === "loading"}
                className="bg-[#C41E3A] hover:bg-[#8B1A2B] text-white w-full"
              >
                {status === "loading" ? "Upload en cours..." : "Importer le fichier"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Manual update */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Mise à jour manuelle</h3>
            <p className="text-sm text-gray-500 mb-4">
              Mettez à jour le prix d&apos;achat proposé pour une référence spécifique.
            </p>
            <div className="space-y-4">
              <div>
                <Label htmlFor="code">Code moteur</Label>
                <Input
                  id="code"
                  placeholder="ex: N47D20A"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  className="mt-1 uppercase"
                />
              </div>
              <div>
                <Label htmlFor="prix">Prix proposé (€)</Label>
                <Input
                  id="prix"
                  type="number"
                  placeholder="ex: 450"
                  value={manualPrix}
                  onChange={(e) => setManualPrix(e.target.value)}
                  className="mt-1"
                />
              </div>
              <Button
                onClick={handleManualUpdate}
                disabled={!manualCode || !manualPrix || manualLoading}
                className="bg-[#C41E3A] hover:bg-[#8B1A2B] text-white w-full"
              >
                {manualLoading ? "Mise à jour..." : "Enregistrer le prix"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info box */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-5">
          <h4 className="font-semibold text-blue-800 mb-2">Format attendu pour l&apos;import Excel</h4>
          <div className="bg-white rounded-lg overflow-hidden mt-3">
            <table className="text-sm w-full">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="px-4 py-2 text-left">code_moteur</th>
                  <th className="px-4 py-2 text-right">prix_propose</th>
                  <th className="px-4 py-2 text-left">marque (optionnel)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[
                  { code: "N47D20A", prix: 450, marque: "BMW" },
                  { code: "K9K714", prix: 320, marque: "Renault" },
                  { code: "D4204T", prix: 510, marque: "Volvo" },
                ].map((row) => (
                  <tr key={row.code}>
                    <td className="px-4 py-2 font-mono">{row.code}</td>
                    <td className="px-4 py-2 text-right">{row.prix} €</td>
                    <td className="px-4 py-2 text-gray-500">{row.marque}</td>
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
