import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import StatusBadge from "../components/StatusBadge";
import { fetchAppointmentReport, fetchDepartments, fetchDoctors } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";

interface ReportRow {
  id: number;
  patient_name: string;
  doctor_name: string;
  department_name: string;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  reason?: string;
}

interface ReportData {
  summary: {
    total_appointments: number;
    returned_rows: number;
    status_counts: Record<string, number>;
    average_duration_minutes: number;
  };
  rows: ReportRow[];
}

const STATUS_OPTIONS = ["", "SCHEDULED", "COMPLETED", "CANCELLED", "NO_SHOW"];

export default function Reports() {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
  const [doctors, setDoctors] = useState<{ id: number; full_name: string }[]>([]);

  const [filters, setFilters] = useState({ status: "", department_id: "", doctor_id: "", date_from: "", date_to: "" });

  const load = () => {
    setLoading(true);
    setError(null);
    const params: any = {};
    if (filters.status) params.status = filters.status;
    if (filters.department_id) params.department_id = Number(filters.department_id);
    if (filters.doctor_id) params.doctor_id = Number(filters.doctor_id);
    if (filters.date_from) params.date_from = new Date(filters.date_from).toISOString();
    if (filters.date_to) params.date_to = new Date(filters.date_to).toISOString();

    Promise.all([fetchAppointmentReport(params), fetchDepartments(), fetchDoctors({ limit: 200 })])
      .then(([reportRes, deptRes, docRes]) => {
        setData(reportRes.data);
        setDepartments(deptRes.data);
        setDoctors(docRes.data.items);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const applyFilters = (e: FormEvent) => {
    e.preventDefault();
    load();
  };

  const exportCsv = () => {
    if (!data) return;
    const headers = ["ID", "Patient", "Doctor", "Department", "Scheduled", "Duration (min)", "Status", "Reason"];
    const csvRows = data.rows.map((r) =>
      [r.id, r.patient_name, r.doctor_name, r.department_name, r.scheduled_at, r.duration_minutes, r.status, r.reason ?? ""]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(",")
    );
    const csv = [headers.join(","), ...csvRows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `mediflow-appointment-report-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageShell title="Reports">
      <form className="card" onSubmit={applyFilters} style={{ marginBottom: 18 }}>
        <div className="form-grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
          <div className="form-field">
            <label>Status</label>
            <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s || "All"}</option>)}
            </select>
          </div>
          <div className="form-field">
            <label>Department</label>
            <select value={filters.department_id} onChange={(e) => setFilters({ ...filters, department_id: e.target.value })}>
              <option value="">All</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="form-field">
            <label>Doctor</label>
            <select value={filters.doctor_id} onChange={(e) => setFilters({ ...filters, doctor_id: e.target.value })}>
              <option value="">All</option>
              {doctors.map((d) => <option key={d.id} value={d.id}>{d.full_name}</option>)}
            </select>
          </div>
          <div className="form-field">
            <label>From</label>
            <input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
          </div>
          <div className="form-field">
            <label>To</label>
            <input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button type="submit" className="btn btn-primary">Apply Filters</button>
          <button type="button" className="btn btn-secondary" onClick={exportCsv} disabled={!data || data.rows.length === 0}>
            Export CSV
          </button>
        </div>
      </form>

      {loading && <LoadingBlock label="Building report..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}

      {data && (
        <>
          <div className="card-grid">
            <div className="card">
              <div className="stat-label">Total Appointments</div>
              <div className="stat-value">{data.summary.total_appointments}</div>
            </div>
            <div className="card">
              <div className="stat-label">Average Duration</div>
              <div className="stat-value">{data.summary.average_duration_minutes} min</div>
            </div>
            {Object.entries(data.summary.status_counts).map(([status, count]) => (
              <div className="card" key={status}>
                <div className="stat-label">{status.replace("_", " ")}</div>
                <div className="stat-value">{count}</div>
              </div>
            ))}
          </div>

          {data.rows.length === 0 ? (
            <EmptyBlock message="No appointments match these filters." />
          ) : (
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
                      <th>Status</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((r) => (
                      <tr key={r.id}>
                        <td>{r.patient_name}</td>
                        <td>{r.doctor_name}</td>
                        <td>{r.department_name}</td>
                        <td>{new Date(r.scheduled_at).toLocaleString()}</td>
                        <td>{r.duration_minutes} min</td>
                        <td><StatusBadge status={r.status} /></td>
                        <td>{r.reason || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
