"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Calendar, FileText, Send } from "lucide-react";
import type { Revision, Note } from "@/lib/types";

export function RevisionCard({ revision }: { revision: Revision }) {
  const isOverdue = revision.is_overdue;
  return (
    <Link href={`/notes?chapter=${revision.chapter_id}`}
      className="block bg-white border border-slate-200 rounded-lg p-3 hover:border-amber-300 hover:shadow-sm transition-all">
      <div className="flex items-start gap-2">
        <Calendar size={14} className={isOverdue ? "text-red-500 mt-0.5" : "text-amber-500 mt-0.5"} />
        <div>
          <p className="text-sm font-medium text-slate-700 line-clamp-1">{revision.chapter_name}</p>
          <p className="text-xs text-slate-400">{revision.subject}</p>
          <p className={`text-xs mt-1 ${isOverdue ? "text-red-500" : "text-amber-600"}`}>
            {isOverdue ? "⚠️ Overdue" : "Due today"}
          </p>
        </div>
      </div>
    </Link>
  );
}

export function RecentNoteCard({ note }: { note: Note }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-3">
        <FileText size={16} className="text-blue-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-700 line-clamp-1">{note.chapter_name}</p>
          <p className="text-xs text-slate-400">{note.subject} · {note.exam}</p>
        </div>
        {note.pdf_url && (
          <a href={note.pdf_url} target="_blank" rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:underline shrink-0">PDF</a>
        )}
      </div>
      <div className="mt-2 flex items-center gap-2">
        <div className="h-1.5 flex-1 bg-slate-100 rounded-full">
          <div className="h-1.5 bg-blue-500 rounded-full" style={{ width: `${(note.quality_score || 0) * 100}%` }} />
        </div>
        <span className="text-xs text-slate-400">{Math.round((note.quality_score || 0) * 100)}%</span>
      </div>
    </div>
  );
}

export function QuickAskBar({ exam }: { exam: string }) {
  const [question, setQuestion] = useState("");
  const router = useRouter();
  const handleSubmit = () => {
    if (!question.trim()) return;
    router.push(`/chat?q=${encodeURIComponent(question)}&exam=${exam}`);
  };
  return (
    <div className="flex gap-2">
      <input value={question} onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        placeholder={`Ask a ${exam.replace("_", " ")} doubt...`}
        className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white" />
      <button onClick={handleSubmit}
        className="bg-blue-600 text-white px-4 py-2.5 rounded-xl hover:bg-blue-700 transition-colors">
        <Send size={16} />
      </button>
    </div>
  );
}
