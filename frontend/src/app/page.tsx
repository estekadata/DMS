"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Erreur de connexion");
        return;
      }

      if (data.user.role === "vhu") {
        router.push("/vhu");
      } else {
        router.push("/dashboard");
      }
    } catch {
      setError("Erreur de connexion au serveur");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image
              src="/logo-multirex.jpg"
              alt="Multirex Auto"
              width={160}
              height={80}
              className="rounded-[10px]"
              priority
            />
          </div>
          <h1 className="font-heading text-3xl font-bold text-foreground">Multirex Auto DMS</h1>
          <p className="text-text-dim mt-2 text-sm">Systeme de gestion intelligent</p>
        </div>

        <div className="bg-surface border border-border rounded-[14px] p-8 shadow-[0_4px_12px_rgba(0,0,0,0.08)]">
          <h2 className="text-xl font-bold text-foreground mb-1">Connexion</h2>
          <p className="text-sm text-text-dim mb-6">Entrez vos identifiants</p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-text-dim">Email ou identifiant</Label>
              <Input
                id="email"
                type="text"
                placeholder="email@exemple.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 bg-surface-alt border-border text-foreground placeholder:text-text-muted"
                autoFocus
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-text-dim">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                placeholder="Votre mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 bg-surface-alt border-border text-foreground placeholder:text-text-muted"
              />
            </div>

            {error && (
              <div className="text-sm p-3 rounded-[10px] bg-[rgba(220,38,38,0.06)] text-red-600 border border-[rgba(220,38,38,0.12)]">
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 bg-brand hover:bg-brand/80 text-white rounded-[11px] h-10 font-semibold"
              >
                {loading ? "Connexion..." : "Se connecter"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1 rounded-[11px] h-10"
                onClick={() => router.push("/vhu")}
              >
                Centres VHU
              </Button>
            </div>
          </form>
        </div>

        <p className="text-text-muted text-xs mt-8 text-center">Multirex Auto 2025</p>
      </div>
    </div>
  );
}
