"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type User = {
  id: string;
  email?: string;
  created_at?: string;
  last_sign_in_at?: string;
  role?: string;
  nom?: string;
  prenom?: string;
  actif?: boolean;
};

export default function UtilisateursPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", nom: "", prenom: "", role: "utilisateur" });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    const { data } = await supabase
      .from("v_utilisateurs")
      .select("id, email, created_at, last_sign_in_at, role, nom, prenom, actif")
      .order("created_at", { ascending: false })
      .limit(100);
    setUsers(data || []);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function toggleActif(user: User) {
    await supabase
      .from("tbl_utilisateurs_profils")
      .update({ actif: !user.actif })
      .eq("id", user.id);
    load();
  }

  async function createUser() {
    if (!form.email) return;
    setSaving(true);
    const { error } = await supabase.from("tbl_utilisateurs_profils").insert({
      email: form.email,
      nom: form.nom,
      prenom: form.prenom,
      role: form.role,
      actif: true,
    });
    if (error) {
      alert(`Erreur : ${error.message}`);
    } else {
      setShowForm(false);
      setForm({ email: "", nom: "", prenom: "", role: "utilisateur" });
      load();
    }
    setSaving(false);
  }

  const ROLES = ["administrateur", "commercial", "gestionnaire", "utilisateur"];

  return (
    <div>
      <PageHeader title="Gestion des utilisateurs" icon="👥" description="Administration des accès et des rôles" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Total utilisateurs</p>
            <p className="text-2xl font-bold text-[#C41E3A]">{users.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Actifs</p>
            <p className="text-2xl font-bold text-emerald-600">{users.filter((u) => u.actif !== false).length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Admins</p>
            <p className="text-2xl font-bold text-purple-600">{users.filter((u) => u.role === "administrateur").length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-semibold text-gray-700">Liste des utilisateurs</h2>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-[#C41E3A] hover:bg-[#8B1A2B] text-white"
        >
          + Nouvel utilisateur
        </Button>
      </div>

      {showForm && (
        <Card className="mb-6 border-[#C41E3A]/20">
          <CardContent className="p-5">
            <h3 className="font-semibold text-gray-800 mb-4">Créer un utilisateur</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email">Email *</Label>
                <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1" placeholder="prenom.nom@exemple.fr" />
              </div>
              <div>
                <Label htmlFor="role">Rôle</Label>
                <select id="role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full mt-1 border rounded-lg px-3 py-2 text-sm bg-white">
                  {ROLES.map((r) => <option key={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <Label htmlFor="prenom">Prénom</Label>
                <Input id="prenom" value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label htmlFor="nom">Nom</Label>
                <Input id="nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} className="mt-1" />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <Button onClick={createUser} disabled={saving || !form.email} className="bg-[#C41E3A] hover:bg-[#8B1A2B] text-white">
                {saving ? "Création..." : "Créer"}
              </Button>
              <Button variant="outline" onClick={() => setShowForm(false)}>Annuler</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Chargement...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Nom</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-center">Rôle</th>
                <th className="px-4 py-3 text-left">Créé le</th>
                <th className="px-4 py-3 text-left">Dernière connexion</th>
                <th className="px-4 py-3 text-center">Statut</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{[u.prenom, u.nom].filter(Boolean).join(" ") || "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email || "—"}</td>
                  <td className="px-4 py-3 text-center">
                    <Badge
                      className={
                        u.role === "administrateur"
                          ? "bg-purple-100 text-purple-700 hover:bg-purple-100"
                          : u.role === "commercial"
                          ? "bg-blue-100 text-blue-700 hover:bg-blue-100"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-100"
                      }
                    >
                      {u.role || "utilisateur"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{u.created_at ? new Date(u.created_at).toLocaleDateString("fr-FR") : "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{u.last_sign_in_at ? new Date(u.last_sign_in_at).toLocaleDateString("fr-FR") : "Jamais"}</td>
                  <td className="px-4 py-3 text-center">
                    <Badge
                      className={
                        u.actif !== false
                          ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                          : "bg-gray-100 text-gray-400 hover:bg-gray-100"
                      }
                    >
                      {u.actif !== false ? "Actif" : "Inactif"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs"
                      onClick={() => toggleActif(u)}
                    >
                      {u.actif !== false ? "Désactiver" : "Activer"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && <p className="text-center py-10 text-gray-400">Aucun utilisateur</p>}
        </div>
      )}
    </div>
  );
}
