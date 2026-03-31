"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";

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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🚗</div>
          <h1 className="text-3xl font-bold text-white">Multirex Auto DMS</h1>
          <p className="text-gray-400 mt-2">Systeme de gestion intelligent</p>
        </div>

        <Card className="shadow-2xl border-0">
          <CardContent className="p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-1">Connexion</h2>
            <p className="text-sm text-gray-500 mb-6">Entrez vos identifiants</p>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="email">Email ou identifiant</Label>
                <Input
                  id="email"
                  type="text"
                  placeholder="email@exemple.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1.5"
                  autoFocus
                />
              </div>
              <div>
                <Label htmlFor="password">Mot de passe</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Votre mot de passe"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1.5"
                />
              </div>

              {error && (
                <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg border border-red-200">
                  {error}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-[#C41E3A] hover:bg-[#991B1E] text-white"
                >
                  {loading ? "Connexion..." : "Se connecter"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => router.push("/vhu")}
                >
                  Centres VHU
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="text-center mt-8">
          <div className="inline-flex gap-4 bg-white/10 backdrop-blur px-6 py-3 rounded-full">
            <span className="text-[#C41E3A] text-xs font-semibold">Analytics</span>
            <span className="text-[#C41E3A] text-xs font-semibold">Temps reel</span>
            <span className="text-[#C41E3A] text-xs font-semibold">Securise</span>
          </div>
          <p className="text-gray-500 text-xs mt-4">Multirex Auto 2025</p>
        </div>
      </div>
    </div>
  );
}
