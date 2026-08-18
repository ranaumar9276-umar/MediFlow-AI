import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

const MAIN_ITEMS = [{ to: "/", label: "Dashboard", icon: "◧", end: true }];

const OPERATIONS_ITEMS = [
  { to: "/patients", label: "Patients", icon: "🧑‍⚕" },
  { to: "/appointments", label: "Appointments", icon: "🗓" },
  { to: "/doctors", label: "Doctors", icon: "⚕" },
  { to: "/departments", label: "Departments", icon: "🏥" },
];

const INTELLIGENCE_ITEMS = [
  { to: "/analytics", label: "Analytics", icon: "📊" },
  { to: "/predictions", label: "Predictions", icon: "🔮" },
  { to: "/reports", label: "Reports", icon: "📄" },
];

function NavGroup({ items }: { items: { to: string; label: string; icon: string; end?: boolean }[] }) {
  return (
    <>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
        >
          <span className="icon">{item.icon}</span> {item.label}
        </NavLink>
      ))}
    </>
  );
}

export default function Sidebar({ open }: { open: boolean }) {
  const { user, logout } = useAuth();

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand">
        <img src={logo} alt="MediFlow AI" />
        <div className="sidebar-brand-text">
          <span className="name">MediFlow AI</span>
          <span className="sub">Hospital Ops</span>
        </div>
      </div>

      <div className="nav-section-label">Main</div>
      <NavGroup items={MAIN_ITEMS} />

      <div className="nav-section-label">Operations</div>
      <NavGroup items={OPERATIONS_ITEMS} />

      <div className="nav-section-label">Intelligence</div>
      <NavGroup items={INTELLIGENCE_ITEMS} />

      <div className="nav-section-label">Administration</div>
      <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
        <span className="icon">⚙</span> Settings
      </NavLink>

      <div className="sidebar-footer">
        <div className="avatar">{user?.full_name?.slice(0, 2).toUpperCase() ?? "?"}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {user?.full_name}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{user?.role}</div>
        </div>
        <button className="icon-btn" title="Log out" onClick={logout} style={{ width: 30, height: 30 }}>
          ⏻
        </button>
      </div>
    </aside>
  );
}
