/**
 * EkalavyaAI — Shared TypeScript Types
 */

// ─── API Response Types ───────────────────────────────────────────────────────
export interface ReadinessData {
  readiness_score: number;
  exam: string;
  breakdown: {
    syllabus_coverage: number;
    pyq_accuracy: number;
    revision_completion: number;
    concept_depth: number;
  };
  chapters_studied: number;
  pyq_solved: number;
  credits: number;
  login_streak: number;
  level: string;
  grade_prediction: string;
}

export interface SyllabusSubject {
  chapters: ChapterStatus[];
  studied: number;
  total: number;
  coverage_pct: number;
}

export interface ChapterStatus {
  id: string;
  name: string;
  chapter_no: number;
  importance_score: number;
  pyq_frequency: number;
  studied: boolean;
}

export interface SyllabusData {
  exam: string;
  subjects: Record<string, SyllabusSubject>;
  overall_coverage: number;
}

export interface WeeklyReport {
  student_id: string;
  report_text: string;
  generated_at: string;
  readiness_score: Record<string, number>;
}

export interface Note {
  id: string;
  chapter_name: string;
  exam: string;
  subject: string;
  language: string;
  pdf_url?: string;
  docx_url?: string;
  quality_score: number;
  from_cache: boolean;
  created_at: string;
}

export interface Revision {
  id: string;
  chapter_id: string;
  chapter_name: string;
  subject: string;
  exam: string;
  due_date: string;
  is_overdue: boolean;
  sm2_level: number;
  priority: number;
}

export interface Question {
  id: string;
  year: number;
  month?: string;
  marks: number;
  question_type: "MCQ" | "DESCRIPTIVE" | "NUMERICAL";
  question_text: string;
  options?: Record<string, string>;
  difficulty: number;
  exam: string;
}

export interface AttemptResult {
  is_correct: boolean;
  correct_answer: string;
  solution: string;
  explanation: string;
  examiner_notes?: string;
  attempt_id: string;
}

export interface ProgressStats {
  readiness_score: number;
  chapters_studied: number;
  pyq_solved: number;
  credits: number;
  login_streak: number;
}
