import { ReactNode, useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function PageShell({ title, children }: { title: string; children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar open={mobileOpen} />
      <div className="main-content">
        <Topbar title={title} onMenuClick={() => setMobileOpen((o) => !o)} />
        <div className="page-body">{children}</div>
      </div>
    </div>
  );
}
