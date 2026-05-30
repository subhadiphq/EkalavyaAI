"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { studentAPI } from "@/lib/api";

const STEPS = ["Choose Exam", "Your Level", "Exam Date", "Language", "Study Style"];

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({
    exam_targets: [] as string[],
    level: "AVERAGE",
    exam_dates: {} as Record<string, string>,
    language: "English",
    study_hours_per_day: 4,
    learning_style: "visual",
    weak_subjects: [] as string[],
  });

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const handleFinish = async () => {
    setLoading(true);
    try {
      await studentAPI.completeOnboarding(data);
      router.push("/dashboard");
    } catch { setLoading(false); }
  };

  const examOptions = ["CA_FOUNDATION", "CA_INTERMEDIATE", "CA_FINAL", "JEE", "NEET"];
  const levelOptions = [
    { value: "WEAK", label: "🌱 Beginner", desc: "I need extra help and examples" },
    { value: "AVERAGE", label: "📚 Average", desc: "I know basics but need practice" },
    { value: "TOPPER", label: "🏆 Advanced", desc: "I'm strong but want to perfect" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-lg p-8">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between text-xs text-slate-400 mb-2">
            <span>Step {step + 1} of {STEPS.length}</span>
            <span>{STEPS[step]}</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full">
            <div className="h-2 bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
          </div>
        </div>

        <h2 className="text-xl font-bold text-slate-800 mb-2">
          {step === 0 && `Welcome, ${user?.name?.split(" ")[0]}! 👋`}
          {step === 1 && "What's your current level?"}
          {step === 2 && "When is your exam?"}
          {step === 3 && "Preferred language?"}
          {step === 4 && "How do you study?"}
        </h2>
        <p className="text-slate-500 text-sm mb-6">
          {step === 0 && "Which exam are you preparing for?"}
          {step === 1 && "We'll adapt our teaching style to match you."}
          {step === 2 && "We'll create your personalized study plan."}
          {step === 3 && "Notes will be generated in your language."}
          {step === 4 && "Helps us personalise your experience."}
        </p>

        {/* Step Content */}
        {step === 0 && (
          <div className="grid grid-cols-2 gap-3">
            {examOptions.map((exam) => (
              <button key={exam} onClick={() => setData({ ...data, exam_targets: data.exam_targets.includes(exam) ? data.exam_targets.filter(e => e !== exam) : [...data.exam_targets, exam] })}
                className={`p-3 rounded-xl border-2 text-sm font-medium transition-all ${data.exam_targets.includes(exam) ? "border-blue-600 bg-blue-50 text-blue-700" : "border-slate-200 hover:border-blue-200"}`}>
                {exam.replace("_", " ")}
              </button>
            ))}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-3">
            {levelOptions.map((opt) => (
              <button key={opt.value} onClick={() => setData({ ...data, level: opt.value })}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all ${data.level === opt.value ? "border-blue-600 bg-blue-50" : "border-slate-200 hover:border-blue-200"}`}>
                <div className="font-medium text-slate-800">{opt.label}</div>
                <div className="text-sm text-slate-500 mt-0.5">{opt.desc}</div>
              </button>
            ))}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            {data.exam_targets.map((exam) => (
              <div key={exam}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{exam.replace("_", " ")} Exam Date</label>
                <input type="date" value={data.exam_dates[exam] || ""}
                  onChange={(e) => setData({ ...data, exam_dates: { ...data.exam_dates, [exam]: e.target.value } })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            ))}
          </div>
        )}

        {step === 3 && (
          <div className="grid grid-cols-2 gap-3">
            {["English", "Bengali", "Hindi", "Tamil", "Telugu"].map((lang) => (
              <button key={lang} onClick={() => setData({ ...data, language: lang })}
                className={`p-3 rounded-xl border-2 text-sm font-medium transition-all ${data.language === lang ? "border-blue-600 bg-blue-50 text-blue-700" : "border-slate-200 hover:border-blue-200"}`}>
                {lang}
              </button>
            ))}
          </div>
        )}

        {step === 4 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Hours available per day</label>
              <input type="range" min={1} max={12} value={data.study_hours_per_day}
                onChange={(e) => setData({ ...data, study_hours_per_day: Number(e.target.value) })}
                className="w-full accent-blue-600" />
              <div className="text-center text-blue-700 font-bold mt-1">{data.study_hours_per_day} hours/day</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Learning style</label>
              <div className="grid grid-cols-3 gap-2">
                {[{ v: "visual", l: "👁 Visual" }, { v: "reading", l: "📖 Reading" }, { v: "practice", l: "✏️ Practice" }].map(({ v, l }) => (
                  <button key={v} onClick={() => setData({ ...data, learning_style: v })}
                    className={`p-3 rounded-xl border-2 text-sm font-medium transition-all ${data.learning_style === v ? "border-blue-600 bg-blue-50 text-blue-700" : "border-slate-200 hover:border-blue-200"}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button onClick={back} className="flex-1 border border-slate-200 rounded-xl py-2.5 text-sm font-medium hover:bg-slate-50">
              ← Back
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button onClick={next} disabled={step === 0 && data.exam_targets.length === 0}
              className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-40">
              Next →
            </button>
          ) : (
            <button onClick={handleFinish} disabled={loading}
              className="flex-1 bg-green-600 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-green-700 disabled:opacity-40">
              {loading ? "Setting up..." : "Start Learning! 🚀"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
