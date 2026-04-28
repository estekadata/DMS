"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Mail, Phone, MapPin, Building2, User } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Client = {
  n_client: number;
  societe: string | null;
  titre_contact: string | null;
  nom_contact: string | null;
  prenom_contact: string | null;
  nom_usage: string | null;
  adresse: string | null;
  ville: string | null;
  code_postal: string | null;
  tel: string | null;
  email: string | null;
  remarques: string | null;
};

type Achat = {
  key: string;
  type: "Moteur" | "Boîte";
  date: string | null;
  code: string;
  pieceId: number;
  n_expedition: number | null;
  prix: number | null;
};

type Reservation = {
  key: string;
  type: "Moteur" | "Boîte";
  date: string | null;
  code: string;
  pieceId: number;
};

function fmtPrice(v: number | null | undefined) {
  if (v == null) return "—";
  return `${Math.round(v).toLocaleString("fr-FR")} €`;
}

function clientDisplayName(c: Client) {
  return (
    c.societe ||
    c.nom_usage ||
    [c.prenom_contact, c.nom_contact].filter(Boolean).join(" ") ||
    `Client #${c.n_client}`
  );
}

export default function ClientProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idStr } = use(params);
  const id = Number(idStr);

  const [client, setClient] = useState<Client | null>(null);
  const [achats, setAchats] = useState<Achat[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);

      // 1. Client info
      const { data: cliRow } = await supabase
        .from("tbl_clients")
        .select(
          "n_client, societe, titre_contact, nom_contact, prenom_contact, nom_usage, adresse, ville, code_postal, tel, email, remarques"
        )
        .eq("n_client", id)
        .maybeSingle();

      if (cancelled) return;
      if (!cliRow) {
        setNotFound(true);
        setLoading(false);
        return;
      }
      setClient(cliRow as Client);

      // 2. Expeditions of this client → list of expedition IDs
      const { data: expRows } = await supabase
        .from("tbl_expeditions")
        .select("n_expedition, date_chargement, num_facture")
        .eq("n_client", id);
      const expIds = (expRows || []).map((e: any) => e.n_expedition).filter(Boolean) as number[];

      const expById: Record<number, { date: string | null; num_facture: string | null }> = {};
      (expRows || []).forEach((e: any) => {
        expById[e.n_expedition] = {
          date: e.date_chargement,
          num_facture: e.num_facture,
        };
      });

      // 3. Purchased moteurs + boites for those expeditions
      const [{ data: expMot }, { data: expBoi }] = await Promise.all([
        expIds.length
          ? supabase
              .from("tbl_expeditions_moteurs")
              .select("id, n_expedition, n_moteur, prix_vente_moteur, date_validation")
              .in("n_expedition", expIds)
          : Promise.resolve({ data: [] as any[] }),
        expIds.length
          ? supabase
              .from("tbl_expeditions_boites")
              .select("id, n_expedition, n_bv, prix_vente_bv, date_validation")
              .in("n_expedition", expIds)
          : Promise.resolve({ data: [] as any[] }),
      ]);

      const motorIds = [...new Set((expMot || []).map((r: any) => r.n_moteur).filter(Boolean))] as number[];
      const bvIds = [...new Set((expBoi || []).map((r: any) => r.n_bv).filter(Boolean))] as number[];

      const [{ data: motors }, { data: boites }] = await Promise.all([
        motorIds.length
          ? supabase
              .from("v_moteurs_dispo")
              .select("n_moteur, nom_type_moteur, code_moteur")
              .in("n_moteur", motorIds)
          : Promise.resolve({ data: [] as any[] }),
        bvIds.length
          ? supabase
              .from("v_boites_dispo")
              .select("n_bv, ref_bv, num_interne_bv")
              .in("n_bv", bvIds)
          : Promise.resolve({ data: [] as any[] }),
      ]);

      const motorCode: Record<number, string> = {};
      (motors || []).forEach((m: any) => {
        motorCode[m.n_moteur] = m.nom_type_moteur || m.code_moteur || `Moteur #${m.n_moteur}`;
      });
      const bvCode: Record<number, string> = {};
      (boites || []).forEach((b: any) => {
        bvCode[b.n_bv] = b.ref_bv || b.num_interne_bv || `BV #${b.n_bv}`;
      });

      const allAchats: Achat[] = [
        ...((expMot || []) as any[]).map((r) => ({
          key: `m-${r.id}`,
          type: "Moteur" as const,
          date: r.date_validation || expById[r.n_expedition]?.date || null,
          code: motorCode[r.n_moteur] || `Moteur #${r.n_moteur}`,
          pieceId: r.n_moteur,
          n_expedition: r.n_expedition,
          prix: r.prix_vente_moteur,
        })),
        ...((expBoi || []) as any[]).map((r) => ({
          key: `b-${r.id}`,
          type: "Boîte" as const,
          date: r.date_validation || expById[r.n_expedition]?.date || null,
          code: bvCode[r.n_bv] || `BV #${r.n_bv}`,
          pieceId: r.n_bv,
          n_expedition: r.n_expedition,
          prix: r.prix_vente_bv,
        })),
      ].sort((a, b) => {
        const da = a.date ? new Date(a.date).getTime() : 0;
        const db = b.date ? new Date(b.date).getTime() : 0;
        return db - da;
      });

      // 4. Active reservations not yet shipped — match both "ID" and "ID.0" textual forms
      const variants = [`${id}`, `${id}.0`];
      const [{ data: resaMot }, { data: resaBv }] = await Promise.all([
        supabase
          .from("v_moteurs_dispo")
          .select("n_moteur, nom_type_moteur, code_moteur, date_resa_moteur")
          .in("resa_client_moteur", variants)
          .eq("est_disponible", 1)
          .order("date_resa_moteur", { ascending: false, nullsFirst: false })
          .limit(500),
        supabase
          .from("v_boites_dispo")
          .select("n_bv, ref_bv, num_interne_bv, date_resa_bv")
          .in("resa_client_bv", variants)
          .eq("est_disponible", 1)
          .order("date_resa_bv", { ascending: false, nullsFirst: false })
          .limit(500),
      ]);

      const allResa: Reservation[] = [
        ...((resaMot || []) as any[]).map((r) => ({
          key: `rm-${r.n_moteur}`,
          type: "Moteur" as const,
          date: r.date_resa_moteur,
          code: r.nom_type_moteur || r.code_moteur || `Moteur #${r.n_moteur}`,
          pieceId: r.n_moteur,
        })),
        ...((resaBv || []) as any[]).map((r) => ({
          key: `rb-${r.n_bv}`,
          type: "Boîte" as const,
          date: r.date_resa_bv,
          code: r.ref_bv || r.num_interne_bv || `BV #${r.n_bv}`,
          pieceId: r.n_bv,
        })),
      ].sort((a, b) => {
        const da = a.date ? new Date(a.date).getTime() : 0;
        const db = b.date ? new Date(b.date).getTime() : 0;
        return db - da;
      });

      if (cancelled) return;
      setAchats(allAchats);
      setReservations(allResa);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <div className="text-center py-16 text-text-muted">Chargement du profil client...</div>;
  }

  if (notFound || !client) {
    return (
      <div>
        <Link
          href="/reservations"
          className="inline-flex items-center gap-2 text-sm text-text-dim hover:text-foreground mb-4"
        >
          <ArrowLeft size={14} /> Retour aux réservations
        </Link>
        <div className="bg-surface border border-border rounded-[14px] p-10 text-center">
          <p className="text-foreground font-semibold">Client introuvable</p>
          <p className="text-sm text-text-muted mt-1">
            Aucun client n&apos;existe avec l&apos;identifiant <span className="font-mono">{idStr}</span>.
          </p>
        </div>
      </div>
    );
  }

  const totalDepense = achats.reduce((s, a) => s + (a.prix || 0), 0);
  const nbMoteurs = achats.filter((a) => a.type === "Moteur").length;
  const nbBoites = achats.filter((a) => a.type === "Boîte").length;
  const dernierAchat = achats[0]?.date || null;
  const fullName =
    [client.titre_contact, client.prenom_contact, client.nom_contact].filter(Boolean).join(" ") ||
    client.nom_usage ||
    "—";
  const villeLine = [client.code_postal, client.ville].filter(Boolean).join(" ");

  return (
    <div>
      <Link
        href="/reservations"
        className="inline-flex items-center gap-2 text-sm text-text-dim hover:text-foreground mb-4"
      >
        <ArrowLeft size={14} /> Retour aux réservations
      </Link>

      <PageHeader
        title={clientDisplayName(client)}
        description={`Client n° ${client.n_client}`}
      />

      {/* Coordonnées */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Card>
          <CardContent className="p-5 space-y-2 text-sm">
            <div className="flex items-center gap-2 text-text-dim">
              <Building2 size={14} />
              <span className="font-semibold uppercase text-xs">Société</span>
            </div>
            <p className="text-foreground font-medium">{client.societe || "—"}</p>
            <div className="flex items-center gap-2 text-text-dim pt-2">
              <User size={14} />
              <span className="font-semibold uppercase text-xs">Contact</span>
            </div>
            <p className="text-foreground">{fullName}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <MapPin size={14} className="text-text-dim mt-1 shrink-0" />
              <div>
                <p className="text-foreground">{client.adresse || "—"}</p>
                <p className="text-text-dim">{villeLine || "—"}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Mail size={14} className="text-text-dim shrink-0" />
              {client.email ? (
                <a
                  href={`mailto:${client.email}`}
                  className="text-brand hover:underline truncate"
                >
                  {client.email}
                </a>
              ) : (
                <span className="text-text-dim">—</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Phone size={14} className="text-text-dim shrink-0" />
              <span className="text-foreground">{client.tel || "—"}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">Total dépensé</p>
            <p className="text-2xl font-bold text-brand">{fmtPrice(totalDepense)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">Moteurs achetés</p>
            <p className="text-2xl font-bold text-foreground">{nbMoteurs}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">Boîtes achetées</p>
            <p className="text-2xl font-bold text-foreground">{nbBoites}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">Dernier achat</p>
            <p className="text-2xl font-bold text-foreground">
              {dernierAchat ? new Date(dernierAchat).toLocaleDateString("fr-FR") : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Réservations en cours */}
      {reservations.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-foreground mb-3">
            Réservations en cours ({reservations.length})
          </h3>
          <div className="bg-surface border border-border rounded-[14px] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-surface-alt text-text-dim text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">N°</th>
                  <th className="px-4 py-3 text-left">Code / Réf</th>
                  <th className="px-4 py-3 text-left">Date réservation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {reservations.map((r) => (
                  <tr key={r.key} className="hover:bg-surface-hover transition-colors">
                    <td className="px-4 py-3">
                      <Badge
                        className={
                          r.type === "Moteur"
                            ? "bg-[rgba(96,165,250,0.10)] text-blue-600 border border-[rgba(96,165,250,0.20)]"
                            : "bg-[rgba(168,85,247,0.10)] text-purple-600 border border-[rgba(168,85,247,0.20)]"
                        }
                      >
                        {r.type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">{r.pieceId}</td>
                    <td className="px-4 py-3 font-semibold text-foreground">{r.code}</td>
                    <td className="px-4 py-3 text-text-dim">
                      {r.date ? new Date(r.date).toLocaleDateString("fr-FR") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Historique des achats */}
      <h3 className="font-semibold text-foreground mb-3">
        Historique des achats ({achats.length})
      </h3>
      <div className="bg-surface border border-border rounded-[14px] overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-alt text-text-dim text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Code / Réf</th>
              <th className="px-4 py-3 text-left">N° Expédition</th>
              <th className="px-4 py-3 text-right">Prix de vente</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {achats.map((a) => (
              <tr key={a.key} className="hover:bg-surface-hover transition-colors">
                <td className="px-4 py-3 text-text-dim">
                  {a.date ? new Date(a.date).toLocaleDateString("fr-FR") : "—"}
                </td>
                <td className="px-4 py-3">
                  <Badge
                    className={
                      a.type === "Moteur"
                        ? "bg-[rgba(96,165,250,0.10)] text-blue-600 border border-[rgba(96,165,250,0.20)]"
                        : "bg-[rgba(168,85,247,0.10)] text-purple-600 border border-[rgba(168,85,247,0.20)]"
                    }
                  >
                    {a.type}
                  </Badge>
                </td>
                <td className="px-4 py-3 font-semibold text-foreground">{a.code}</td>
                <td className="px-4 py-3 font-mono text-xs text-text-muted">
                  {a.n_expedition ?? "—"}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-text-dim">
                  {fmtPrice(a.prix)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {achats.length === 0 && (
          <p className="text-center py-10 text-text-muted italic">Aucun achat enregistré</p>
        )}
      </div>

      {client.remarques && (
        <Card className="mt-6">
          <CardContent className="p-5">
            <p className="text-xs text-text-dim font-semibold uppercase mb-2">Remarques</p>
            <p className="text-sm text-foreground whitespace-pre-line">{client.remarques}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
