import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import Modal from "../components/Modal";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import StatusBadge from "../components/StatusBadge";
import { createPatient, deletePatient, fetchPatients, updatePatient } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface Patient {
  id: number;
  full_name: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone?: string;
  email?: string;
  blood_type?: string;
  status: string;
  appointment_count: number;
}

const emptyForm = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "UNSPECIFIED",
  phone: "",
  email: "",
  blood_type: "",
  status: "ACTIVE",
  notes: "",
};

export default function Patients() {
  const { user } = useAuth();
  const canWrite = user && ["ADMIN", "HOSPITAL_MANAGER", "STAFF"].includes(user.role);
  const canDelete = user && ["ADMIN", "HOSPITAL_MANAGER"].includes(user.role);

  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchPatients({ search: search || undefined, limit: 100 })
      .then((res) => {
        setPatients(res.data.items);
        setTotal(res.data.total);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (p: Patient) => {
    setEditingId(p.id);
    setForm({
      first_name: p.first_name,
      last_name: p.last_name,
      date_of_birth: p.date_of_birth,
      gender: p.gender,
      phone: p.phone ?? "",
      email: p.email ?? "",
      blood_type: p.blood_type ?? "",
      status: p.status,
      notes: "",
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = { ...form, email: form.email || undefined, phone: form.phone || undefined, blood_type: form.blood_type || undefined };
      if (editingId) {
        await updatePatient(editingId, payload);
      } else {
        await createPatient(payload);
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
    if (!confirm("Delete this patient? This cannot be undone.")) return;
    try {
      await deletePatient(id);
      load();
    } catch (err) {
      alert(apiErrorMessage(err));
    }
  };

  return (
    <PageShell title="Patients">
      <div className="toolbar">
        <div className="search-input">
          <span>🔍</span>
          <input placeholder="Search by name, email or phone..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {canWrite && (
          <button className="btn btn-primary" onClick={openCreate}>
            + Add Patient
          </button>
        )}
      </div>

      {loading && <LoadingBlock label="Loading patients..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {!loading && !error && patients.length === 0 && <EmptyBlock message="No patients found. Add your first patient to get started." />}

      {!loading && !error && patients.length > 0 && (
        <div className="card">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>DOB</th>
                  <th>Gender</th>
                  <th>Contact</th>
                  <th>Blood Type</th>
                  <th>Status</th>
                  <th>Appointments</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.id}>
                    <td>{p.full_name}</td>
                    <td>{p.date_of_birth}</td>
                    <td>{p.gender}</td>
                    <td>{p.email || p.phone || "—"}</td>
                    <td>{p.blood_type || "—"}</td>
                    <td><StatusBadge status={p.status} /></td>
                    <td>{p.appointment_count}</td>
                    <td style={{ display: "flex", gap: 6 }}>
                      {canWrite && <button className="btn btn-secondary btn-sm" onClick={() => openEdit(p)}>Edit</button>}
                      {canDelete && <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)}>Delete</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 10 }}>{total} total patient(s)</div>
        </div>
      )}

      {modalOpen && (
        <Modal title={editingId ? "Edit Patient" : "Add Patient"} onClose={() => setModalOpen(false)}>
          {formError && <div className="form-error">{formError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-field">
                <label>First Name</label>
                <input required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Last Name</label>
                <input required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Date of Birth</label>
                <input type="date" required value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Gender</label>
                <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                  <option value="UNSPECIFIED">Unspecified</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Phone</label>
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Blood Type</label>
                <input value={form.blood_type} onChange={(e) => setForm({ ...form, blood_type: e.target.value })} placeholder="e.g. O+" />
              </div>
              <div className="form-field">
                <label>Status</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="ACTIVE">Active</option>
                  <option value="DISCHARGED">Discharged</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={saving}>
              {saving ? "Saving..." : editingId ? "Save Changes" : "Add Patient"}
            </button>
          </form>
        </Modal>
      )}
    </PageShell>
  );
}
