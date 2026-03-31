import { NextRequest, NextResponse } from "next/server";
import { createSession, hashPassword, type SessionUser } from "@/lib/auth";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();

  if (!email || !password) {
    return NextResponse.json({ error: "Email et mot de passe requis" }, { status: 400 });
  }

  const pwdHash = await hashPassword(password);
  let user: SessionUser | null = null;

  // Try dms_users table
  const { data, error } = await supabase
    .from("dms_users")
    .select("id, email, nom, role")
    .eq("email", email.trim())
    .eq("password_hash", pwdHash)
    .eq("actif", true)
    .single();

  if (data && !error) {
    user = { id: data.id, email: data.email, nom: data.nom || "", role: data.role };
    // Update last login
    await supabase.from("dms_users").update({ last_login: new Date().toISOString() }).eq("id", data.id);
  }

  // Fallback: legacy admin
  if (!user) {
    const adminUser = process.env.ADMIN_USER || "admin";
    const adminPwd = process.env.ADMIN_PASSWORD || "change-moi";
    if (email === adminUser && password === adminPwd) {
      user = { id: 0, email: "admin", nom: "Administrateur", role: "super_admin" };
    }
  }

  if (!user) {
    return NextResponse.json({ error: "Identifiants incorrects" }, { status: 401 });
  }

  const token = await createSession(user);
  const response = NextResponse.json({ user });
  response.cookies.set("dms-session", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: "/",
  });

  return response;
}
