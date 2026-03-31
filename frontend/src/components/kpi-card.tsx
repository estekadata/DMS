import { type KpiMeta } from "@/lib/types";

const colorMap: Record<string, string> = {
  emerald: "text-emerald-600",
  amber: "text-amber-600",
  red: "text-red-600",
  blue: "text-blue-600",
};

function formatValue(value: number, fmt: KpiMeta["fmt"]): string {
  if (fmt === "money") return new Intl.NumberFormat("fr-FR").format(Math.round(value)) + " EUR";
  if (fmt === "pct") return value.toFixed(1) + "%";
  return new Intl.NumberFormat("fr-FR").format(Math.round(value));
}

interface KpiCardProps {
  meta: KpiMeta;
  value: number;
}

export function KpiCard({ meta, value }: KpiCardProps) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        {meta.icon} {meta.label}
      </p>
      <p className={`text-3xl font-bold mt-2 ${colorMap[meta.color] || "text-gray-900"}`}>
        {formatValue(value, meta.fmt)}
      </p>
    </div>
  );
}
