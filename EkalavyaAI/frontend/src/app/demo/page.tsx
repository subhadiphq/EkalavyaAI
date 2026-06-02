"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useState } from "react";

export default function DemoPage() {
  const [blurred, setBlurred] = useState(true);

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0F0B1E" }}>
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b" style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold" style={{ color: "#FBBF24" }}>
            EkalavyaAI
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm transition-colors hover:text-blue-400" style={{ color: "#E5E7EB" }}>
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

      {/* Demo Content */}
      <section className="max-w-4xl mx-auto px-4 py-16">
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4" style={{ color: "#FFFFFF" }}>
            Partnership Accounts Explained
          </h1>
          <p className="text-sm mb-8" style={{ color: "#FBBF24" }}>
            🔓 Free Preview • CA Foundation
          </p>
        </div>

        {/* Sample Note Content */}
        <div 
          className="rounded-2xl p-8 border-2 backdrop-blur-sm"
          style={{ 
            backgroundColor: "rgba(255,255,255,0.05)",
            borderColor: "#4C1D95",
          }}
        >
          {/* Paragraph 1 */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-4" style={{ color: "#F97316" }}>
              What is a Partnership Account?
            </h2>
            <p className="leading-relaxed mb-4" style={{ color: "#E5E7EB" }}>
              A partnership account is a financial record that tracks all transactions related to a partnership firm. It includes capital contributions, profit/loss distribution, and withdrawal records for each partner. This account serves as the primary record of each partner's financial stake in the partnership.
            </p>
            <p className="leading-relaxed" style={{ color: "#E5E7EB" }}>
              The partnership account reflects the changing nature of the partnership over time. When partners join or leave, their accounts are adjusted accordingly. Understanding partnership accounts is crucial for CA Foundation students as it forms the basis for more advanced partnership accounting concepts.
            </p>
          </div>

          {/* Paragraph 2 */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4" style={{ color: "#F97316" }}>
              Types of Partnership Accounts
            </h2>
            <p className="leading-relaxed" style={{ color: "#E5E7EB" }}>
              Partnership accounts can be broadly classified into two categories: capital accounts and current accounts. Capital accounts maintain a permanent record of each partner's original investment and any additional capital contributions.
            </p>
          </div>

          {/* Blur Effect for remaining content */}
          {blurred && (
            <div 
              className="rounded-lg p-6 backdrop-blur-sm"
              style={{ backgroundColor: "rgba(15, 11, 30, 0.8)" }}
            >
              <div className="space-y-4 blur-sm select-none pointer-events-none">
                <h2 className="text-2xl font-bold" style={{ color: "#F97316" }}>
                  How to Prepare Partnership Accounts
                </h2>
                <p style={{ color: "#E5E7EB" }}>
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                </p>
                <p style={{ color: "#E5E7EB" }}>
                  Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                </p>
              </div>
              
              {/* Unlock CTA */}
              <div className="text-center mt-8 relative z-10">
                <p className="text-sm font-semibold mb-4" style={{ color: "#FBBF24" }}>
                  📖 Want to see the complete notes?
                </p>
                <Link
                  href="/auth/signup"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all hover:shadow-lg"
                  style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
                >
                  Sign Up Free to Read Full Notes <ArrowRight size={18} />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Key Insights Box */}
        <div 
          className="rounded-xl p-6 mt-8 border-l-4"
          style={{ 
            backgroundColor: "rgba(79, 172, 254, 0.1)",
            borderColor: "#F97316",
          }}
        >
          <p className="font-semibold mb-2" style={{ color: "#F97316" }}>
            💡 Key Insight
          </p>
          <p style={{ color: "#E5E7EB" }}>
            Partnership accounts are essential for understanding how profits and losses are distributed among partners. This concept directly appears in CA Foundation papers with 5-8 marks weightage.
          </p>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <h3 className="text-2xl font-bold mb-4" style={{ color: "#FFFFFF" }}>
            This is just a preview
          </h3>
          <p className="mb-6" style={{ color: "#E5E7EB" }}>
            Get access to 100+ chapters with premium AI-generated notes, handwritten-style PDFs, and PYQ solutions.
          </p>
          <Link
            href="/auth/signup"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:shadow-lg hover:shadow-orange-500/20"
            style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
          >
            Start Learning Free <ArrowRight size={20} />
          </Link>
          <p className="text-xs mt-4" style={{ color: "#9CA3AF" }}>
            No credit card required • 3 chapters free per month
          </p>
        </div>
      </section>
    </div>
  );
}
