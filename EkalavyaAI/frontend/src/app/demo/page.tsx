"use client";

import Link from "next/link";
import { ArrowRight, Send, MessageCircle } from "lucide-react";
import { useState, useEffect } from "react";

export default function DemoPage() {
  const [blurred, setBlurred] = useState(false);
  const [messages, setMessages] = useState<any[]>([
    {
      role: "assistant",
      content: "Partnership Accounts are a fundamental concept in CA Foundation accounting. Let me explain this with a practical example.\n\nA partnership is an association of two or more persons who agree to share profits/losses. For accounting purposes, each partner maintains an account which shows:\n\n1. **Capital Account** - Records permanent capital contributions\n2. **Current Account** - Shows day-to-day transactions like profit share and drawings\n\nFor example, if Rahul and Priya start a partnership with ₹1,00,000 each, their Capital Accounts would show ₹1,00,000 each. If they make profits of ₹50,000 in the first year, this goes to their Current Accounts based on their profit-sharing ratio.",
      typing: false,
    }
  ]);
  const [messageCount, setMessageCount] = useState(1);

  useEffect(() => {
    // Simulate user asking question after 3 seconds
    const timer = setTimeout(() => {
      if (messageCount === 1) {
        setMessages(prev => [...prev, {
          role: "user",
          content: "Can you explain the difference between Capital Account and Current Account?"
        }]);
        setMessageCount(2);
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [messageCount]);

  useEffect(() => {
    // Simulate AI response after user message
    if (messageCount === 2) {
      const timer = setTimeout(() => {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: "Great question! Here are the key differences:\n\n**Capital Account:**\n• Shows permanent/fixed amount\n• Changed only by additional capital or withdrawal of capital\n• Maintains constant balance (if no withdrawals)\n• Shows the long-term investment\n\n**Current Account:**\n• Shows variable balance\n• Affected by profit/loss share and drawings\n• Changes every accounting period\n• Shows short-term transactions\n\n**Practical Example:**\nAmar and Bhuvan each contribute ₹2,00,000 (Capital Account = ₹2,00,000 each)\n\nAfter 1 year:\n• Profit = ₹1,20,000 (equal share = ₹60,000 each)\n• Amar withdraws ₹40,000 (drawings)\n\nCurrent Account:\n• Amar: ₹60,000 - ₹40,000 = ₹20,000 (Credit)\n• Bhuvan: ₹60,000 - 0 = ₹60,000 (Credit)\n\nThe Capital Account remains ₹2,00,000 for both.",
          typing: false,
        }]);
        setMessageCount(3);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [messageCount]);

  useEffect(() => {
    // Blur after 3 messages
    if (messageCount === 3) {
      const timer = setTimeout(() => {
        setBlurred(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [messageCount]);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#0F0B1E" }}>
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b" style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold gradient-text">
            EkalavyaAI
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm transition-colors hover:text-orange" style={{ color: "#E5E7EB" }}>
              Sign In
            </Link>
            <Link 
              href="/auth/signup" 
              className="text-sm px-4 py-2 rounded-lg font-semibold transition-all hover:shadow-orange-glow"
              style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
            >
              Start Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Demo Content */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <MessageCircle size={28} style={{ color: "#F97316" }} />
            <h1 className="text-4xl font-bold" style={{ color: "#FFFFFF" }}>
              Experience AI Learning
            </h1>
          </div>
          <p className="text-sm mb-2" style={{ color: "#F97316" }}>
            🔓 Free Preview • Partnership Accounts
          </p>
          <p className="text-sm" style={{ color: "#E5E7EB" }}>
            Watch how EkalavyaAI teaches complex accounting concepts in simple terms
          </p>
        </div>

        {/* Chat Demo */}
        <div 
          className="flex-1 rounded-2xl p-6 border-2 backdrop-blur-sm mb-8 flex flex-col"
          style={{ 
            backgroundColor: "rgba(255,255,255,0.03)",
            borderColor: "rgba(249, 115, 22, 0.3)",
          }}
        >
          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto mb-6">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`} style={{ animation: "fade-in 300ms ease-out" }}>
                <div
                  className={`max-w-lg rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "rounded-br-none"
                      : "rounded-bl-none glass-card"
                  }`}
                  style={{
                    backgroundColor: msg.role === "user" ? "#F97316" : "rgba(255,255,255,0.05)",
                    color: msg.role === "user" ? "white" : "#E5E7EB",
                  }}
                >
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#F97316" }} />
                      <div className="text-xs font-semibold" style={{ color: "#F97316" }}>
                        EkalavyaAI Teacher
                      </div>
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Blur overlay after 3 messages */}
          {blurred && (
            <div 
              className="absolute inset-6 rounded-2xl backdrop-blur-md flex items-center justify-center flex-col gap-6 z-10"
              style={{ backgroundColor: "rgba(15, 11, 30, 0.7)" }}
            >
              <div className="text-center">
                <div className="text-4xl mb-4">🔒</div>
                <p className="text-lg font-semibold text-textLight mb-2">
                  This is just the beginning
                </p>
                <p className="text-sm text-textMuted mb-6 max-w-md">
                  With EkalavyaAI, you get unlimited questions, personalized explanations, and exam-focused solutions.
                </p>
                <Link
                  href="/auth/signup"
                  className="inline-flex items-center gap-2 px-8 py-3 rounded-lg font-semibold transition-all hover:shadow-orange-glow"
                  style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
                >
                  Unlock Full Access <ArrowRight size={18} />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Input Area (disabled) */}
        <div className="flex gap-3 mb-8">
          <input
            type="text"
            placeholder="Ask your question..."
            disabled
            className="input-dark flex-1 disabled:opacity-50"
            style={{
              backgroundColor: "#1E1535",
              borderColor: "rgba(76, 29, 149, 0.3)",
            }}
          />
          <button
            disabled
            className="btn-orange px-6 disabled:opacity-50"
          >
            <Send size={18} />
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { emoji: "⚡", title: "Instant Answers", desc: "Get exam-quality explanations in seconds" },
            { emoji: "📚", title: "100+ Chapters", desc: "Complete syllabus coverage with examples" },
            { emoji: "📊", title: "PYQ Solutions", desc: "Past year questions solved with clarity" },
          ].map((feat) => (
            <div
              key={feat.title}
              className="rounded-xl p-4 text-center card-interactive"
              style={{
                backgroundColor: "rgba(255,255,255,0.05)",
                borderLeft: "3px solid #F97316",
              }}
            >
              <div className="text-3xl mb-2">{feat.emoji}</div>
              <h4 className="font-semibold text-sm text-textLight mb-1">{feat.title}</h4>
              <p className="text-xs text-textMuted">{feat.desc}</p>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="text-center mt-12 mb-8">
          <h3 className="text-2xl font-bold mb-4" style={{ color: "#FFFFFF" }}>
            Ready to ace your exams?
          </h3>
          <p className="mb-6 text-textBody">
            Join 100,000+ students already learning with EkalavyaAI
          </p>
          <Link
            href="/auth/signup?ref=demo"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:shadow-orange-glow card-interactive"
            style={{ backgroundColor: "#F97316", color: "#FFFFFF" }}
          >
            Start Free Trial <ArrowRight size={20} />
          </Link>
          <p className="text-xs mt-4" style={{ color: "#9CA3AF" }}>
            No credit card required • 3 chapters free per month • Cancel anytime
          </p>
        </div>
      </div>
    </div>
  );
}
