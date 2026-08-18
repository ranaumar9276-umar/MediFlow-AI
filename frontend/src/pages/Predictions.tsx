import { FormEvent, useEffect, useState } from "react";
import PageShell from "../components/PageShell";
import { LoadingBlock, ErrorBlock } from "../components/StateBlocks";
import { fetchDepartments, fetchDoctors, fetchModelInfo, predictNoShow, trainModel } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number | null;
  confusion_matrix: { true_negative: number; false_positive: number; false_negative: number; true_positive: number };
}

interface ComparisonEntry {
  model_name: string;
  cv_metrics: Record<string, any>;
  test_metrics: ModelMetrics;
}

interface ModelInfo {
  model_available: boolean;
  message?: string;
  best_model?: string;
  best_metrics?: ModelMetrics;
  comparison?: ComparisonEntry[];
  class_balance?: { positive_rate: number; is_imbalanced: boolean; positive_count: number; negative_count: number };
  cross_validated?: boolean;
}

const predictFormDefaults = {
  department_id: "",
  doctor_id: "",
  scheduled_at: "",
  duration_minutes: 30,
  patient_prior_appointment_count: 0,
  patient_prior_no_show_rate: 0,
};

export default function Predictions() {
  const { user } = useAuth();
  const canTrain = user && ["ADMIN", "HOSPITAL_MANAGER"].includes(user.role);

  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);

  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
  const [doctors, setDoctors] = useState<{ id: number; full_name: string; department_id: number }[]>([]);
  const [predictForm, setPredictForm] = useState(predictFormDefaults);
  const [predicting, setPredicting] = useState(false);
  const [predictResult, setPredictResult] = useState<{ no_show_risk_probability: number; risk_level: string; model_used: string } | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([fetchModelInfo(), fetchDepartments(), fetchDoctors({ limit: 200 })])
      .then(([infoRes, deptRes, docRes]) => {
        setModelInfo(infoRes.data);
        setDepartments(deptRes.data);
        setDoctors(docRes.data.items);
      })
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleTrain = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const res = await trainModel();
      if (res.data.trained) {
        setTrainMessage(`Training complete. Best model: ${res.data.best_model} (F1 = ${res.data.metrics.f1}).`);
      } else {
        setTrainMessage(res.data.reason);
      }
      load();
    } catch (err) {
      setTrainMessage(apiErrorMessage(err));
    } finally {
      setTraining(false);
    }
  };

  const handlePredict = async (e: FormEvent) => {
    e.preventDefault();
    setPredicting(true);
    setPredictError(null);
    setPredictResult(null);
    try {
      const res = await predictNoShow({
        doctor_id: Number(predictForm.doctor_id),
        department_id: Number(predictForm.department_id),
        scheduled_at: new Date(predictForm.scheduled_at).toISOString(),
        duration_minutes: predictForm.duration_minutes,
        patient_prior_appointment_count: predictForm.patient_prior_appointment_count,
        patient_prior_no_show_rate: predictForm.patient_prior_no_show_rate,
      });
      setPredictResult(res.data);
    } catch (err) {
      setPredictError(apiErrorMessage(err));
    } finally {
      setPredicting(false);
    }
  };

  const doctorsInDept = doctors.filter((d) => !predictForm.department_id || d.department_id === Number(predictForm.department_id));

  return (
    <PageShell title="Predictions">
      {loading && <LoadingBlock label="Loading model status..." />}
      {error && <ErrorBlock message={error} onRetry={load} />}

      {!loading && !error && (
        <>
          <div className="card" style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
              <div>
                <h3 style={{ fontSize: 15, marginBottom: 6 }}>No-Show Risk Model</h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  Compares Logistic Regression, Decision Tree, and Random Forest (plus XGBoost if
                  installed) with cross-validation on real appointment history, and selects the best
                  by test-set F1 score.
                </p>
              </div>
              {canTrain && (
                <button className="btn btn-primary" onClick={handleTrain} disabled={training}>
                  {training ? "Training..." : "Train / Retrain Model"}
                </button>
              )}
            </div>
            {trainMessage && <div className="form-error" style={{ background: "var(--bg-surface-2)", color: "var(--text-primary)", borderColor: "var(--border-color)", marginTop: 14 }}>{trainMessage}</div>}

            {!modelInfo?.model_available && (
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 14 }}>
                {modelInfo?.message ?? "No model trained yet."}
              </p>
            )}

            {modelInfo?.model_available && modelInfo.best_metrics && (
              <>
                <div className="card-grid" style={{ marginTop: 18 }}>
                  <div className="card">
                    <div className="stat-label">Best Model</div>
                    <div className="stat-value" style={{ fontSize: 18 }}>{modelInfo.best_model}</div>
                  </div>
                  <div className="card">
                    <div className="stat-label">F1 Score</div>
                    <div className="stat-value">{modelInfo.best_metrics.f1}</div>
                  </div>
                  <div className="card">
                    <div className="stat-label">ROC-AUC</div>
                    <div className="stat-value">{modelInfo.best_metrics.roc_auc ?? "N/A"}</div>
                  </div>
                  <div className="card">
                    <div className="stat-label">Recall</div>
                    <div className="stat-value">{modelInfo.best_metrics.recall}</div>
                  </div>
                </div>

                {modelInfo.class_balance?.is_imbalanced && (
                  <div className="form-error" style={{ marginTop: 14 }}>
                    ⚠ Class imbalance detected: {(modelInfo.class_balance.positive_rate * 100).toFixed(1)}%
                    positive (no-show) rate in training data. Precision/recall matter more than raw
                    accuracy here.
                  </div>
                )}

                {modelInfo.comparison && (
                  <div className="table-wrap" style={{ marginTop: 18 }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Model</th>
                          <th>CV F1 (mean)</th>
                          <th>Test Accuracy</th>
                          <th>Test Precision</th>
                          <th>Test Recall</th>
                          <th>Test F1</th>
                          <th>ROC-AUC</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelInfo.comparison.map((c) => (
                          <tr key={c.model_name} style={c.model_name === modelInfo.best_model ? { background: "var(--accent-soft)" } : {}}>
                            <td>{c.model_name}{c.model_name === modelInfo.best_model ? " ★" : ""}</td>
                            <td>{c.cv_metrics?.f1_mean ?? "—"}</td>
                            <td>{c.test_metrics.accuracy}</td>
                            <td>{c.test_metrics.precision}</td>
                            <td>{c.test_metrics.recall}</td>
                            <td>{c.test_metrics.f1}</td>
                            <td>{c.test_metrics.roc_auc ?? "N/A"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="card">
            <h3 style={{ fontSize: 15, marginBottom: 6 }}>Predict No-Show Risk</h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
              Estimate the no-show risk for a candidate appointment using the currently trained model.
            </p>

            {!modelInfo?.model_available ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                Train a model above before making predictions.
              </p>
            ) : (
              <form onSubmit={handlePredict}>
                <div className="form-grid">
                  <div className="form-field">
                    <label>Department</label>
                    <select required value={predictForm.department_id} onChange={(e) => setPredictForm({ ...predictForm, department_id: e.target.value, doctor_id: "" })}>
                      <option value="">Select department</option>
                      {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div className="form-field">
                    <label>Doctor</label>
                    <select required value={predictForm.doctor_id} onChange={(e) => setPredictForm({ ...predictForm, doctor_id: e.target.value })}>
                      <option value="">Select doctor</option>
                      {doctorsInDept.map((d) => <option key={d.id} value={d.id}>{d.full_name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-grid">
                  <div className="form-field">
                    <label>Scheduled Date &amp; Time</label>
                    <input type="datetime-local" required value={predictForm.scheduled_at} onChange={(e) => setPredictForm({ ...predictForm, scheduled_at: e.target.value })} />
                  </div>
                  <div className="form-field">
                    <label>Duration (minutes)</label>
                    <input type="number" min={5} max={480} value={predictForm.duration_minutes} onChange={(e) => setPredictForm({ ...predictForm, duration_minutes: Number(e.target.value) })} />
                  </div>
                </div>
                <div className="form-grid">
                  <div className="form-field">
                    <label>Patient's Prior Appointments</label>
                    <input type="number" min={0} value={predictForm.patient_prior_appointment_count} onChange={(e) => setPredictForm({ ...predictForm, patient_prior_appointment_count: Number(e.target.value) })} />
                  </div>
                  <div className="form-field">
                    <label>Patient's Prior No-Show Rate (0-1)</label>
                    <input type="number" min={0} max={1} step={0.05} value={predictForm.patient_prior_no_show_rate} onChange={(e) => setPredictForm({ ...predictForm, patient_prior_no_show_rate: Number(e.target.value) })} />
                  </div>
                </div>

                {predictError && <div className="form-error">{predictError}</div>}

                <button type="submit" className="btn btn-primary" disabled={predicting}>
                  {predicting ? "Predicting..." : "Predict Risk"}
                </button>
              </form>
            )}

            {predictResult && (
              <div
                className="card"
                style={{
                  marginTop: 18,
                  borderColor:
                    predictResult.risk_level === "HIGH" ? "var(--danger)" : predictResult.risk_level === "MEDIUM" ? "var(--warning)" : "var(--success)",
                }}
              >
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Predicted no-show risk</div>
                <div className="stat-value" style={{ fontSize: 32 }}>
                  {(predictResult.no_show_risk_probability * 100).toFixed(1)}%
                </div>
                <span
                  className={`badge ${predictResult.risk_level === "HIGH" ? "badge-cancelled" : predictResult.risk_level === "MEDIUM" ? "badge-no_show" : "badge-completed"}`}
                >
                  {predictResult.risk_level} RISK
                </span>
                <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 10 }}>
                  Model used: {predictResult.model_used}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </PageShell>
  );
}
