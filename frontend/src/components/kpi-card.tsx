import { type KpiMeta } from "@/lib/types";

function formatValue(value: number | null | undefined, fmt: KpiMeta["fmt"]): string {
  const v = typeof value === "number" && !isNaN(value) ? value : 0;
  if (fmt === "money") return new Intl.NumberFormat("fr-FR").format(Math.round(v)) + " €";
  if (fmt === "pct") return v.toFixed(1) + "%";
  return new Intl.NumberFormat("fr-FR").format(Math.round(v));
}

interface KpiCardProps {
  meta: KpiMeta;
  value: number;
}

export function KpiCard({ meta, value }: KpiCardProps) {
  return (
    <div className="bg-surface border border-border rounded-[14px] p-5 hover:bg-surface-hover transition-all">
      <p className="text-[11px] font-semibold text-text-muted uppercase tracking-wide mb-2">
        {meta.label}
      </p>
      <p className={`text-2xl font-semibold tabular-nums ${meta.color === "brand" ? "text-brand" : "text-foreground"}`}>
        {formatValue(value, meta.fmt)}
      </p>
    </div>
  );
}
