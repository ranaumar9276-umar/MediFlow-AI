import { useTheme } from "../context/ThemeContext";

export default function Topbar({
  title,
  onMenuClick,
}: {
  title: string;
  onMenuClick: () => void;
}) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="topbar">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button className="icon-btn" onClick={onMenuClick} style={{ display: "none" }} id="mobile-menu-btn">
          ☰
        </button>
        <h1>{title}</h1>
      </div>
      <div className="topbar-actions">
        <button className="icon-btn" onClick={toggleTheme} title="Toggle theme">
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
