/**
 * EkalavyaAI — Frontend API Client
 * Axios instance with JWT auth interceptor + SSE streaming helpers
 */
import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Axios Instance ──────────────────────────────────────────────────────────
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — redirect to login
apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/auth/login";
    }
    return Promise.reject(error);
  }
);

// ─── SSE Streaming Helper ────────────────────────────────────────────────────
export interface SSEChunk {
  type: "start" | "progress" | "chunk" | "complete" | "error";
  content?: string;
  message?: string;
  step?: number;
  total?: number;
  pdf_url?: string;
  docx_url?: string;
  confidence?: number;
  from_cache?: boolean;
  timing_ms?: number;
  session_id?: string;
  [key: string]: unknown;
}

export async function* streamSSE(
  url: string,
  body: Record<string, unknown>,
  token: string
): AsyncGenerator<SSEChunk> {
  const response = await fetch(`${API_BASE}/api/v1${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    let currentData = "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        currentData = line.slice(6).trim();
      } else if (line === "" && currentEvent && currentData) {
        try {
          const parsed = JSON.parse(currentData);
          yield { type: currentEvent as SSEChunk["type"], ...parsed };
        } catch {
          // skip malformed
        }
        currentEvent = "";
        currentData = "";
      }
    }
  }
}

// ─── Auth helpers ────────────────────────────────────────────────────────────
export const authAPI = {
  signup: (data: { name: string; email: string; password: string; referral_code?: string }) =>
    apiClient.post("/auth/signup", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  google: (token: string) => apiClient.post("/auth/google", { google_token: token }),
  logout: () => apiClient.post("/auth/logout"),
};

// ─── Student helpers ─────────────────────────────────────────────────────────
export const studentAPI = {
  getProfile: () => apiClient.get("/student/profile"),
  updateProfile: (data: Record<string, unknown>) => apiClient.put("/student/profile", data),
  completeOnboarding: (data: Record<string, unknown>) => apiClient.post("/student/onboarding", data),
  getCredits: () => apiClient.get("/student/credits"),
  getReferral: () => apiClient.get("/student/referral"),
  applyReferral: (code: string) => apiClient.post(`/student/referral?referral_code=${code}`),
};

// ─── Notes helpers ───────────────────────────────────────────────────────────
export const notesAPI = {
  list: (params?: Record<string, unknown>) => apiClient.get("/notes", { params }),
  get: (id: string) => apiClient.get(`/notes/${id}`),
  getPDFUrl: (id: string) => apiClient.get(`/notes/${id}/pdf`),
  checkCache: (key: string) => apiClient.get(`/notes/cache/${key}`),
};

// ─── Progress helpers ────────────────────────────────────────────────────────
export const progressAPI = {
  getReadiness: (exam?: string) => apiClient.get("/progress/readiness", { params: { exam } }),
  getSyllabus: (exam: string) => apiClient.get("/progress/syllabus", { params: { exam } }),
  getRevisions: () => apiClient.get("/progress/revision"),
  getWeeklyReport: () => apiClient.get("/progress/report"),
};

// ─── Practice helpers ────────────────────────────────────────────────────────
export const practiceAPI = {
  getQuestions: (params: Record<string, unknown>) => apiClient.get("/practice/questions", { params }),
  submitAttempt: (data: { question_id: string; student_answer: string; time_taken_seconds?: number }) =>
    apiClient.post("/practice/attempt", data),
  getMistakes: () => apiClient.get("/practice/mistakes"),
};
