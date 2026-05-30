"use client";
import { useState, useRef } from "react";
import { useAuthStore } from "@/lib/stores/authStore";
import { streamSSE, notesAPI } from "@/lib/api";
import { FileText, Download, Zap, BookOpen } from "lucide-react";

const EXAM_SUBJECTS: Record<string, string[]> = {
  CA_FOUNDATION: ["Principles and Practice of Accounting","Business Mathematics","Business Economics","Business and Commercial Knowledge"],
  CA_INTERMEDIATE: ["Advanced Accounting","Corporate Laws","Cost and Management Accounting","Taxation","Auditing"],
  CA_FINAL: ["Financial Reporting","Strategic Financial Management","Advanced Auditing","Direct Tax Laws","Indirect Tax Laws"],
  JEE: ["Physics","Chemistry","Mathematics"],
  NEET: ["Physics","Chemistry","Biology"],
};

interface GenerationState {
  status: "idle" | "generating" | "complete" | "error";
  step: number;
  totalSteps: number;
  message: string;
  pdfUrl?: string;
  docxUrl?: string;
  fromCache?: boolean;
  confidence?: number;
  timingMs?: number;
}

export default function NotesPage() {
  const { user, token } = useAuthStore();
  const [exam, setExam] = useState("CA_FOUNDATION");
  const [subject, setSubject] = useState("");
  const [chapterId, setChapterId] = useState("");
  const [chapterName, setChapterName] = useState("");
  const [language, setLanguage] = useState("English");
  const [gen, setGen] = useState<GenerationState>({ status: "idle", step: 0, totalSteps: 9, message: "" });
  const [recentNotes, setRecentNotes] = useState<any[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const subjects = EXAM_SUBJECTS[exam] || [];

  const handleGenerate = async () => {
    if (!chapterName.trim() || !subject) return;
    abortRef.current = new AbortController();
    setGen({ status: "generating", step: 0, totalSteps: 9, message: "Starting..." });

    try {
      const fakeChapterId = chapterId || `temp-${Date.now()}`;
      for await (const chunk of streamSSE("/notes/generate", {
        exam, subject, chapter_id: fakeChapterId, chapter_name: chapterName, language,
      }, token || "")) {
        if (chunk.type === "start") setGen(g => ({ ...g, message: chunk.message as string || "Starting..." }));
        else if (chunk.type === "progress") setGen(g => ({ ...g, step: chunk.step as number, message: chunk.message as string || "" }));
        else if (chunk.type === "complete") {
          setGen({ status: "complete", step: 9, totalSteps: 9, message: "Notes ready!",
            pdfUrl: chunk.pdf_url as string, docxUrl: chunk.docx_url as string,
            fromCache: chunk.from_cache as boolean, confidence: chunk.confidence as number,
            timingMs: chunk.timing_ms as number });
        } else if (chunk.type === "error") {
          setGen({ status: "error", step: 0, totalSteps: 9, message: chunk.message as string || "Error occurred" });
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") setGen({ status: "error", step: 0, totalSteps: 9, message: "Connection failed. Please try again." });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Chapter Details</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1">Exam</label>
              <select value={exam} onChange={(e) => { setExam(e.target.value); setSubject(""); }}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {["CA_FOUNDATION","CA_INTERMEDIATE","CA_FINAL","JEE","NEET"].map(e => (
                  <option key={e} value={e}>{e.replace("_"," ")}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1">Subject</label>
              <select value={subject} onChange={(e) => setSubject(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select subject...</option>
                {subjects.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-600 mb-1">Chapter Name</label>
              <input value={chapterName} onChange={(e) => setChapterName(e.target.value)}
                placeholder="e.g. Partnership Accounts, Thermodynamics, Cell Division"
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1">Language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {["English","Bengali","Hindi","Tamil","Telugu"].map(l => <option key={l}>{l}</option>)}
              </select>
            </div>
          </div>

          <button onClick={handleGenerate}
            disabled={gen.status === "generating" || !subject || !chapterName.trim()}
            className="mt-6 w-full flex items-center justify-center gap-2 bg-blue-600 text-white rounded-xl py-3 font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
            <Zap size={16} />
            {gen.status === "generating" ? "Generating..." : "Generate Premium Notes"}
          </button>
        </div>

        {/* Generation Progress */}
        {(gen.status === "generating" || gen.status === "complete" || gen.status === "error") && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            {gen.status === "generating" && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  <p className="text-slate-700 font-medium">{gen.message}</p>
                </div>
                <div className="h-2 bg-slate-100 rounded-full">
                  <div className="h-2 bg-blue-600 rounded-full transition-all duration-500"
                    style={{ width: `${(gen.step / gen.totalSteps) * 100}%` }} />
                </div>
                <p className="text-xs text-slate-400">
                  7 AI agents working in parallel — Claude 3.5 Sonnet + GPT-4o + Gemini 1.5 Pro
                </p>
              </div>
            )}

            {gen.status === "complete" && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-green-700">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-lg">✅</div>
                  <div>
                    <p className="font-semibold">Notes Generated Successfully!</p>
                    <p className="text-xs text-slate-500">
                      {gen.fromCache ? "⚡ Served from cache instantly" : `Generated in ${((gen.timingMs || 0)/1000).toFixed(1)}s`}
                      {" · "}Confidence: {Math.round((gen.confidence || 0) * 100)}%
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  {gen.pdfUrl && (
                    <a href={gen.pdfUrl} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors">
                      <Download size={14} /> Download PDF
                    </a>
                  )}
                  {gen.docxUrl && (
                    <a href={gen.docxUrl} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 border border-slate-200 px-4 py-2 rounded-lg text-sm hover:bg-slate-50 transition-colors">
                      <FileText size={14} /> Download DOCX
                    </a>
                  )}
                </div>
              </div>
            )}

            {gen.status === "error" && (
              <div className="flex items-center gap-3 text-red-700">
                <span className="text-xl">⚠️</span>
                <div>
                  <p className="font-medium">Generation Failed</p>
                  <p className="text-sm text-slate-500">{gen.message}</p>
                  <button onClick={handleGenerate} className="mt-2 text-sm text-blue-600 hover:underline">
                    Try again →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
