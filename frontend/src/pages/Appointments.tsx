import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import Modal from "../components/Modal";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import StatusBadge from "../components/StatusBadge";
import {
  cancelAppointment,
  checkInAppointment,
  completeAppointment,
  createAppointment,
  fetchAppointments,
  fetchDepartments,
  fetchDoctors,
  fetchPatients,
  noShowAppointment,
  startAppointment,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  department_id: number;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  reason?: string;
  patient_name?: string;
  doctor_name?: string;
  department_name?: string;
  checked_in_at?: string | null;
  started_at?: string | null;
  wait_time_minutes?: number | null;
}

interface Option { id: number; label: string; department_id?: number }

const STATUS_TABS = ["ALL", "SCHEDULED", "COMPLETED", "CANCELLED", "NO_SHOW"];

const emptyForm = { patient_id: "", doctor_id: "", department_id: "", scheduled_at: "", duration_minutes: 30, reason: "" };

export default function Appointments() {
  const { user } = useAuth();
  const canWrite = user && ["ADMIN", "HOSPITAL_MANAGER", "STAFF", "DOCTOR"].includes(user.role);

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patients, setPatients] = useState<Option[]>([]);
  const [doctors, setDoctors] = useState<Option[]>([]);
  const [departments, setDepartments] = useState<Option[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("ALL");

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadReferenceData = () =>
    Promise.all([fetchPatients({ limit: 200 }), fetchDoctors({ limit: 200 }), fetchDepartments()]).then(
      ([pRes, dRes, deptRes]) => {
        setPatients(pRes.data.items.map((p: any) => ({ id: p.id, label: p.full_name })));
        setDoctors(dRes.data.items.map((d: any) => ({ id: d.id, label: `${d.full_name} (${d.department_name})`, department_id: d.department_id })));
        setDepartments(deptRes.data.map((d: any) => ({ id: d.id, label: d.name })));
      }
    );

  const load = () => {
    setLoading(true);
    setError(null);
    const params: any = { limit: 100 };
    if (statusFilter !== "ALL") params.status = statusFilter;
    Promise.all([fetchAppointments(params), loadReferenceData()])
      .then(([apptRes]) => setAppointments(apptRes.data.items))
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [statusFilter]);

  const openCreate = () => {
    setForm({ ...emptyForm, department_id: departments[0]?.id?.toString() ?? "" });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createAppointment({
        patient_id: Number(form.patient_id),
        doctor_id: Number(form.doctor_id),
        department_id: Number(form.department_id),
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        duration_minutes: form.duration_minutes,
        reason: form.reason || undefined,
      });
      setModalOpen(false);
      load();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleAction = async (id: number, action: "cancel" | "complete" | "no-show" | "check-in" | "start") => {
    try {
      if (action === "cancel") await cancelAppointment(id);
      if (action === "complete") await completeAppointment(id);
      if (action === "no-show") await noShowAppointment(id);
      if (action === "check-in") await checkInAppointment(id);
      if (action === "start") await startAppointment(id);
      load();
    } catch (err) {
      alert(apiErrorMessage(err));
    }
  };

  const doctorsInDepartment = doctors.filter((d) => !form.department_id || d.department_id === Number(form.department_id));

  return (
    <PageShell title="Appointments">
      <div className="toolbar">
        <div className="pill-tabs">
          {STATUS_TABS.map((s) => (
            <button key={s} className={`pill-tab ${statusFilter === s ? "active" : ""}`} onClick={() => setStatusFilter(s)}>
              {s.replace("_", " ")}
            </button>
          ))}
        </div>
        {canWrite && (
          <button className="btn btn-primary" onClick={openCreate} disabled={patients.length === 0 || doctors.length === 0}>
            + New Appointment
          </button>
        )}
      </div>

      {loading && <LoadingBlock label="Loading appointments..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {!loading && !error && appointments.length === 0 && <EmptyBlock message="No appointments found for this filter." />}

      {!loading && !error && appointments.length > 0 && (
        <div className="card">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Department</th>
                  <th>Scheduled</th>
                  <th>Duration</th>
                  <th>Wait Time</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.patient_name}</td>
                    <td>{a.doctor_name}</td>
                    <td>{a.department_name}</td>
                    <td>{new Date(a.scheduled_at).toLocaleString()}</td>
                    <td>{a.duration_minutes} min</td>
                    <td>
                      {a.wait_time_minutes != null
                        ? `${a.wait_time_minutes} min`
                        : a.checked_in_at
                        ? "In progress..."
                        : "—"}
                    </td>
                    <td><StatusBadge status={a.status} /></td>
                    <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {canWrite && a.status === "SCHEDULED" && (
                        <>
                          {!a.checked_in_at && (
                            <button className="btn btn-secondary btn-sm" onClick={() => handleAction(a.id, "check-in")}>Check-in</button>
                          )}
                          {a.checked_in_at && !a.started_at && (
                            <button className="btn btn-secondary btn-sm" onClick={() => handleAction(a.id, "start")}>Start</button>
                          )}
                          <button className="btn btn-secondary btn-sm" onClick={() => handleAction(a.id, "complete")}>Complete</button>
                          <button className="btn btn-secondary btn-sm" onClick={() => handleAction(a.id, "no-show")}>No-show</button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleAction(a.id, "cancel")}>Cancel</button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {modalOpen && (
        <Modal title="New Appointment" onClose={() => setModalOpen(false)}>
          {formError && <div className="form-error">{formError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Patient</label>
              <select required value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })}>
                <option value="">Select patient</option>
                {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
              </select>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Department</label>
                <select required value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value, doctor_id: "" })}>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Doctor</label>
                <select required value={form.doctor_id} onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}>
                  <option value="">Select doctor</option>
                  {doctorsInDepartment.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
                </select>
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Date &amp; Time</label>
                <input type="datetime-local" required value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Duration (minutes)</label>
                <input type="number" min={5} max={480} value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })} />
              </div>
            </div>
            <div className="form-field">
              <label>Reason</label>
              <input value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} placeholder="e.g. Follow-up consultation" />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={saving}>
              {saving ? "Scheduling..." : "Schedule Appointment"}
            </button>
          </form>
        </Modal>
      )}
    </PageShell>
  );
}
