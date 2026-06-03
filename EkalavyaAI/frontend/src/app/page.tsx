"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, Brain, Shield, Globe, Target, Zap, Users } from "lucide-react";

export default function LandingPage() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div style={{ backgroundColor: "#0F0B1E" }}>
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b" style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <span className="text-xl font-bold" style={{ color: "#FBBF24" }}>EkalavyaAI</span>
          <div className="flex items-center gap-4">
            <Link href="/demo" className="text-sm transition-colors hover:text-orange-400" style={{ color: "#E5E7EB" }}>
              Try Demo
            </Link>
            <Link href="/auth/login" className="text-sm transition-colors hover:text-orange-400" style={{ color: "#E5E7EB" }}>
              Sign In
            </Link>
            <Link 
              href="/auth/signup" 
              className="text-sm px-4 py-2 rounded-lg font-semibold transition-colors hover:opacity-90"
              style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
            >
              Start Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 py-32 text-center">
        <div 
          className="inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full mb-6 border"
          style={{ backgroundColor: "rgba(79, 29, 149, 0.2)", borderColor: "#4C1D95", color: "#FBBF24" }}
        >
          🇮🇳 Built for India's CA, JEE & NEET students
        </div>
        <h1 className="text-6xl sm:text-7xl font-bold leading-tight mb-6" style={{ color: "#FFFFFF" }}>
          Learn Like a <span style={{ color: "#F97316" }}>Topper</span>
        </h1>
        <p className="text-xl mb-10 max-w-3xl mx-auto leading-relaxed" style={{ color: "#E5E7EB" }}>
          7 AI agents generate premium exam-quality notes in seconds. Powered by Claude 3.5 Sonnet — your personal CA/JEE/NEET teacher, available 24/7.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
          <Link 
            href="/auth/signup"
            className="px-8 py-4 rounded-xl font-semibold text-lg transition-all hover:shadow-lg hover:shadow-orange-500/20"
            style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
          >
            Start Learning Free →
          </Link>
          <Link
            href="/demo"
            className="px-8 py-4 rounded-xl font-semibold border-2 transition-colors hover:border-orange-400"
            style={{ borderColor: "#4C1D95", color: "#E5E7EB" }}
          >
            Try Demo
          </Link>
        </div>
        <p className="text-xs" style={{ color: "#9CA3AF" }}>No credit card required · Free plan forever</p>
      </section>

      {/* Exam Selector */}
      <section id="exams" className="max-w-6xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12" style={{ color: "#FFFFFF" }}>
          Choose Your Exam
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {[
            { icon: "📚", name: "CA Foundation", students: "45K" },
            { icon: "⚖️", name: "CA Intermediate", students: "32K" },
            { icon: "🏛️", name: "CA Final", students: "18K" },
            { icon: "🔬", name: "JEE", students: "78K" },
            { icon: "🧬", name: "NEET", students: "92K" },
          ].map((exam) => (
            <button
              key={exam.name}
              onClick={() => scrollToSection("features")}
              className="rounded-xl p-6 transition-all hover:scale-105 border-2 cursor-pointer"
              style={{ 
                backgroundColor: "rgba(255,255,255,0.05)",
                borderColor: "#4C1D95",
              }}
            >
              <div className="text-3xl mb-2">{exam.icon}</div>
              <p className="font-semibold text-sm" style={{ color: "#FFFFFF" }}>{exam.name}</p>
              <p className="text-xs mt-1" style={{ color: "#E5E7EB" }}>{exam.students} students</p>
            </button>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-16" style={{ color: "#FFFFFF" }}>
          How It Works in 3 Steps
        </h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {[
            {
              step: "1",
              title: "Choose Your Chapter",
              desc: "Search and select any chapter from your exam syllabus",
              icon: BookOpen,
            },
            {
              step: "2",
              title: "7 AI Agents Teach You",
              desc: "Claude, GPT-4, Gemini & others work together to create the perfect explanation",
              icon: Brain,
            },
            {
              step: "3",
              title: "Download Premium Notes",
              desc: "Get handwritten-style PDF with diagrams, tips, and PYQ alerts in seconds",
              icon: Zap,
            },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx}
                className="rounded-2xl p-8 border-2 relative"
                style={{ 
                  backgroundColor: "rgba(255,255,255,0.05)",
                  borderColor: "#4C1D95",
                }}
              >
                <div 
                  className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg mb-4"
                  style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
                >
                  {item.step}
                </div>
                <Icon size={32} style={{ color: "#F97316" }} className="mb-4" />
                <h3 className="text-xl font-bold mb-3" style={{ color: "#FFFFFF" }}>{item.title}</h3>
                <p style={{ color: "#E5E7EB" }}>{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12" style={{ color: "#FFFFFF" }}>
          Everything a Topper Needs
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon:"🤖", title:"7 AI Agents", desc:"Claude 3.5 Sonnet + GPT-4o + Gemini work in parallel to generate premium notes" },
            { icon:"📝", title:"Premium PDF Notes", desc:"Handwriting-style notes with exam tips, mnemonics, PYQ alerts and SVG diagrams" },
            { icon:"🎯", title:"PYQ Practice", desc:"10 years of verified past year questions with step-by-step AI solutions" },
            { icon:"🧠", title:"Student Memory", desc:"AI remembers your weak chapters and adapts every response to your level" },
            { icon:"🛡️", title:"Anti-Hallucination", desc:"5-layer verification ensures every fact is correct — critical for CA/JEE/NEET" },
            { icon:"🌍", title:"5 Languages", desc:"English, Bengali, Hindi, Tamil, Telugu — notes in your mother tongue" },
          ].map((f) => (
            <div 
              key={f.title}
              className="rounded-2xl p-6 border-2"
              style={{ 
                backgroundColor: "rgba(255,255,255,0.05)",
                borderColor: "#4C1D95",
              }}
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold mb-2" style={{ color: "#FFFFFF" }}>{f.title}</h3>
              <p className="text-sm" style={{ color: "#E5E7EB" }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Notes Preview */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12" style={{ color: "#FFFFFF" }}>
          See What Premium Notes Look Like
        </h2>
        <div 
          className="rounded-2xl p-8 border-2"
          style={{ 
            backgroundColor: "rgba(255,255,255,0.05)",
            borderColor: "#4C1D95",
          }}
        >
          {/* Note preview container */}
          <div 
            className="rounded-lg p-8"
            style={{ 
              backgroundImage: "repeating-linear-gradient(to bottom, transparent, transparent 31px, rgba(251, 191, 36, 0.1) 31px, rgba(251, 191, 36, 0.1) 32px)",
              backgroundColor: "rgba(255,255,255,0.02)",
            }}
          >
            <div className="text-right text-xs mb-6 opacity-50" style={{ color: "#FBBF24" }}>
              ✨ powered by EkalavyaAI
            </div>

            <h3 className="text-2xl font-bold mb-6" style={{ color: "#F97316" }}>
              Partnership Accounts - CA Foundation
            </h3>

            <p className="mb-4 leading-relaxed" style={{ color: "#E5E7EB", fontFamily: "var(--font-caveat)", fontSize: "18px" }}>
              A partnership is an agreement between two or more persons to carry on business with a view to profit.
            </p>

            <p className="mb-6 leading-relaxed" style={{ color: "#E5E7EB", fontFamily: "var(--font-caveat)", fontSize: "18px" }}>
              Key points: • Each partner contributes capital • Profits shared as per agreement
            </p>

            {/* Alert Box */}
            <div 
              className="rounded-lg p-4 mb-6 border-l-4"
              style={{ 
                backgroundColor: "rgba(251, 191, 36, 0.1)",
                borderColor: "#F97316",
              }}
            >
              <p className="font-bold text-sm mb-1" style={{ color: "#F97316" }}>⚠️ PYQ Alert</p>
              <p className="text-sm" style={{ color: "#E5E7EB" }}>Appeared in 2023, 2022, 2021 papers with 8 marks weight</p>
            </div>

            {/* Highlight example */}
            <div 
              className="rounded p-3 text-sm"
              style={{ 
                backgroundColor: "rgba(76, 29, 149, 0.3)",
                borderLeft: "4px solid #4C1D95",
                color: "#E5E7EB",
              }}
            >
              Important: Profit/Loss Account is common to all partners
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="max-w-6xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12" style={{ color: "#FFFFFF" }}>
          Loved by 1L+ Students
        </h2>
        <div className="grid sm:grid-cols-3 gap-6">
          {[
            { quote: "Scored 72% in CA Foundation with these notes!", student: "Priya K., CA Foundation", emoji: "⭐" },
            { quote: "PYQ solutions are insanely accurate. Saved my JEE prep!", student: "Arjun M., JEE 2024", emoji: "🔥" },
            { quote: "5 languages feature helped me prepare in Hindi. Game changer!", student: "Anaya P., NEET 2024", emoji: "💯" },
          ].map((testimonial, idx) => (
            <div
              key={idx}
              className="rounded-2xl p-6 border-2"
              style={{ 
                backgroundColor: "rgba(255,255,255,0.05)",
                borderColor: "#4C1D95",
              }}
            >
              <p className="text-2xl mb-4">{testimonial.emoji}</p>
              <p className="mb-4 italic" style={{ color: "#E5E7EB" }}>"{testimonial.quote}"</p>
              <p className="font-semibold text-sm" style={{ color: "#F97316" }}>{testimonial.student}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12" style={{ color: "#FFFFFF" }}>
          Plans Starting at ₹0
        </h2>
        <div className="grid sm:grid-cols-3 gap-6 mb-12">
          {[
            { plan:"Free", price:"₹0", planKey: "free", features:["3 chapters/month","5 PYQ/day","1 exam"], highlight: false },
            { plan:"Basic", price:"₹299/mo", planKey: "basic", features:["15 chapters/month","Unlimited PYQ","Notes download"], highlight: false },
            { plan:"Pro", price:"₹599/mo", planKey: "pro", features:["Unlimited everything","5 exams","5 languages","Weekly AI report"], highlight: true },
          ].map((p) => (
            <div 
              key={p.plan}
              className={`rounded-2xl p-6 border-2 card-interactive ${p.highlight ? "scale-105" : ""}`}
              style={{ 
                backgroundColor: p.highlight ? "rgba(249, 115, 22, 0.2)" : "rgba(255,255,255,0.05)",
                borderColor: p.highlight ? "#F97316" : "#4C1D95",
              }}
            >
              {p.highlight && (
                <div className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2" style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}>
                  Most Popular
                </div>
              )}
              <p className="font-bold text-lg mb-2" style={{ color: "#FFFFFF" }}>{p.plan}</p>
              <p className="text-3xl font-bold mb-6" style={{ color: "#F97316" }}>{p.price}</p>
              <ul className="space-y-2 mb-6">
                {p.features.map(f => (
                  <li key={f} className="text-sm" style={{ color: "#E5E7EB" }}>✓ {f}</li>
                ))}
              </ul>
              <Link
                href={`/auth/signup?plan=${p.planKey}`}
                className="block w-full py-2 rounded-lg font-semibold transition-all text-center"
                style={{ 
                  backgroundColor: p.highlight ? "#F97316" : "rgba(249, 115, 22, 0.2)",
                  color: p.highlight ? "#FFFFFF" : "#F97316",
                  border: p.highlight ? "none" : "1px solid rgba(249, 115, 22, 0.5)",
                }}
              >
                Get Started
              </Link>
            </div>
          ))}
        </div>
        <div className="text-center">
          <Link
            href="/auth/signup"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:shadow-lg hover:shadow-orange-500/20"
            style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
          >
            Start Learning Free <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-sm" style={{ borderColor: "rgba(255,255,255,0.1)", color: "#9CA3AF" }}>
        <p>© 2025 EkalavyaAI. All rights reserved. | Made with ❤️ for India's exam warriors.</p>
      </footer>
    </div>
  );
}
