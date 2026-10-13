// 合同详情页 —— 原文 / 风险审查 / AI 问答（标签切换，聊天记录跨标签保留）

"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import {
  getContract,
  reviewContract,
  getReview,
  chatWithContractStream,
  listChatSessions,
  getChatSession,
  deleteChatSession,
} from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import RiskGauge from "@/components/RiskGauge";
import RiskCard from "@/components/RiskCard";
import ChatPanel from "@/components/ChatPanel";
import SessionSidebar from "@/components/SessionSidebar";
import LoginModal from "@/components/LoginModal";
import type { ContractDetail, ReviewResponse, ChatMessage, ChatSession } from "@/lib/types";

type Tab = "text" | "review" | "chat";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "text", label: "合同原文", icon: "📄" },
  { key: "review", label: "风险审查", icon: "🔍" },
  { key: "chat", label: "AI 问答", icon: "💬" },
];

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>(
    (searchParams.get("tab") as Tab) || "text"
  );

  // ===== 聊天状态（提升到页面级别，切换标签不丢失） =====
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // 加载合同详情
  const loadContract = useCallback(async () => {
    try {
      setError("");
      const data = await getContract(id);
      setContract(data);

      if (data.risk_score !== null) {
        try {
          const rev = await getReview(id);
          setReview(rev);
        } catch {
          // 审查结果加载失败不影响
        }
      }
    } catch {
      setError("合同不存在或加载失败");
    } finally {
      setPageLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadContract();
  }, [loadContract]);

  // ===== 会话管理（多轮对话） =====
  const loadSessions = useCallback(async () => {
    try {
      const list = await listChatSessions(id);
      setSessions(list);
    } catch {
      // 加载会话列表失败不阻塞问答
    }
  }, [id]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 选中会话 → 拉取历史消息
  async function handleSelectSession(sessionId: string) {
    setCurrentSessionId(sessionId);
    try {
      const detail = await getChatSession(sessionId);
      const msgs: ChatMessage[] = detail.messages.map((m) => ({
        role: m.role,
        content: m.content,
        sources: m.sources ?? undefined,
      }));
      setChatMessages(msgs);
      setChatError("");
    } catch {
      setChatError("会话历史加载失败");
    }
  }

  // 新建会话 → 清空当前会话与消息
  function handleNewSession() {
    setCurrentSessionId(null);
    setChatMessages([]);
    setChatError("");
  }

  // 删除会话
  async function handleDeleteSession(sessionId: string) {
    try {
      await deleteChatSession(sessionId);
      if (currentSessionId === sessionId) {
        handleNewSession();
      }
      await loadSessions();
    } catch {
      setChatError("删除会话失败");
    }
  }

  // 触发审查
  async function triggerReview() {
    setReviewing(true);
    setError("");
    try {
      const rev = await reviewContract(id);
      setReview(rev);
      setActiveTab("review");
      const updated = await getContract(id);
      setContract(updated);
    } catch {
      setError("审查失败，请稍后重试");
    } finally {
      setReviewing(false);
    }
  }

  // 发送聊天消息（SSE 流式：边生成边追加 token）
  async function handleChatSend(question: string) {
    if (!isLoggedIn()) {
      setShowLogin(true);
      return;
    }

    const userMsg: ChatMessage = { role: "user", content: question };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);
    setChatError("");

    try {
      await chatWithContractStream(id, question, currentSessionId, {
        onSession: (sessionId) => {
          setCurrentSessionId(sessionId);
          loadSessions();
        },
        onSources: (sources) => {
          setChatMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === "assistant") {
              last.sources = sources;
            } else {
              copy.push({ role: "assistant", content: "", sources });
            }
            return copy;
          });
        },
        onToken: (token) => {
          setChatMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === "assistant") {
              last.content += token;
            } else {
              copy.push({ role: "assistant", content: token });
            }
            return copy;
          });
        },
        onError: (message) => {
          setChatError(`AI 回答失败：${message}`);
        },
      });
    } catch (err: unknown) {
      const e = err as Error;
      setChatError(`AI 回答失败：${e?.message || "未知错误"}`);
    } finally {
      setChatLoading(false);
      // 清理空 AI 气泡（无内容且无引用）
      setChatMessages((prev) => {
        const copy = [...prev];
        const last = copy[copy.length - 1];
        if (last && last.role === "assistant" && !last.content && !last.sources?.length) {
          copy.pop();
        }
        return copy;
      });
    }
  }

  if (pageLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="inline-block w-10 h-10 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (error && !contract) {
    return (
      <div className="text-center py-20">
        <span className="text-5xl block mb-4">😕</span>
        <p className="text-red-500 text-sm mb-4">{error}</p>
        <a href="/" className="text-blue-500 hover:underline text-sm">
          ← 返回首页
        </a>
      </div>
    );
  }

  if (!contract) return null;

  return (
    <div className="space-y-6">
      {/* 合同信息头 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              📄 {contract.filename}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span>类型：{contract.contract_type}</span>
              <span>{contract.char_count.toLocaleString()} 字</span>
              <span>
                上传于 {new Date(contract.created_at).toLocaleDateString("zh-CN")}
              </span>
            </div>
          </div>

          {contract.risk_score !== null && review && (
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <RiskGauge score={contract.risk_score} size={90} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 标签导航 */}
      <div className="flex border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* 标签内容 */}
      <div>
        {/* 合同原文 */}
        <div className={activeTab === "text" ? "" : "hidden"}>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
              {contract.content}
            </pre>
          </div>
        </div>

        {/* 风险审查 */}
        <div className={activeTab === "review" ? "" : "hidden"}>
          <div className="space-y-4">
            {review ? (
              <>
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-start gap-5 flex-wrap">
                    <div className="relative">
                      <RiskGauge score={review.risk_score} size={100} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-800 mb-1">审查摘要</h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {review.summary}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-700">
                    风险清单 ({review.risks.length} 条)
                  </h3>
                  {review.risks.length === 0 ? (
                    <div className="text-center py-8 bg-green-50 rounded-xl border border-green-200">
                      <span className="text-3xl block mb-2">🎉</span>
                      <p className="text-green-700 font-medium">未发现明显风险</p>
                    </div>
                  ) : (
                    review.risks.map((risk, i) => (
                      <RiskCard key={i} risk={risk} index={i} />
                    ))
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
                <span className="text-5xl block mb-4">🔍</span>
                <p className="text-gray-600 font-medium mb-2">尚未审查</p>
                <p className="text-sm text-gray-400 mb-4">
                  AI 将从 8 个维度全面扫描合同风险
                </p>
                <button
                  onClick={triggerReview}
                  disabled={reviewing}
                  className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg
                             hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
                >
                  {reviewing ? (
                    <span className="flex items-center gap-2">
                      <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      审查中...
                    </span>
                  ) : (
                    "开始审查"
                  )}
                </button>
                {error && (
                  <p className="text-sm text-red-500 mt-3">{error}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* AI 问答 — 始终渲染，用 hidden 切换，聊天记录不会丢失 */}
        <div className={activeTab === "chat" ? "" : "hidden"}>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="w-full md:w-64 md:shrink-0">
              <SessionSidebar
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelect={handleSelectSession}
                onNew={handleNewSession}
                onDelete={handleDeleteSession}
              />
            </div>
            <div className="flex-1 min-w-0">
              <ChatPanel
                contractId={id}
                messages={chatMessages}
                loading={chatLoading}
                error={chatError}
                onSend={handleChatSend}
                onRetry={() => {
                  // 重试最后一条用户消息
                  const lastUser = [...chatMessages].reverse().find((m) => m.role === "user");
                  if (lastUser) {
                    setChatError("");
                    handleChatSend(lastUser.content);
                  }
                }}
                onLoginRequired={() => setShowLogin(true)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 登录弹窗 */}
      <LoginModal
        open={showLogin}
        onClose={() => setShowLogin(false)}
        onLogin={() => setShowLogin(false)}
      />
    </div>
  );
}
