import { getSession } from "@/lib/auth";
import { redirect } from "next/navigation";
import { SidebarWrapper } from "./sidebar-wrapper";

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/");

  return (
    <div className="flex min-h-screen">
      <SidebarWrapper userName={session.nom} userRole={session.role} />
      <main className="flex-1 ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
