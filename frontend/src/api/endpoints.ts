import { api } from "./client";

// ---------- Auth ----------
export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  full_name: string;
  email: string;
}

export const login = (email: string, password: string) =>
  api.post<LoginResponse>("/auth/login-json", { email, password });

export const fetchMe = () => api.get("/auth/me");

// ---------- Departments ----------
export const fetchDepartments = () => api.get("/departments");
export const createDepartment = (data: any) => api.post("/departments", data);
export const updateDepartment = (id: number, data: any) => api.put(`/departments/${id}`, data);
export const deleteDepartment = (id: number) => api.delete(`/departments/${id}`);

// ---------- Doctors ----------
export const fetchDoctors = (params?: any) => api.get("/doctors", { params });
export const createDoctor = (data: any) => api.post("/doctors", data);
export const updateDoctor = (id: number, data: any) => api.put(`/doctors/${id}`, data);
export const deleteDoctor = (id: number) => api.delete(`/doctors/${id}`);

// ---------- Patients ----------
export const fetchPatients = (params?: any) => api.get("/patients", { params });
export const createPatient = (data: any) => api.post("/patients", data);
export const updatePatient = (id: number, data: any) => api.put(`/patients/${id}`, data);
export const deletePatient = (id: number) => api.delete(`/patients/${id}`);

// ---------- Appointments ----------
export const fetchAppointments = (params?: any) => api.get("/appointments", { params });
export const createAppointment = (data: any) => api.post("/appointments", data);
export const updateAppointment = (id: number, data: any) => api.put(`/appointments/${id}`, data);
export const cancelAppointment = (id: number) => api.post(`/appointments/${id}/cancel`);
export const completeAppointment = (id: number) => api.post(`/appointments/${id}/complete`);
export const noShowAppointment = (id: number) => api.post(`/appointments/${id}/no-show`);
export const checkInAppointment = (id: number) => api.post(`/appointments/${id}/check-in`);
export const startAppointment = (id: number) => api.post(`/appointments/${id}/start`);
export const deleteAppointment = (id: number) => api.delete(`/appointments/${id}`);

// ---------- Dashboard & Analytics ----------
export const fetchDashboardSummary = () => api.get("/dashboard/summary");
export const fetchAppointmentStatistics = () => api.get("/analytics/appointment-statistics");
export const fetchWaitingTimeAnalytics = () => api.get("/analytics/waiting-time");
export const fetchPeakPeriods = () => api.get("/analytics/peak-periods");
export const fetchCancellationNoShowAnalysis = () => api.get("/analytics/cancellation-no-show");
export const fetchDataQuality = () => api.get("/analytics/data-quality");
export const fetchEdaCharts = () => api.get("/analytics/eda-charts");
export const fetchForecast = (params?: { department_id?: number; horizon_days?: number }) =>
  api.get("/analytics/forecast", { params });
export const fetchAlerts = () => api.get("/analytics/alerts");

// ---------- ML / Predictions ----------
export const trainModel = () => api.post("/ml/train");
export const fetchModelInfo = () => api.get("/ml/model-info");
export const predictNoShow = (data: any) => api.post("/ml/predict-no-show", data);

// ---------- Reports ----------
export const fetchAppointmentReport = (params?: any) => api.get("/reports/appointments", { params });
