import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line } from "recharts";
import PageShell from "../components/PageShell";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "../components/StateBlocks";
import {
  fetchAppointmentStatistics,
  fetchCancellationNoShowAnalysis,
  fetchDataQuality,
  fetchEdaCharts,
  fetchForecast,
  fetchPeakPeriods,
  fetchWaitingTimeAnalytics,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";

interface StatsResponse {
  row_count: number;
  statistics: {
    duration_minutes: { mean: number; median: number; std: number; p25: number; p75: number; p90: number };
    status_breakdown: Record<string, number>;
  };
  weekday_distribution: Record<string, number>;
}

interface WaitingTimeResponse {
  has_data: boolean;
  sample_size: number;
  mean_minutes?: number;
  median_minutes?: number;
  p90_minutes?: number;
  by_department?: Record<string, number>;
}

interface PeakPeriodsResponse {
  peak_weekday: string | null;
  peak_weekday_count: number;
  peak_hour: number | null;
  peak_hour_count: number;
  hourly_distribution: Record<string, number>;
}

interface DataQualityResponse {
  patients: {
    total_records: number;
    quality_score_percent: number;
    duplicate_records: number;
    invalid_dates_of_birth: number;
    inconsistent_blood_types: number;
    missing_values: Record<string, { missing_count: number; missing_percent: number }>;
  };
  appointments: {
    total_records: number;
    duplicate_records: number;
    duration_outliers: number;
    invalid_status_transitions: number;
  };
}

interface EdaResponse {
  duration_distribution: string | null;
  weekday_hour_heatmap: string | null;
  department_status_breakdown: string | null;
}

interface ForecastResponse {
  forecastable: boolean;
  reason?: string;
  history?: { date: string; count: number }[];
  forecast?: { date: string; predicted_count: number }[];
  trend_direction?: string;
  fit_quality_r_squared?: number;
  limitations?: string;
}

interface CancellationEntry {
  total: number;
  cancelled: number;
  no_show: number;
  cancellation_rate_percent: number;
  no_show_rate_percent: number;
}

interface CancellationNoShowResponse {
  by_department: Record<string, CancellationEntry>;
  by_doctor: Record<string, CancellationEntry>;
}

export default function Analytics() {
  const [data, setData] = useState<StatsResponse | null>(null);
  const [waitingTime, setWaitingTime] = useState<WaitingTimeResponse | null>(null);
  const [peakPeriods, setPeakPeriods] = useState<PeakPeriodsResponse | null>(null);
  const [cancellationNoShow, setCancellationNoShow] = useState<CancellationNoShowResponse | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityResponse | null>(null);
  const [eda, setEda] = useState<EdaResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchAppointmentStatistics(),
      fetchWaitingTimeAnalytics(),
      fetchPeakPeriods(),
      fetchCancellationNoShowAnalysis(),
      fetchDataQuality(),
      fetchEdaCharts(),
      fetchForecast(),
    ])
      .then(([statsRes, waitRes, peakRes, cnsRes, dqRes, edaRes, forecastRes]) => {
        setData(statsRes.data);
        setWaitingTime(waitRes.data);
        setPeakPeriods(peakRes.data);
        setCancellationNoShow(cnsRes.data);
        setDataQuality(dqRes.data);
        setEda(edaRes.data);
        setForecast(forecastRes.data);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const weekdayData = data ? Object.entries(data.weekday_distribution).map(([day, count]) => ({ day: day.slice(0, 3), count })) : [];
  const statusData = data ? Object.entries(data.statistics.status_breakdown).map(([status, count]) => ({ status, count })) : [];
  const hourlyData = peakPeriods
    ? Object.entries(peakPeriods.hourly_distribution).map(([hour, count]) => ({ hour: `${hour}:00`, count }))
    : [];
  const forecastChartData = forecast?.forecastable
    ? [
        ...(forecast.history ?? []).map((h) => ({ date: h.date, actual: h.count, predicted: null })),
        ...(forecast.forecast ?? []).map((f) => ({ date: f.date, actual: null, predicted: f.predicted_count })),
      ]
    : [];

  return (
    <PageShell title="Analytics">
      {loading && <LoadingBlock label="Computing statistics from live data..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}

      {data && data.row_count === 0 && (
        <EmptyBlock message="No appointment data yet. Statistics will populate as appointments are scheduled." />
      )}

      {data && data.row_count > 0 && (
        <>
          <p style={{ fontSize: 12.5, color: "var(--text-muted)", marginBottom: 18 }}>
            Descriptive statistics computed with pandas/NumPy over {data.row_count} appointment record(s).
          </p>

          <div className="card-grid">
            <div className="card">
              <div className="stat-label">Mean Duration</div>
              <div className="stat-value">{data.statistics.duration_minutes.mean} min</div>
            </div>
            <div className="card">
              <div className="stat-label">Median Duration</div>
              <div className="stat-value">{data.statistics.duration_minutes.median} min</div>
            </div>
            <div className="card">
              <div className="stat-label">Std. Deviation</div>
              <div className="stat-value">{data.statistics.duration_minutes.std} min</div>
            </div>
            <div className="card">
              <div className="stat-label">90th Percentile</div>
              <div className="stat-value">{data.statistics.duration_minutes.p90} min</div>
            </div>
          </div>

          <div className="two-col-grid">
            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 14 }}>Appointments by Weekday</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={weekdayData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#c8963e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 14 }}>Status Breakdown</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="status" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#6fa8dc" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ---------- Phase 1: Waiting Time ---------- */}
          <div className="card" style={{ marginTop: 18 }}>
            <h3 style={{ fontSize: 15, marginBottom: 6 }}>Waiting Time Analysis</h3>
            {!waitingTime?.has_data ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                No waiting-time data recorded yet. Use "Check-in" and "Start" on the Appointments page to
                begin collecting this data.
              </p>
            ) : (
              <div className="card-grid">
                <div className="card">
                  <div className="stat-label">Mean Wait</div>
                  <div className="stat-value">{waitingTime.mean_minutes} min</div>
                </div>
                <div className="card">
                  <div className="stat-label">Median Wait</div>
                  <div className="stat-value">{waitingTime.median_minutes} min</div>
                </div>
                <div className="card">
                  <div className="stat-label">90th Percentile</div>
                  <div className="stat-value">{waitingTime.p90_minutes} min</div>
                </div>
                <div className="card">
                  <div className="stat-label">Sample Size</div>
                  <div className="stat-value">{waitingTime.sample_size}</div>
                </div>
              </div>
            )}
          </div>

          {/* ---------- Phase 1: Peak Periods ---------- */}
          {peakPeriods && (
            <div className="card" style={{ marginTop: 18 }}>
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>Peak Periods</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
                Busiest day: <strong>{peakPeriods.peak_weekday ?? "—"}</strong> ({peakPeriods.peak_weekday_count} appointments) ·
                Busiest hour: <strong>{peakPeriods.peak_hour != null ? `${peakPeriods.peak_hour}:00` : "—"}</strong> ({peakPeriods.peak_hour_count} appointments)
              </p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={hourlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "var(--text-muted)" }} interval={2} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#e0654f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* ---------- Phase 1: Cancellation & No-Show Drill-Down ---------- */}
          {cancellationNoShow && Object.keys(cancellationNoShow.by_department).length > 0 && (
            <div className="card" style={{ marginTop: 18 }}>
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>Cancellation &amp; No-Show by Department</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
                Drills into where cancellations/no-shows are concentrated, beyond the hospital-wide rate shown on the Dashboard.
              </p>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Department</th>
                      <th>Total</th>
                      <th>Cancelled</th>
                      <th>No-Show</th>
                      <th>Cancellation Rate</th>
                      <th>No-Show Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(cancellationNoShow.by_department).map(([dept, entry]) => (
                      <tr key={dept}>
                        <td>{dept}</td>
                        <td>{entry.total}</td>
                        <td>{entry.cancelled}</td>
                        <td>{entry.no_show}</td>
                        <td>{entry.cancellation_rate_percent}%</td>
                        <td>{entry.no_show_rate_percent}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ---------- Phase 1: Demand Forecast ---------- */}
          <div className="card" style={{ marginTop: 18 }}>
            <h3 style={{ fontSize: 15, marginBottom: 4 }}>Appointment Demand Forecast</h3>
            {!forecast?.forecastable ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{forecast?.reason}</p>
            ) : (
              <>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
                  Trend: <strong>{forecast.trend_direction}</strong> · Fit quality (R²): <strong>{forecast.fit_quality_r_squared}</strong>
                </p>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={forecastChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--text-muted)" }} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-color)", borderRadius: 8 }} />
                    <Line type="monotone" dataKey="actual" stroke="#6fa8dc" strokeWidth={2} dot={false} connectNulls={false} name="Actual" />
                    <Line type="monotone" dataKey="predicted" stroke="#c8963e" strokeWidth={2} strokeDasharray="5 4" dot={false} connectNulls={false} name="Forecast" />
                  </LineChart>
                </ResponsiveContainer>
                <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 10 }}>{forecast.limitations}</p>
              </>
            )}
          </div>

          {/* ---------- Phase 1: Data Quality ---------- */}
          {dataQuality && (
            <div className="card" style={{ marginTop: 18 }}>
              <h3 style={{ fontSize: 15, marginBottom: 14 }}>Data Quality Summary</h3>
              <div className="card-grid">
                <div className="card">
                  <div className="stat-label">Patient Quality Score</div>
                  <div className="stat-value">{dataQuality.patients.quality_score_percent}%</div>
                </div>
                <div className="card">
                  <div className="stat-label">Duplicate Patients</div>
                  <div className="stat-value">{dataQuality.patients.duplicate_records}</div>
                </div>
                <div className="card">
                  <div className="stat-label">Invalid Birth Dates</div>
                  <div className="stat-value">{dataQuality.patients.invalid_dates_of_birth}</div>
                </div>
                <div className="card">
                  <div className="stat-label">Duration Outliers</div>
                  <div className="stat-value">{dataQuality.appointments.duration_outliers}</div>
                </div>
              </div>
            </div>
          )}

          {/* ---------- Phase 1: EDA (Matplotlib/Seaborn) ---------- */}
          {eda && (eda.duration_distribution || eda.weekday_hour_heatmap || eda.department_status_breakdown) && (
            <div className="card" style={{ marginTop: 18 }}>
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>Exploratory Data Analysis</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
                Generated server-side with Matplotlib/Seaborn from live data.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {eda.duration_distribution && <img src={`data:image/png;base64,${eda.duration_distribution}`} alt="Duration distribution" style={{ width: "100%", borderRadius: 10 }} />}
                {eda.weekday_hour_heatmap && <img src={`data:image/png;base64,${eda.weekday_hour_heatmap}`} alt="Weekday x hour heatmap" style={{ width: "100%", borderRadius: 10 }} />}
                {eda.department_status_breakdown && <img src={`data:image/png;base64,${eda.department_status_breakdown}`} alt="Department status breakdown" style={{ width: "100%", borderRadius: 10 }} />}
              </div>
            </div>
          )}

          <div className="card" style={{ marginTop: 18 }}>
            <h3 style={{ fontSize: 15, marginBottom: 8 }}>ML No-Show Prediction</h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              A full no-show risk pipeline (Logistic Regression, Decision Tree, Random Forest, and
              XGBoost when available) with cross-validation and a live prediction endpoint is now
              available on the <Link to="/predictions" style={{ color: "var(--accent)", fontWeight: 600 }}>Predictions</Link> page.
            </p>
          </div>
        </>
      )}
    </PageShell>
  );
}
