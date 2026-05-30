"use client";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/authStore";

const PLANS = [
  { id:"FREE", label:"Free", price:0, annual:0, color:"slate", features:["10 general chats/day","3 chapter notes/month","5 PYQ questions/day","1 exam","English only"], notIncluded:["Notes download","DOCX export","Memory system","Multi-language","Weekly AI report"] },
  { id:"BASIC", label:"Basic", price:299, annual:2499, color:"blue", popular:false, features:["Unlimited chat","15 chapter notes/month","Unlimited PYQ","Notes PDF download (10/month)","1 exam","English + 1 Indian language"], notIncluded:["Unlimited notes","DOCX export","5 exams","Weekly AI report"] },
  { id:"PRO", label:"Pro", price:599, annual:4999, color:"purple", popular:true, features:["Everything in Basic","Unlimited notes generation","DOCX + PDF download","5 exams (CA + JEE + NEET)","All 5 languages","Full memory system","Weekly AI study report","Exam readiness score","Spaced repetition schedule"], notIncluded:[] },
  { id:"INSTITUTE", label:"Institute", price:4999, annual:44999, color:"amber", features:["Everything in Pro","30 student accounts","Teacher dashboard","Batch analytics","Priority support","Custom branding"], notIncluded:[] },
];

export default function PricingPage() {
  const { isAuthenticated } = useAuthStore();
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-100">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/" className="font-bold text-blue-700 text-lg">EkalavyaAI</Link>
          <Link href={isAuthenticated ? "/dashboard" : "/auth/login"} className="text-sm text-slate-600 hover:text-blue-600">
            {isAuthenticated ? "Dashboard →" : "Sign In"}
          </Link>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-3">Simple, Transparent Pricing</h1>
          <p className="text-slate-500 text-lg">Start free. Upgrade when you need more.</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {PLANS.map((plan) => (
            <div key={plan.id} className={`bg-white rounded-2xl border-2 p-6 flex flex-col ${plan.popular ? "border-purple-500 shadow-lg shadow-purple-100 relative" : "border-slate-200"}`}>
              {plan.popular && <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full">MOST POPULAR</div>}
              <div className={`font-bold text-lg mb-1 text-${plan.color}-600`}>{plan.label}</div>
              <div className="text-3xl font-bold text-slate-900 mb-0.5">
                {plan.price === 0 ? "Free" : `₹${plan.price}`}
                {plan.price > 0 && <span className="text-sm font-normal text-slate-400">/mo</span>}
              </div>
              {plan.annual > 0 && <p className="text-xs text-green-600 mb-4">₹{plan.annual}/year (save 30%)</p>}
              <div className="border-t border-slate-100 my-4" />
              <ul className="space-y-2 mb-6 flex-1">
                {plan.features.map(f => <li key={f} className="text-sm text-slate-700 flex gap-2"><span className="text-green-500 shrink-0">✓</span>{f}</li>)}
                {plan.notIncluded.map(f => <li key={f} className="text-sm text-slate-300 flex gap-2 line-through"><span className="shrink-0">✗</span>{f}</li>)}
              </ul>
              <Link href={plan.price === 0 ? "/auth/signup" : `/auth/signup?plan=${plan.id}`}
                className={`block text-center py-2.5 rounded-xl font-medium text-sm transition-colors ${plan.popular ? "bg-purple-600 text-white hover:bg-purple-700" : "border border-slate-200 hover:bg-slate-50 text-slate-700"}`}>
                {plan.price === 0 ? "Start Free" : `Get ${plan.label}`}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-12 bg-white rounded-2xl border border-slate-200 p-6 text-center">
          <h3 className="font-semibold text-slate-800 mb-2">💳 Earn Free Credits</h3>
          <p className="text-slate-500 text-sm mb-4">Refer friends, maintain study streaks, rate notes — earn credits to redeem Pro features for free</p>
          <div className="grid sm:grid-cols-4 gap-4 text-sm">
            {[["👥 Refer a Friend","200 credits"],["🔥 7-Day Streak","50 credits"],["⭐ Rate Notes","10 credits"],["🏆 Complete Profile","30 credits"]].map(([action, credits]) => (
              <div key={action} className="bg-slate-50 rounded-xl p-3">
                <div className="font-medium text-slate-700">{action}</div>
                <div className="text-blue-600 font-bold mt-1">{credits}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
