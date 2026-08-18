export default function StatCard({
  icon,
  label,
  value,
  delta,
}: {
  icon: string;
  label: string;
  value: string | number;
  delta?: { direction: "up" | "down"; text: string };
}) {
  return (
    <div className="card stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {delta && <div className={`stat-delta ${delta.direction}`}>{delta.direction === "up" ? "▲" : "▼"} {delta.text}</div>}
    </div>
  );
}
