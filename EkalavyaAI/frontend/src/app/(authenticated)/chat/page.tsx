"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { streamSSE } from "@/lib/api";
import { Send, MessageCircle, Download, Save, Volume2, ChevronDown, Zap, Menu, X } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; streaming?: boolean; }

function ChatContent() {
  const { token } = useAuthStore();
  const searchParams = useSearchParams();
  const [exam, setExam] = useState(searchParams.get("exam") || "CA_FOUNDATION");
  const [language, setLanguage] = useState("EN");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(searchParams.get("q") || "");
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
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
      for await (const chunk of streamSSE("/chat/message", { message: msg, exam, language }, token || "")) {
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

  const downloadPDF = (messageIndex: number) => {
    const message = messages[messageIndex];
    if (!message) return;
    // Simple text download - in production would generate PDF
    const element = document.createElement("a");
    const file = new Blob([message.content], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `ekalavya-response-${new Date().getTime()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="h-screen flex" style={{ backgroundColor: "#0F0B1E" }}>
      {/* Sidebar - Syllabus */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform md:static md:transform-none ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        } border-r overflow-y-auto`}
        style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold gradient-text">Syllabus</h3>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden text-textLight hover:text-orange"
            >
              <X size={20} />
            </button>
          </div>

          <div className="space-y-3">
            {[
              { title: "Partnership Accounts", count: 8 },
              { title: "Goodwill Valuation", count: 5 },
              { title: "Admission & Retirement", count: 6 },
              { title: "Branch Accounting", count: 4 },
              { title: "Amalgamation", count: 7 },
              { title: "As. and Ind. As.", count: 10 },
            ].map((chapter) => (
              <button
                key={chapter.title}
                className="w-full text-left p-3 rounded-lg transition-all hover:bg-card-dark-hover"
                style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
              >
                <div className="font-medium text-sm text-textLight">{chapter.title}</div>
                <div className="text-xs text-textMuted mt-1">{chapter.count} topics</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div
          className="h-16 border-b flex items-center justify-between px-6"
          style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden text-textLight hover:text-orange"
            >
              <Menu size={24} />
            </button>
            <h2 className="text-textLight font-caveat text-2xl">EkalavyaAI Teacher</h2>
          </div>

          <div className="flex items-center gap-4">
            {/* Language selector */}
            <div className="relative group">
              <button
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-textBody text-sm hover:bg-card-dark-hover transition-colors"
              >
                <span className="font-medium">Language:</span>
                <span style={{ color: "#F97316" }} className="font-semibold">{language}</span>
                <ChevronDown size={16} />
              </button>
              <div
                className="absolute right-0 top-full mt-2 w-32 rounded-lg p-2 hidden group-hover:block z-50"
                style={{ backgroundColor: "#0F0B1E", borderColor: "rgba(255,255,255,0.1)" }}
              >
                {["EN", "HI", "BN"].map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      language === lang ? "bg-orange text-white" : "text-textBody hover:bg-card-dark-hover"
                    }`}
                  >
                    {lang === "EN" ? "English" : lang === "HI" ? "Hindi" : "Bengali"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center py-16">
                <div className="text-6xl mb-4">💬</div>
                <h2 className="text-2xl font-bold text-textLight mb-2">Ask Any Doubt</h2>
                <p className="text-textMuted text-sm mb-8">Powered by EkalavyaAI — exam-quality answers in seconds</p>
                <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {[
                    "Explain Partnership Goodwill",
                    "Revenue Recognition (AS 9)",
                    "Calculate NPV with examples",
                    "Difference between AS and Ind AS"
                  ].map(q => (
                    <button 
                      key={q} 
                      onClick={() => handleSend(q)}
                      className="text-left p-4 rounded-xl text-sm transition-all hover:scale-105"
                      style={{
                        backgroundColor: "rgba(255,255,255,0.05)",
                        borderLeft: "3px solid #F97316",
                        color: "#E5E7EB",
                      }}
                    >
                      <div className="flex items-start gap-2">
                        <Zap size={16} style={{ color: "#F97316", marginTop: "2px" }} />
                        <span>{q}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              style={{ animation: "fade-in 300ms ease-out" }}
            >
              <div
                className={`max-w-xl rounded-2xl px-5 py-4 text-sm leading-relaxed transition-all ${
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

                {/* Typing indicator */}
                {msg.streaming && (
                  <div className="flex gap-1 mt-2">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: "#F97316",
                          animation: `bounce 1.4s infinite`,
                          animationDelay: `${i * 0.2}s`,
                        }}
                      />
                    ))}
                  </div>
                )}

                {/* Action buttons for AI responses */}
                {msg.role === "assistant" && !msg.streaming && (
                  <div className="flex gap-2 mt-3 pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                    <button
                      onClick={() => downloadPDF(i)}
                      className="flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-colors hover:bg-white/10"
                      style={{ color: "#F97316" }}
                      title="Download as PDF"
                    >
                      <Download size={14} />
                      <span>PDF</span>
                    </button>
                    <button
                      className="flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-colors hover:bg-white/10"
                      style={{ color: "#F97316" }}
                      title="Save to library"
                    >
                      <Save size={14} />
                      <span>Save</span>
                    </button>
                    <button
                      className="flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-colors hover:bg-white/10"
                      style={{ color: "#F97316" }}
                      title="Read aloud"
                    >
                      <Volume2 size={14} />
                      <span>Read</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input Area */}
        <div
          className="border-t sticky bottom-0 p-6"
          style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div className="max-w-4xl mx-auto flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask your doubt here... (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="input-dark flex-1 resize-none"
              style={{
                backgroundColor: "#1E1535",
                borderColor: "rgba(76, 29, 149, 0.3)",
                maxHeight: "120px",
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={streaming || !input.trim()}
              className="btn-orange px-6 disabled:opacity-40 transition-all flex items-center gap-2"
            >
              <Send size={18} />
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sidebar overlay on mobile */}
      {sidebarOpen && (
        <button
          className="fixed inset-0 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
          style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
        />
      )}
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen flex items-center justify-center" style={{ backgroundColor: "#0F0B1E" }}>
          <div className="text-center">
            <div className="animate-spin w-10 h-10 border-4 border-orange border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-textBody font-caveat text-lg">Loading AI Teacher...</p>
          </div>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
