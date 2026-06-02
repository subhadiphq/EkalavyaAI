/**
 * EkalavyaAI — Zustand Auth + Student Stores
 * Persisted across sessions with localStorage + cookie for middleware
 */
"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ReadinessData, Note, Revision } from "../types";

export interface User {
  id: string;
  name: string;
  email: string;
  plan: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", token);
          // Set cookie so middleware can read it (httpOnly not needed for client-side JWT)
          document.cookie = `access_token=${token}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
        }
        set({ user, token, isAuthenticated: true });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          document.cookie = "access_token=; path=/; max-age=0";
        }
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: "ekalavya-auth",
      partialize: (s) => ({ user: s.user, token: s.token, isAuthenticated: s.isAuthenticated }),
    }
  )
);

// ─── Student Store ─────────────────────────────────────────────
export interface StudentProfile {
  exam_targets: string[];
  exam_dates: Record<string, string>;
  level: string;
  language: string;
  weak_chapters: string[];
  login_streak: number;
  readiness_scores: Record<string, number>;
  onboarding_complete: boolean;
}

interface StudentState {
  profile: StudentProfile | null;
  progress: ReadinessData | null;
  recentNotes: Note[];
  revisions: Revision[];
  setProfile: (p: StudentProfile) => void;
  setProgress: (p: ReadinessData) => void;
  setRecentNotes: (n: Note[]) => void;
  setRevisions: (r: Revision[]) => void;
  reset: () => void;
}

export const useStudentStore = create<StudentState>()((set) => ({
  profile: null,
  progress: null,
  recentNotes: [],
  revisions: [],
  setProfile: (profile) => set({ profile }),
  setProgress: (progress) => set({ progress }),
  setRecentNotes: (recentNotes) => set({ recentNotes }),
  setRevisions: (revisions) => set({ revisions }),
  reset: () => set({ profile: null, progress: null, recentNotes: [], revisions: [] }),
}));
