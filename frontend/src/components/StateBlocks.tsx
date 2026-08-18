export function LoadingBlock({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="state-block">
      <div className="spinner" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-block">
      <span style={{ color: "var(--danger)", fontWeight: 600 }}>Something went wrong</span>
      <span>{message}</span>
      {onRetry && (
        <button className="btn btn-secondary btn-sm" onClick={onRetry} style={{ marginTop: 8 }}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyBlock({ message }: { message: string }) {
  return (
    <div className="state-block">
      <span style={{ fontSize: 28 }}>—</span>
      <span>{message}</span>
    </div>
  );
}
