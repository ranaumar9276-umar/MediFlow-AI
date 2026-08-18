import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";
import logo from "../assets/logo.png";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-form-side">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
            <img src={logo} alt="MediFlow AI" style={{ width: 40, height: 40, borderRadius: 10 }} />
            <div>
              <div style={{ fontFamily: "Playfair Display, serif", fontWeight: 700, fontSize: 17 }}>
                MediFlow AI
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Hospital Operations Platform
              </div>
            </div>
          </div>

          <h2 style={{ fontSize: 24, marginBottom: 6 }}>Welcome back</h2>
          <p style={{ fontSize: 13.5, color: "var(--text-secondary)", marginBottom: 22 }}>
            Sign in to manage patient flow, appointments and operational analytics.
          </p>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@mediflow.ai"
                autoComplete="username"
              />
            </div>
            <div className="form-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: 6 }} disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 18 }}>
            Default seeded admin: <strong>admin@mediflow.ai</strong> — see backend .env for the password.
          </p>
        </div>

        <div className="login-hero-side">
          <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", opacity: 0.75 }}>
            In MediFlow AI
          </span>
          <h2>Real-time visibility into every department, doctor and patient.</h2>
          <p>
            Track appointments, no-shows, cancellations and workload across your entire hospital from a
            single operational dashboard — backed by a real PostgreSQL database and live analytics.
          </p>
        </div>
      </div>
    </div>
  );
}
