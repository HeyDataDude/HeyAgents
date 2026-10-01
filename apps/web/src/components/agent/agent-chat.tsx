"use client";

import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";

interface Msg {
  id: string;
  role: string;
  content: string;
}

export function AgentChat({ agentId, agentName }: { agentId: string; agentName: string }) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const ensureConversation = async (): Promise<string> => {
    if (conversationId) return conversationId;
    const conv = await api.post<{ id: string }>("/api/conversations", { agent_id: agentId });
    setConversationId(conv.id);
    return conv.id;
  };

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setSending(true);
    const temp: Msg = { id: `temp-${Date.now()}`, role: "user", content: text };
    setMessages((m) => [...m, temp]);
    try {
      const cid = await ensureConversation();
      const res = await api.post<any>(`/api/conversations/${cid}/messages`, { content: text });
      setMessages((m) => [...m, res.agent_message]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="card flex h-[60vh] flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="py-10 text-center text-sm text-muted">
            Start a conversation with {agentName}. It has access to its own persistent memory.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-3.5 py-2 text-sm leading-relaxed ${
                m.role === "user" ? "bg-accent text-accent-fg" : "bg-surface-2"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-surface-2 px-3.5 py-2 text-sm text-muted">
              {agentName} is thinking…
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="flex items-center gap-2 border-t p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={`Message ${agentName}…`}
          className="input"
        />
        <button onClick={send} disabled={!input.trim() || sending} className="btn btn-primary h-9 w-9 p-0">
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
