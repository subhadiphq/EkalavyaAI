"use client";
import { useState, useEffect } from "react";
import { practiceAPI } from "@/lib/api";
import type { Question, AttemptResult } from "@/lib/types";
import { Target, Clock, CheckCircle, XCircle } from "lucide-react";



export default function PracticePage() {
  const [exam, setExam] = useState("CA_FOUNDATION");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    let t: ReturnType<typeof setInterval>;
    if (timerActive) t = setInterval(() => setTimer(n => n + 1), 1000);
    return () => clearInterval(t);
  }, [timerActive]);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const res = await practiceAPI.getQuestions({ exam, limit: 10 });
      setQuestions(res.data.questions);
      setCurrent(0); setAnswer(""); setResult(null); setFeedback("");
      setTimer(0); setTimerActive(true);
    } finally { setLoading(false); }
  };

  const handleSubmit = async () => {
    if (!answer.trim()) return;
    setTimerActive(false);
    const q = questions[current];
    try {
      const res = await practiceAPI.submitAttempt({ question_id: q.id, student_answer: answer, time_taken_seconds: timer });
      setResult(res.data);
      setScore(s => ({ correct: s.correct + (res.data.is_correct ? 1 : 0), total: s.total + 1 }));
    } catch { setResult(null); }
  };

  const nextQuestion = () => {
    if (current < questions.length - 1) {
      setCurrent(c => c + 1); setAnswer(""); setResult(null); setFeedback(""); setTimer(0); setTimerActive(true);
    }
  };

  const q = questions[current];
  const fmtTime = (s: number) => `${Math.floor(s/60).toString().padStart(2,"0")}:${(s%60).toString().padStart(2,"0")}`;

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-5">
        {/* Setup */}
        {questions.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center space-y-4">
            <div className="text-4xl">🎯</div>
            <h2 className="text-xl font-semibold text-slate-800">Practice Past Year Questions</h2>
            <p className="text-slate-500 text-sm">10 years of verified PYQ with AI feedback</p>
            <select value={exam} onChange={(e) => setExam(e.target.value)}
              className="border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              {["CA_FOUNDATION","CA_INTERMEDIATE","CA_FINAL","JEE","NEET"].map(e => <option key={e} value={e}>{e.replace("_"," ")}</option>)}
            </select>
            <button onClick={loadQuestions} disabled={loading}
              className="block w-full bg-green-600 text-white rounded-xl py-3 font-medium hover:bg-green-700 disabled:opacity-40">
              {loading ? "Loading..." : "Start Practice Session"}
            </button>
          </div>
        )}

        {/* Question */}
        {q && (
          <>
            <div className="flex items-center justify-between text-sm text-slate-500">
              <span>Question {current + 1} / {questions.length}</span>
              <div className="flex items-center gap-2"><Clock size={14}/>{fmtTime(timer)}</div>
              <span className="text-amber-600 font-medium">{q.marks} marks · {q.year}</span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <p className="text-slate-800 leading-relaxed">{q.question_text}</p>

              {q.question_type === "MCQ" && q.options ? (
                <div className="mt-4 space-y-2">
                  {Object.entries(q.options).map(([k, v]) => (
                    <button key={k} onClick={() => setAnswer(k)} disabled={!!result}
                      className={`w-full text-left px-4 py-3 rounded-xl border-2 text-sm transition-all ${answer === k ? "border-blue-600 bg-blue-50" : "border-slate-200 hover:border-blue-200"} ${result && k === result.correct_answer ? "border-green-500 bg-green-50" : ""} ${result && answer === k && !result.is_correct ? "border-red-400 bg-red-50" : ""}`}>
                      <span className="font-bold mr-2">{k}.</span>{v}
                    </button>
                  ))}
                </div>
              ) : (
                <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} disabled={!!result}
                  placeholder="Write your answer here..." rows={6}
                  className="mt-4 w-full border border-slate-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" />
              )}

              {!result && (
                <button onClick={handleSubmit} disabled={!answer.trim()}
                  className="mt-4 w-full bg-blue-600 text-white rounded-xl py-2.5 font-medium hover:bg-blue-700 disabled:opacity-40">
                  Submit Answer
                </button>
              )}
            </div>

            {/* Result */}
            {result && (
              <div className={`rounded-2xl border-2 p-5 ${result.is_correct ? "border-green-400 bg-green-50" : "border-red-300 bg-red-50"}`}>
                <div className="flex items-center gap-2 font-semibold mb-3">
                  {result.is_correct ? <CheckCircle className="text-green-600"/> : <XCircle className="text-red-500"/>}
                  <span className={result.is_correct ? "text-green-700" : "text-red-600"}>{result.is_correct ? "Correct! ✅" : `Wrong — Answer: ${result.correct_answer}`}</span>
                </div>
                <div className="text-sm text-slate-700 space-y-2">
                  <p><strong>Solution:</strong> {result.solution}</p>
                  {result.explanation && <p><strong>Explanation:</strong> {result.explanation}</p>}
                </div>
                <div className="mt-4 flex gap-3">
                  <button onClick={nextQuestion} disabled={current === questions.length - 1}
                    className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-40">
                    Next Question →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
