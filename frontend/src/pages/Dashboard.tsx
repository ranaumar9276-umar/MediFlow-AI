import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";
import PageShell from "../components/PageShell";
import StatCard from "../components/StatCard";
import { fetchAlerts, fetchDashboardSummary } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { LoadingBlock, ErrorBlock } from "../components/StateBlocks";

interface DashboardData {
  total_patients: number;
  total_doctors: number;
  total_departments: number;
  total_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  no_show_appointments: number;
  scheduled_appointments: number;
  no_show_rate_percent: number;
  cancellation_rate_percent: number;
  department_workload: { department: string; total_appointments: number; completed: number; cancelled: number; no_show: number }[];
  doctor_workload: { doctor: string; department: string; total_appointments: number; completed: number; upcoming: number }[];
  appointment_trend_last_14_days: { label: string; value: number }[];
}

interface Alert {
  severity: "critical" | "warning" | "info";
  category: string;
  message: string;
  metric_value: number;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([fetchDashboardSummary(), fetchAlerts()])
      .then(([summaryRes, alertsRes]) => {
        setData(summaryRes.data);
        setAlerts(alertsRes.data.alerts);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <PageShell title="Dashboard">
      {loading && <LoadingBlock label="Loading operational data..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {data && (
        <>
          {alerts.length > 0 && (
            <div className="card" style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>Operational Alerts</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {alerts.map((a, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "8px 12px",
                      borderRadius: 8,
                      background:
                        a.severity === "critical"
                          ? "rgba(224, 101, 79, 0.1)"
                          : a.severity === "warning"
                          ? "rgba(217, 170, 90, 0.1)"
                          : "var(--bg-surface-2)",
                      border: `1px solid ${a.severity === "critical" ? "var(--danger)" : a.severity === "warning" ? "var(--warning)" : "var(--border-color)"}`,
                    }}
                  >
                    <span
                      className={`badge ${a.severity === "critical" ? "badge-cancelled" : a.severity === "warning" ? "badge-no_show" : "badge-active"}`}
                    >
                      {a.severity}
                    </span>
                    <span style={{ fontSize: 13 }}>{a.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card-grid">
            <StatCard icon="🧑‍🤝‍🧑" label="Total Patients" value={data.total_patients} />
            <StatCard icon="⚕" label="Active Doctors" value={data.total_doctors} />
            <StatCard icon="🏥" label="Departments" value={data.total_departments} />
            <StatCard icon="🗓" label="Total Appointments" value={data.total_appointments} />
          </div>

          <div className="card-grid">
            <StatCard icon="✔" label="Completed" value={data.completed_appointments} />
            <StatCard icon="⏳" label="Scheduled (Upcoming)" value={data.scheduled_appointments} />
            <StatCard
              icon="✕"
              label="Cancellation Rate"
              value={`${data.cancellation_rate_percent}%`}
              delta={{ direction: data.cancellation_rate_percent > 15 ? "up" : "down", text: `${data.cancelled_appointments} cancelled` }}
            />
            <StatCard
              icon="⚠"
              label="No-Show Rate"
              value={`${data.no_show_rate_percent}%`}
              delta={{ direction: data.no_show_rate_percent > 10 ? "up" : "down", text: `${data.no_show_appointments} no-shows` }}
            />
          </div>

          <div className="two-col-grid">
            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>Appointment Volume Trend</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>Last 14 days, live from database</p>
              {data.appointment_trend_last_14_days.every((d) => d.value === 0) ? (
                <div className="state-block" style={{ padding: "30px 0" }}>No appointment activity yet</div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={data.appointment_trend_last_14_days}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                    <Line type="monotone" dataKey="value" stroke="var(--accent, #c8963e)" strokeWidth={2.5} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>Department Workload</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>Total appointments by department</p>
              {data.department_workload.length === 0 ? (
                <div className="state-block" style={{ padding: "30px 0" }}>No departments yet</div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.department_workload}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                    <XAxis dataKey="department" tick={{ fontSize: 10, fill: "var(--text-muted)" }} interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                    <Bar dataKey="total_appointments" fill="#c8963e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="card" style={{ marginTop: 18 }}>
            <h3 style={{ fontSize: 15, marginBottom: 14 }}>Doctor Workload</h3>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Doctor</th>
                    <th>Department</th>
                    <th>Total Appointments</th>
                    <th>Completed</th>
                    <th>Upcoming</th>
                  </tr>
                </thead>
                <tbody>
                  {data.doctor_workload.length === 0 && (
                    <tr><td colSpan={5} style={{ textAlign: "center", color: "var(--text-muted)" }}>No doctors registered yet</td></tr>
                  )}
                  {data.doctor_workload.map((d) => (
                    <tr key={d.doctor}>
                      <td>{d.doctor}</td>
                      <td>{d.department}</td>
                      <td>{d.total_appointments}</td>
                      <td>{d.completed}</td>
                      <td>{d.upcoming}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </PageShell>
  );
}
