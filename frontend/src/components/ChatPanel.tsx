"use client";

import { useState, useRef } from "react";
import { apiUrl, authHeaders } from "../lib/api";

type ChatEvent =
  | { type: "thinking"; thread_id: string }
  | { type: "tool_call"; tool: string; args: unknown }
  | { type: "tool_result"; tool: string; result: string }
  | { type: "token"; text: string }
  | { type: "done"; thread_id: string }
  | { type: "error"; message: string };

type ChatMessage = { role: "user" | "assistant"; content: string; toolCalls?: string[] };

export default function ChatPanel({ lat, lng }: { lat?: number; lng?: number }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const threadIdRef = useRef<string | null>(null);

  async function send() {
    if (!input.trim() || busy) return;
    const userText = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: userText }, { role: "assistant", content: "", toolCalls: [] }]);
    setBusy(true);

    try {
      const res = await fetch(apiUrl("/api/v1/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ message: userText, lat, lng, thread_id: threadIdRef.current }),
      });

      if (res.status === 401) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = "Please sign in to chat with the assistant.";
          return updated;
        });
        return;
      }
      if (!res.body) throw new Error("No response stream");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;
          const evt: ChatEvent = JSON.parse(raw);

          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (evt.type === "token") last.content += evt.text;
            else if (evt.type === "tool_call") last.toolCalls = [...(last.toolCalls || []), evt.tool];
            else if (evt.type === "done") threadIdRef.current = evt.thread_id;
            else if (evt.type === "error") last.content = evt.message;
            return updated;
          });
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = "Connection lost. Please try again.";
        return updated;
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-emerald-600 text-white shadow-xl flex items-center justify-center text-2xl hover:bg-emerald-700 transition-all"
        aria-label="Open Foodly Assistant"
      >
        💬
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] h-[520px] bg-white border border-slate-200 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          <div className="px-4 py-3 bg-slate-900 text-white font-bold text-sm flex items-center justify-between">
            Foodly Assistant
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white">✕</button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
            {messages.length === 0 && (
              <p className="text-slate-400 text-center mt-10">
                Try: "find biryani under 300 near NUST"
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 ${m.role === "user" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-800"}`}>
                  {m.toolCalls && m.toolCalls.length > 0 && (
                    <div className="mb-1 flex flex-wrap gap-1">
                      {m.toolCalls.map((t, j) => (
                        <span key={j} className="text-[9px] font-bold uppercase bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{m.content || (busy && i === messages.length - 1 ? "…" : "")}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 border-t border-slate-100 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask about food nearby…"
              disabled={busy}
              className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
            />
            <button
              onClick={send}
              disabled={busy}
              className="bg-emerald-600 text-white px-4 py-2 rounded-xl text-sm font-bold disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}