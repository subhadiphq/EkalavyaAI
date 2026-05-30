"use client";
interface Props { score: number; exam: string; }
export function ReadinessGauge({ score, exam }: Props) {
  const color = score >= 70 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";
  const circumference = 2 * Math.PI * 45;
  const dash = (score / 100) * circumference;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 text-center">
      <h3 className="text-sm font-semibold text-slate-600 mb-3">Exam Readiness</h3>
      <div className="relative inline-flex items-center justify-center">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="45" fill="none" stroke="#f1f5f9" strokeWidth="10" />
          <circle cx="60" cy="60" r="45" fill="none" stroke={color} strokeWidth="10"
            strokeDasharray={`${dash} ${circumference}`} strokeDashoffset={circumference / 4}
            strokeLinecap="round" transform="rotate(-90 60 60)" />
        </svg>
        <div className="absolute text-center">
          <div className="text-2xl font-bold" style={{ color }}>{Math.round(score)}%</div>
        </div>
      </div>
      <p className="text-xs text-slate-500 mt-2">{exam.replace("_", " ")}</p>
    </div>
  );
}
