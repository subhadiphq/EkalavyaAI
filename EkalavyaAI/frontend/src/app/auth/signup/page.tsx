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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setError(""); setLoading(true);
    try {
      const res = await authAPI.signup(form);
      setAuth(res.data.user, res.data.access_token);
      const plan = searchParams.get("plan");
      router.push(`/onboarding${plan ? `?plan=${plan}` : ""}`);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || "Registration failed. Please try again.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-700">EkalavyaAI</h1>
          <p className="text-slate-500 mt-1 text-sm">Join 10,000+ exam toppers</p>
        </div>
        <h2 className="text-xl font-semibold text-slate-800 mb-6">Create Free Account</h2>
        {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { key: "name", label: "Full Name", type: "text", placeholder: "Rahul Sharma" },
            { key: "email", label: "Email", type: "email", placeholder: "rahul@example.com" },
            { key: "password", label: "Password", type: "password", placeholder: "Min. 8 characters" },
            { key: "referral_code", label: "Referral Code (optional)", type: "text", placeholder: "EKA-XXX-XXXX" },
          ].map(({ key, label, type, placeholder }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              <input type={type} value={(form as any)[key]} required={key !== "referral_code"}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={placeholder} />
            </div>
          ))}
          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg py-2.5 font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {loading ? "Creating account..." : "Create Free Account"}
          </button>
        </form>
        <p className="text-center text-xs text-slate-400 mt-4">
          By signing up you agree to our Terms of Service
        </p>
        <p className="text-center text-sm text-slate-500 mt-3">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-blue-600 font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    }>
      <SignupContent />
    </Suspense>
  );
}
