import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import Modal from "../components/Modal";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import { createDoctor, deleteDoctor, fetchDepartments, fetchDoctors, updateDoctor } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface Doctor {
  id: number;
  full_name: string;
  specialty: string;
  email: string;
  phone?: string;
  department_id: number;
  department_name?: string;
  daily_capacity: number;
  is_active: boolean;
  active_appointment_count: number;
}

interface Department {
  id: number;
  name: string;
}

const emptyForm = { full_name: "", specialty: "", email: "", phone: "", department_id: "", daily_capacity: 12, is_active: true };

export default function Doctors() {
  const { user } = useAuth();
  const canWrite = user && ["ADMIN", "HOSPITAL_MANAGER"].includes(user.role);

  const [doctors, setDoctors] = useState<Doctor[]>([]);
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
    Promise.all([fetchDoctors({ limit: 100 }), fetchDepartments()])
      .then(([docRes, deptRes]) => {
        setDoctors(docRes.data.items);
        setDepartments(deptRes.data);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => {
    setEditingId(null);
    setForm({ ...emptyForm, department_id: departments[0]?.id?.toString() ?? "" });
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (d: Doctor) => {
    setEditingId(d.id);
    setForm({
      full_name: d.full_name,
      specialty: d.specialty,
      email: d.email,
      phone: d.phone ?? "",
      department_id: d.department_id.toString(),
      daily_capacity: d.daily_capacity,
      is_active: d.is_active,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = { ...form, department_id: Number(form.department_id), phone: form.phone || undefined };
      if (editingId) {
        await updateDoctor(editingId, payload);
      } else {
        await createDoctor(payload);
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
    if (!confirm("Delete this doctor?")) return;
    try {
      await deleteDoctor(id);
      load();
    } catch (err) {
      alert(apiErrorMessage(err));
    }
  };

  return (
    <PageShell title="Doctors">
      <div className="toolbar">
        <div />
        {canWrite && (
          <button className="btn btn-primary" onClick={openCreate} disabled={departments.length === 0}>
            + Add Doctor
          </button>
        )}
      </div>

      {loading && <LoadingBlock label="Loading doctors..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {!loading && !error && doctors.length === 0 && <EmptyBlock message="No doctors registered yet." />}

      {!loading && !error && doctors.length > 0 && (
        <div className="card">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Specialty</th>
                  <th>Department</th>
                  <th>Contact</th>
                  <th>Capacity/day</th>
                  <th>Active Appointments</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((d) => (
                  <tr key={d.id}>
                    <td>{d.full_name}</td>
                    <td>{d.specialty}</td>
                    <td>{d.department_name}</td>
                    <td>{d.email}</td>
                    <td>{d.daily_capacity}</td>
                    <td>{d.active_appointment_count}</td>
                    <td><span className={`badge ${d.is_active ? "badge-active" : "badge-inactive"}`}>{d.is_active ? "Active" : "Inactive"}</span></td>
                    <td style={{ display: "flex", gap: 6 }}>
                      {canWrite && <button className="btn btn-secondary btn-sm" onClick={() => openEdit(d)}>Edit</button>}
                      {canWrite && <button className="btn btn-danger btn-sm" onClick={() => handleDelete(d.id)}>Delete</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {modalOpen && (
        <Modal title={editingId ? "Edit Doctor" : "Add Doctor"} onClose={() => setModalOpen(false)}>
          {formError && <div className="form-error">{formError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Full Name</label>
              <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Specialty</label>
                <input required value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Department</label>
                <select required value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
                  {departments.map((dep) => (
                    <option key={dep.id} value={dep.id}>{dep.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Email</label>
                <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Phone</label>
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
            </div>
            <div className="form-field">
              <label>Daily Capacity</label>
              <input type="number" min={1} max={100} value={form.daily_capacity} onChange={(e) => setForm({ ...form, daily_capacity: Number(e.target.value) })} />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={saving}>
              {saving ? "Saving..." : editingId ? "Save Changes" : "Add Doctor"}
            </button>
          </form>
        </Modal>
      )}
    </PageShell>
  );
}
