// AI 对话面板 —— 受控组件，状态由父页面管理（跨标签切换不丢失）

"use client";

import { useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/types";

interface Props {
  contractId: string;
  messages: ChatMessage[];
  loading: boolean;
  error: string;
  onSend: (question: string) => void;
  onRetry?: () => void;
  onLoginRequired: () => void;
}

export default function ChatPanel({
  contractId: _contractId,
  messages,
  loading,
  error,
  onSend,
  onRetry,
  onLoginRequired: _onLoginRequired,
}: Props) {
  const listEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 自动滚到底部
  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const input = form.elements.namedItem("question") as HTMLInputElement;
    const q = input.value.trim();
    if (!q || loading) return;
    onSend(q);
    input.value = "";
  }

  return (
    <div className="flex flex-col h-[500px] border rounded-xl bg-white">
      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <span className="text-4xl block mb-3">💬</span>
              <p className="text-sm">在下方输入问题，对合同进行 AI 问答</p>
              <p className="text-xs mt-1">例如："试用期有多长？"、"违约责任条款是否公平？"</p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-md"
                  : "bg-gray-100 text-gray-800 rounded-bl-md"
              }`}
            >
              {msg.content}

              {/* 引用来源 */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-400 mb-1">📎 引用来源：</p>
                  {msg.sources.map((src, j) => (
                    <p key={j} className="text-xs text-gray-400 italic truncate">
                      {src.length > 80 ? src.slice(0, 80) + "..." : src}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* 加载动画：等待 AI 首个 token（还没有 assistant 消息）时才显示 */}
        {loading &&
          (messages.length === 0 ||
            messages[messages.length - 1].role !== "assistant") && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-3 rounded-bl-md">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        {/* 错误提示 + 重试按钮 */}
        {error && (
          <div className="text-center text-sm">
            <div className="text-red-500 bg-red-50 py-2 px-4 rounded-lg mb-2">
              {error}
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-blue-600 hover:text-blue-700 text-xs underline"
              >
                重新发送
              </button>
            )}
          </div>
        )}

        <div ref={listEndRef} />
      </div>

      {/* 输入区域 */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 p-3 flex gap-2"
      >
        <input
          name="question"
          type="text"
          placeholder="输入你的问题..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
        >
          发送
        </button>
      </form>
    </div>
  );
}
