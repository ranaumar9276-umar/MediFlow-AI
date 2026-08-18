import { ReactNode } from "react";

export default function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} style={{ width: 30, height: 30 }}>
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
