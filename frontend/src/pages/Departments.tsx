import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import Modal from "../components/Modal";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import { createDepartment, deleteDepartment, fetchDepartments, updateDepartment } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface Department {
  id: number;
  name: string;
  description?: string;
  location?: string;
  doctor_count: number;
  appointment_count: number;
}

const emptyForm = { name: "", description: "", location: "" };

export default function Departments() {
  const { user } = useAuth();
  const canWrite = user && ["ADMIN", "HOSPITAL_MANAGER"].includes(user.role);
  const canDelete = user?.role === "ADMIN";

  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchDepartments()
      .then((res) => setDepartments(res.data))
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (d: Department) => {
    setEditingId(d.id);
    setForm({ name: d.name, description: d.description ?? "", location: d.location ?? "" });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      if (editingId) {
        await updateDepartment(editingId, form);
      } else {
        await createDepartment(form);
      }
      setModalOpen(false);
      load();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this department?")) return;
    try {
      await deleteDepartment(id);
      load();
    } catch (err) {
      alert(apiErrorMessage(err));
    }
  };

  return (
    <PageShell title="Departments">
      <div className="toolbar">
        <div />
        {canWrite && (
          <button className="btn btn-primary" onClick={openCreate}>
            + Add Department
          </button>
        )}
      </div>

      {loading && <LoadingBlock label="Loading departments..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {!loading && !error && departments.length === 0 && <EmptyBlock message="No departments yet." />}

      {!loading && !error && departments.length > 0 && (
        <div className="card-grid">
          {departments.map((d) => (
            <div className="card" key={d.id}>
              <h3 style={{ fontSize: 16, marginBottom: 4 }}>{d.name}</h3>
              {d.location && <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>{d.location}</div>}
              {d.description && <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 14 }}>{d.description}</p>}
              <div style={{ display: "flex", gap: 16, fontSize: 13, marginBottom: 14 }}>
                <div><strong>{d.doctor_count}</strong> doctors</div>
                <div><strong>{d.appointment_count}</strong> appointments</div>
              </div>
              {(canWrite || canDelete) && (
                <div style={{ display: "flex", gap: 6 }}>
                  {canWrite && <button className="btn btn-secondary btn-sm" onClick={() => openEdit(d)}>Edit</button>}
                  {canDelete && <button className="btn btn-danger btn-sm" onClick={() => handleDelete(d.id)}>Delete</button>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {modalOpen && (
        <Modal title={editingId ? "Edit Department" : "Add Department"} onClose={() => setModalOpen(false)}>
          {formError && <div className="form-error">{formError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Name</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-field">
              <label>Location</label>
              <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="e.g. Building A, Floor 2" />
            </div>
            <div className="form-field">
              <label>Description</label>
              <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={saving}>
              {saving ? "Saving..." : editingId ? "Save Changes" : "Add Department"}
            </button>
          </form>
        </Modal>
      )}
    </PageShell>
  );
}
