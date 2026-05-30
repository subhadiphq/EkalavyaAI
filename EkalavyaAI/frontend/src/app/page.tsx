import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-slate-100 sticky top-0 bg-white/90 backdrop-blur z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-blue-700">EkalavyaAI</span>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm text-slate-600 hover:text-blue-600">Sign In</Link>
            <Link href="/auth/signup" className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              Start Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-4 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-medium px-3 py-1.5 rounded-full mb-6">
          🇮🇳 Built for India's CA, JEE & NEET students
        </div>
        <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 leading-tight mb-6">
          Learn Like a <span className="text-blue-600">Topper</span>
        </h1>
        <p className="text-xl text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
          7 AI agents generate premium exam-quality notes in seconds.
          Powered by Claude 3.5 Sonnet — your personal CA/JEE/NEET teacher, available 24/7.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/auth/signup"
            className="bg-blue-600 text-white px-8 py-3.5 rounded-xl font-semibold text-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
            Start Learning Free →
          </Link>
          <Link href="/auth/login"
            className="border border-slate-200 px-8 py-3.5 rounded-xl font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            Sign In
          </Link>
        </div>
        <p className="text-xs text-slate-400 mt-4">No credit card required · Free plan forever</p>
      </section>

      {/* Features */}
      <section className="bg-slate-50 py-20">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-slate-800 mb-12">Everything a Topper Needs</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon:"🤖", title:"7 AI Agents", desc:"Claude 3.5 Sonnet + GPT-4o + Gemini work in parallel to generate premium notes" },
              { icon:"📝", title:"Premium PDF Notes", desc:"Handwriting-style notes with exam tips, mnemonics, PYQ alerts and SVG diagrams" },
              { icon:"🎯", title:"PYQ Practice", desc:"10 years of verified past year questions with step-by-step AI solutions" },
              { icon:"🧠", title:"Student Memory", desc:"AI remembers your weak chapters and adapts every response to your level" },
              { icon:"🛡️", title:"Anti-Hallucination", desc:"5-layer verification ensures every fact is correct — critical for CA/JEE/NEET" },
              { icon:"🌍", title:"5 Languages", desc:"English, Bengali, Hindi, Tamil, Telugu — notes in your mother tongue" },
            ].map((f) => (
              <div key={f.title} className="bg-white rounded-2xl p-6 border border-slate-200">
                <div className="text-3xl mb-3">{f.icon}</div>
                <h3 className="font-semibold text-slate-800 mb-1">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing teaser */}
      <section className="py-20 max-w-3xl mx-auto px-4 text-center">
        <h2 className="text-3xl font-bold text-slate-800 mb-4">Plans Starting at ₹0</h2>
        <p className="text-slate-500 mb-8">Free plan includes 3 chapter notes/month + 5 PYQ questions/day</p>
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          {[
            { plan:"Free", price:"₹0", features:["3 chapters/month","5 PYQ/day","1 exam"] },
            { plan:"Basic", price:"₹299/mo", features:["15 chapters/month","Unlimited PYQ","Notes download"], highlight:false },
            { plan:"Pro", price:"₹599/mo", features:["Unlimited everything","5 exams","5 languages","Weekly AI report"], highlight:true },
          ].map((p) => (
            <div key={p.plan} className={`rounded-2xl p-5 border-2 ${p.highlight ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white"}`}>
              <div className="font-bold text-slate-800 text-lg">{p.plan}</div>
              <div className={`text-2xl font-bold mt-1 mb-4 ${p.highlight ? "text-blue-700" : "text-slate-700"}`}>{p.price}</div>
              <ul className="space-y-1.5 text-sm text-slate-600">
                {p.features.map(f => <li key={f}>✓ {f}</li>)}
              </ul>
            </div>
          ))}
        </div>
        <Link href="/auth/signup" className="bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors">
          Get Started Free
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 py-8 text-center text-sm text-slate-400">
        <p>© 2025 EkalavyaAI. All rights reserved. | Made with ❤️ for India's exam warriors.</p>
      </footer>
    </div>
  );
}
