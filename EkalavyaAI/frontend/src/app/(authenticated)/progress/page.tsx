"use client";
import { useEffect, useState } from "react";
import { progressAPI } from "@/lib/api";
import type { ReadinessData, SyllabusData, WeeklyReport } from "@/lib/types";
import { TrendingUp, BookOpen, Target, Calendar } from "lucide-react";
import { ReadinessGauge } from "@/components/features/ReadinessGauge";

export default function ProgressPage() {
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [syllabus, setSyllabus] = useState<SyllabusData | null>(null);
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [exam, setExam] = useState("CA_FOUNDATION");
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [exam]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [r, s, rep] = await Promise.all([
        progressAPI.getReadiness(exam),
        progressAPI.getSyllabus(exam),
        progressAPI.getWeeklyReport(),
      ]);
      setReadiness(r.data); setSyllabus(s.data); setReport(rep.data);
    } finally { setLoading(false); }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"/></div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Page title + exam selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <TrendingUp size={20} className="text-purple-600"/>
            <h1 className="text-xl font-bold text-slate-800">My Progress</h1>
          </div>
          <select value={exam} onChange={(e) => setExam(e.target.value)}
            className="text-sm border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            {["CA_FOUNDATION","CA_INTERMEDIATE","CA_FINAL","JEE","NEET"].map(e => (
              <option key={e} value={e}>{e.replace(/_/g," ")}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: <BookOpen size={18} className="text-blue-600"/>, label: "Chapters Studied", value: readiness?.chapters_studied || 0, bg: "bg-blue-50" },
            { icon: <Target size={18} className="text-green-600"/>, label: "PYQ Accuracy", value: `${readiness?.breakdown?.pyq_accuracy || 0}%`, bg: "bg-green-50" },
            { icon: <TrendingUp size={18} className="text-purple-600"/>, label: "Syllabus Coverage", value: `${readiness?.breakdown?.syllabus_coverage || 0}%`, bg: "bg-purple-50" },
            { icon: <Calendar size={18} className="text-amber-600"/>, label: "Login Streak 🔥", value: `${readiness?.login_streak || 0} days`, bg: "bg-amber-50" },
          ].map((s) => (
            <div key={s.label} className={`${s.bg} rounded-xl p-4`}>
              {s.icon}
              <div className="font-bold text-2xl text-slate-800 mt-2">{s.value}</div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <ReadinessGauge score={readiness?.readiness_score || 0} exam={exam} />

          <div className="md:col-span-2 bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-700 mb-4">Grade Prediction</h3>
            <div className="text-2xl font-bold text-blue-700 mb-1">{readiness?.grade_prediction || "—"}</div>
            <div className="space-y-2 mt-4">
              {[
                { label: "Syllabus Coverage", val: readiness?.breakdown?.syllabus_coverage || 0 },
                { label: "PYQ Accuracy", val: readiness?.breakdown?.pyq_accuracy || 0 },
                { label: "Revision Rate", val: readiness?.breakdown?.revision_completion || 0 },
                { label: "Concept Depth", val: readiness?.breakdown?.concept_depth || 0 },
              ].map(({ label, val }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs text-slate-500 mb-1"><span>{label}</span><span>{val}%</span></div>
                  <div className="h-1.5 bg-slate-100 rounded-full"><div className="h-1.5 bg-blue-500 rounded-full" style={{ width: `${val}%` }}/></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Weekly AI Report */}
        {report?.report_text && (
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-6 text-white">
            <h3 className="font-semibold mb-3 flex items-center gap-2">🤖 AI Weekly Report</h3>
            <p className="text-blue-100 text-sm leading-relaxed">{report.report_text}</p>
          </div>
        )}

        {/* Syllabus Heatmap */}
        {syllabus?.subjects && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="font-semibold text-slate-700 mb-4">Syllabus Coverage — {exam.replace("_"," ")}</h3>
            <div className="space-y-5">
              {Object.entries(syllabus.subjects as Record<string, any>).map(([subject, data]) => (
                <div key={subject}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-slate-700">{subject}</span>
                    <span className="text-slate-400">{data.studied}/{data.total} chapters ({data.coverage_pct}%)</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full mb-2">
                    <div className="h-2 bg-blue-500 rounded-full transition-all" style={{ width: `${data.coverage_pct}%` }}/>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.chapters.slice(0,12).map((ch: any) => (
                      <span key={ch.id} className={`text-xs px-2 py-0.5 rounded-full ${ch.studied ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-400"}`}>
                        {ch.chapter_no}. {ch.name.slice(0,20)}{ch.name.length > 20 ? "..." : ""}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
