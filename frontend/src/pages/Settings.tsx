import PageShell from "../components/PageShell";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Settings() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <PageShell title="Settings">
      <div className="two-col-grid">
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 16 }}>Profile</h3>
          <div className="form-field">
            <label>Full Name</label>
            <input value={user?.full_name ?? ""} disabled />
          </div>
          <div className="form-field">
            <label>Email</label>
            <input value={user?.email ?? ""} disabled />
          </div>
          <div className="form-field">
            <label>Role</label>
            <input value={user?.role ?? ""} disabled />
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Profile editing and account management will be extended in a future phase.
          </p>
        </div>

        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 16 }}>Appearance</h3>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 14 }}>
            Choose how MediFlow AI looks on this device. Your preference is saved automatically.
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <button className={`btn ${theme === "light" ? "btn-primary" : "btn-secondary"}`} onClick={() => theme !== "light" && toggleTheme()}>
              ☀ Light Mode
            </button>
            <button className={`btn ${theme === "dark" ? "btn-primary" : "btn-secondary"}`} onClick={() => theme !== "dark" && toggleTheme()}>
              ☾ Dark Mode
            </button>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
