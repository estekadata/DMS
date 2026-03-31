"use client";

import { useRouter } from "next/navigation";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: string;
  showBack?: boolean;
}

export function PageHeader({ title, description, icon, showBack = true }: PageHeaderProps) {
  const router = useRouter();

  return (
    <div className="mb-6">
      {showBack && (
        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm text-gray-500 hover:text-gray-700 mb-3 flex items-center gap-1 transition-colors"
        >
          ← Retour à l&apos;accueil
        </button>
      )}
      <h1 className="text-2xl font-bold text-gray-900">
        {icon && <span className="mr-2">{icon}</span>}
        {title}
      </h1>
      {description && <p className="text-gray-500 mt-1">{description}</p>}
    </div>
  );
}
