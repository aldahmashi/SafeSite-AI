"use client";

import { useState, useRef, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { api } from "@/lib/api";
import { Send, Bot, User, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "How many incidents were detected overall?",
  "What are the most common PPE violations?",
  "What is the current safety compliance status?",
  "Which risk level appears most often?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am SafeSite AI's safety assistant. I can help you analyze PPE violations, compliance trends, and safety incidents. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chatWithAssistant(trimmed);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.reply },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I could not reach the backend. Please make sure the server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const showSuggestions = messages.length === 1 && !loading;

  return (
    <DashboardShell title="AI Safety Assistant">
      <div className="flex flex-col" style={{ height: "calc(100vh - 140px)" }}>
        {/* Header badge */}
        <div className="mb-4 flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-full">
            <Sparkles size={12} className="text-amber-400" />
            <span className="text-amber-400 text-xs font-medium">
              Powered by GPT-4o-mini &mdash; set LLM_API_KEY in .env to enable
            </span>
          </div>
        </div>

        {/* Message list */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1">
          {messages.map((msg, i) => (
            <Bubble key={i} message={msg} />
          ))}

          {loading && (
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-500/10 rounded-full shrink-0">
                <Bot size={16} className="text-amber-400" />
              </div>
              <div className="bg-[#1e293b] border border-[#334155] rounded-xl px-4 py-3">
                <span className="text-slate-400 text-sm animate-pulse">
                  Thinking&hellip;
                </span>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Suggestion chips */}
        {showSuggestions && (
          <div className="mb-4 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="px-3 py-1.5 bg-[#1e293b] border border-[#334155] hover:border-amber-500/50 text-slate-400 hover:text-slate-200 text-xs rounded-full transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input row */}
        <div className="flex gap-3">
          <input
            className="flex-1 bg-[#1e293b] border border-[#334155] rounded-xl px-4 py-3 text-slate-200 text-sm focus:outline-none focus:border-amber-500 placeholder:text-slate-500"
            placeholder="Ask about safety incidents, compliance, violations&hellip;"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            disabled={loading}
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-black rounded-xl transition-colors"
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}

function Bubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`p-2 rounded-full shrink-0 ${
          isUser ? "bg-blue-500/10" : "bg-amber-500/10"
        }`}
      >
        {isUser ? (
          <User size={16} className="text-blue-400" />
        ) : (
          <Bot size={16} className="text-amber-400" />
        )}
      </div>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
          isUser
            ? "bg-blue-500/10 border border-blue-500/20 text-slate-200"
            : "bg-[#1e293b] border border-[#334155] text-slate-300"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
