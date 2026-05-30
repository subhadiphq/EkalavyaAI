"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { streamSSE } from "@/lib/api";
import { Send, MessageCircle } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; streaming?: boolean; }

function ChatContent() {
  const { token } = useAuthStore();
  const searchParams = useSearchParams();
  const [exam, setExam] = useState(searchParams.get("exam") || "CA_FOUNDATION");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(searchParams.get("q") || "");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  // Auto-submit if query param is present
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && messages.length === 0) { setTimeout(() => handleSend(q), 300); }
  }, []);

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setStreaming(true);

    let assistantContent = "";
    setMessages(prev => [...prev, { role: "assistant", content: "", streaming: true }]);

    try {
      for await (const chunk of streamSSE("/chat/message", { message: msg, exam }, token || "")) {
        if (chunk.type === "chunk" && chunk.content) {
          assistantContent += chunk.content;
          setMessages(prev => prev.map((m, i) => i === prev.length - 1 ? { ...m, content: assistantContent } : m));
        } else if (chunk.type === "complete") {
          setMessages(prev => prev.map((m, i) => i === prev.length - 1 ? { ...m, streaming: false } : m));
        }
      }
    } catch {
      setMessages(prev => prev.map((m, i) => i === prev.length - 1 ? { ...m, content: "Sorry, something went wrong. Please try again.", streaming: false } : m));
    } finally { setStreaming(false); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 py-6 space-y-4 overflow-y-auto">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">💬</div>
            <h2 className="text-xl font-semibold text-slate-700 mb-2">Ask Any Doubt</h2>
            <p className="text-slate-400 text-sm">Powered by Claude 3.5 Sonnet — exam-quality answers</p>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto">
              {["Explain Partnership Goodwill methods","What is AS 9? Revenue recognition","Solve: NPV of ₹10,000 at 10% for 3 years","Difference between AS and Ind AS"].map(q => (
                <button key={q} onClick={() => handleSend(q)}
                  className="text-left p-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-600 hover:border-blue-300 hover:bg-blue-50 transition-colors">
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === "user" ? "bg-blue-600 text-white rounded-br-md" : "bg-white border border-slate-200 text-slate-700 rounded-bl-md"}`}>
              {msg.role === "assistant" && <div className="text-xs font-medium text-blue-600 mb-1">EkalavyaAI Teacher</div>}
              <div className="whitespace-pre-wrap">{msg.content}</div>
              {msg.streaming && <div className="inline-block w-1.5 h-4 bg-blue-400 animate-pulse ml-0.5 rounded-sm" />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="sticky bottom-0 bg-white border-t border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-3 flex gap-3">
          <textarea value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Type your doubt here... (Enter to send, Shift+Enter for newline)"
            rows={1} className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            style={{ maxHeight: "120px" }} />
          <button onClick={() => handleSend()} disabled={streaming || !input.trim()}
            className="bg-blue-600 text-white px-4 rounded-xl hover:bg-blue-700 disabled:opacity-40 transition-colors">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" /></div>}><ChatContent /></Suspense>;
}
