"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/authStore";
import { authAPI } from "@/lib/api";

function SignupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({
    name: "", email: "", password: "",
    referral_code: searchParams.get("ref") || "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setError(""); setLoading(true);
    try {
      const res = await authAPI.signup(form);
      setAuth(res.data.user, res.data.access_token);
      setSuccess(true);
      setTimeout(() => {
        const plan = searchParams.get("plan");
        router.push(`/onboarding${plan ? `?plan=${plan}` : ""}`);
      }, 800);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || "Registration failed. Please try again.");
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
          {/* Animated student character */}
          <div className="flex justify-center mb-8">
            <div className="relative w-24 h-24" style={{ animation: success ? "none" : "float 3s ease-in-out infinite" }}>
              {/* Head */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full" style={{ backgroundColor: "#F4A460" }} />
              
              {/* Body */}
              <div className="absolute top-7 left-1/2 -translate-x-1/2 w-6 h-8" style={{ backgroundColor: "#4C1D95" }} />
              
              {/* Book */}
              <div className="absolute top-14 left-1/2 -translate-x-1/2 w-10 h-6 rounded" style={{ 
                backgroundColor: "#F97316",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "10px",
                fontWeight: "bold",
                color: "white",
              }}>
                EKA
              </div>
              
              {/* Wave hand - animated */}
              <div 
                className="absolute top-3 -right-2 w-4 h-4 rounded-full" 
                style={{ backgroundColor: "#F4A460", animation: success ? "none" : "wave 600ms ease-in-out infinite" }}
              />
              
              {/* Success checkmark */}
              {success && (
                <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-orange flex items-center justify-center animate-bounce-soft">
                  <span className="text-white text-lg">✓</span>
                </div>
              )}
            </div>
          </div>

          {/* Heading */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2 gradient-text">EkalavyaAI</h1>
            <p className="text-textBody text-sm">Join 100K+ exam toppers</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-orange/10 border border-orange/30 text-orange rounded-lg px-4 py-3 mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 mb-6">
            {[
              { key: "name", label: "Full Name", type: "text", placeholder: "Rahul Sharma" },
              { key: "email", label: "Email", type: "email", placeholder: "rahul@example.com" },
              { key: "password", label: "Password", type: "password", placeholder: "Min. 8 characters" },
              { key: "referral_code", label: "Referral Code (optional)", type: "text", placeholder: "EKA-XXX-XXXX" },
            ].map(({ key, label, type, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-textLight mb-2">{label}</label>
                <input 
                  type={type} 
                  value={(form as any)[key]} 
                  required={key !== "referral_code"}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="input-dark w-full transition-all"
                  placeholder={placeholder} 
                  style={{
                    backgroundColor: "#1E1535",
                    borderColor: "rgba(76, 29, 149, 0.3)",
                    color: "white",
                  }}
                />
              </div>
            ))}
            
            {/* Google Sign In */}
            <button
              type="button"
              className="w-full flex items-center justify-center gap-3 py-2.5 rounded-lg font-medium border-2 transition-all hover:bg-card-dark-hover"
              style={{ borderColor: "rgba(255,255,255,0.1)", color: "#E5E7EB" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
              </svg>
              Sign up with Google
            </button>

            {/* Submit button */}
            <button 
              type="submit" 
              disabled={loading}
              className="btn-orange w-full py-2.5 disabled:opacity-50 transition-all"
            >
              {loading ? "Creating account..." : "Create Free Account"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.1)" }} />
            <span className="text-xs text-textMuted">or</span>
            <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.1)" }} />
          </div>

          {/* Terms and Sign In */}
          <p className="text-center text-xs text-textMuted mb-4">
            By signing up, you agree to our Terms of Service
          </p>
          <p className="text-center text-sm" style={{ color: "#E5E7EB" }}>
            Already have an account?{" "}
            <Link href="/auth/login" className="font-semibold transition-colors hover:text-orange" style={{ color: "#F97316" }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "#0F0B1E" }}>
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-orange border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p style={{ color: "#E5E7EB" }}>Loading...</p>
        </div>
      </div>
    }>
      <SignupContent />
    </Suspense>
  );
}
