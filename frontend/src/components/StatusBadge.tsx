export default function StatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase();
  return <span className={`badge badge-${key}`}>{status.replace("_", " ")}</span>;
}
