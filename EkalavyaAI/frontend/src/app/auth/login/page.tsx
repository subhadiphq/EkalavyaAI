"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/authStore";
import { authAPI } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const res = await authAPI.login(form);
      setAuth(res.data.user, res.data.access_token);
      router.push(res.data.user.onboarding_complete ? "/dashboard" : "/onboarding");
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || "Login failed. Please try again.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden particles-bg" style={{ backgroundColor: "#0F0B1E" }}>
      {/* Gradient overlay */}
      <div className="absolute inset-0" style={{
        background: "radial-gradient(ellipse at 20% 50%, rgba(76, 29, 149, 0.15) 0%, transparent 50%)",
      }} />
      
      {/* Content */}
      <div className="relative z-10 w-full max-w-md animate-slide-in-right">
        {/* Glass card */}
        <div className="glass-card p-8 border-2" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2 gradient-text">EkalavyaAI</h1>
            <p className="text-textBody text-sm">Learn Like a Topper</p>
          </div>

          {/* Heading */}
          <h2 className="text-xl font-semibold text-textLight mb-6">Welcome Back</h2>

          {/* Error message */}
          {error && (
            <div className="bg-orange/10 border border-orange/30 text-orange rounded-lg px-4 py-3 mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-textLight mb-2">Email</label>
              <input 
                type="email" 
                required 
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="input-dark w-full transition-all"
                placeholder="you@example.com"
                style={{
                  backgroundColor: "#1E1535",
                  borderColor: "rgba(76, 29, 149, 0.3)",
                  color: "white",
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-textLight mb-2">Password</label>
              <input 
                type="password" 
                required 
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="input-dark w-full transition-all"
                placeholder="••••••••"
                style={{
                  backgroundColor: "#1E1535",
                  borderColor: "rgba(76, 29, 149, 0.3)",
                  color: "white",
                }}
              />
            </div>
            
            {/* Submit button */}
            <button 
              type="submit" 
              disabled={loading}
              className="btn-orange w-full py-2.5 disabled:opacity-50 transition-all"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.1)" }} />
            <span className="text-xs text-textMuted">or</span>
            <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.1)" }} />
          </div>

          {/* Google Sign In */}
          <button
            type="button"
            className="w-full flex items-center justify-center gap-3 py-2.5 rounded-lg font-medium border-2 transition-all hover:bg-card-dark-hover mb-6"
            style={{ borderColor: "rgba(255,255,255,0.1)", color: "#E5E7EB" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
            </svg>
            Sign in with Google
          </button>

          {/* Sign up link */}
          <p className="text-center text-sm" style={{ color: "#E5E7EB" }}>
            Don't have an account?{" "}
            <Link href="/auth/signup" className="font-semibold transition-colors hover:text-orange" style={{ color: "#F97316" }}>
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
