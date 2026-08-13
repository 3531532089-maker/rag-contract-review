// 首页 —— 上传合同 + 合同列表（分页）

"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import UploadZone from "@/components/UploadZone";
import ContractCard from "@/components/ContractCard";
import LoginModal from "@/components/LoginModal";
import { listContracts, deleteContract, reviewContract } from "@/lib/api";
import { onAuthRequired } from "@/lib/auth";
import type { ContractListItem, UploadResponse } from "@/lib/types";

const PAGE_SIZE = 20;

export default function Home() {
  const [contracts, setContracts] = useState<ContractListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  // 分页
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const router = useRouter();

  // 加载合同列表
  const loadContracts = useCallback(async (p: number = 1) => {
    try {
      setError("");
      const data = await listContracts(p, PAGE_SIZE);
      setContracts(data.contracts);
      setTotal(data.total);
      setPage(data.page);
    } catch {
      setError("加载合同列表失败，请检查后端是否运行");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContracts(1);
  }, [loadContracts]);

  // 监听登录过期事件
  useEffect(() => {
    const unsub = onAuthRequired(() => setShowLogin(true));
    return unsub;
  }, []);

  // 上传成功回调
  function handleUploaded(_result: UploadResponse) {
    loadContracts(1);
  }

  // 查看详情
  function handleView(id: string) {
    router.push(`/contract/${id}?tab=text`);
  }

  // 触发审查
  async function handleReview(id: string) {
    setReviewingId(id);
    try {
      await reviewContract(id);
      showNotification("success", "审查完成！正在跳转到结果页面...");
      setTimeout(() => router.push(`/contract/${id}?tab=review`), 800);
    } catch {
      showNotification("error", "审查失败，请稍后重试");
    } finally {
      setReviewingId(null);
    }
  }

  // 删除合同
  async function handleDelete(id: string) {
    const filename = contracts.find((c) => c.id === id)?.filename || "未知";
    if (!confirm(`确定要删除 "${filename}" 吗？此操作不可恢复。`)) return;

    try {
      await deleteContract(id);
      showNotification("success", `"${filename}" 已删除`);
      loadContracts(page);
    } catch {
      showNotification("error", "删除失败，请稍后重试");
    }
  }

  function showNotification(type: "success" | "error", message: string) {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-8">
      {/* 通知 */}
      {notification && (
        <div
          className={`fixed top-16 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm ${
            notification.type === "success"
              ? "bg-green-600 text-white"
              : "bg-red-600 text-white"
          }`}
        >
          {notification.message}
        </div>
      )}

      {/* 欢迎区域 */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          欢迎使用智能合同审查系统
        </h2>
        <p className="text-gray-500 text-sm max-w-xl mx-auto">
          上传合同文件，AI 自动识别合同类型并进行多维度风险分析，
          支持智能问答，帮助快速识别潜在风险
        </p>
      </div>

      {/* 上传区域 */}
      <section>
        <h3 className="text-lg font-semibold text-gray-700 mb-3">📤 上传合同</h3>
        <UploadZone onUploaded={handleUploaded} />
      </section>

      {/* 合同列表 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-700">
            📋 已上传合同
            {!loading && (
              <span className="text-sm text-gray-400 font-normal ml-2">
                ({total})
              </span>
            )}
          </h3>
          <button
            onClick={() => loadContracts(page)}
            className="text-xs text-blue-500 hover:text-blue-700 transition-colors"
          >
            刷新列表
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">
            <div className="inline-block w-8 h-8 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mb-2" />
            <p className="text-sm">加载中...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-500 text-sm">{error}</p>
          </div>
        ) : contracts.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
            <span className="text-4xl block mb-3">📭</span>
            <p className="text-gray-400 text-sm">暂无合同，请先上传</p>
          </div>
        ) : (
          <>
            <div className="grid gap-3">
              {contracts.map((c) => (
                <ContractCard
                  key={c.id}
                  contract={c}
                  onView={handleView}
                  onReview={handleReview}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {/* 分页控件 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  onClick={() => loadContracts(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30
                             hover:bg-gray-100 transition-colors"
                >
                  上一页
                </button>
                <span className="text-sm text-gray-500 px-2">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => loadContracts(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30
                             hover:bg-gray-100 transition-colors"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </section>

      {/* 正在审查的蒙层 */}
      {reviewingId && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center">
          <div className="bg-white rounded-2xl p-8 text-center shadow-xl">
            <div className="inline-block w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4" />
            <p className="text-gray-700 font-medium">正在审查合同中...</p>
            <p className="text-sm text-gray-400 mt-1">AI 正在从 8 个维度全面扫描，请稍候</p>
          </div>
        </div>
      )}

      {/* 登录弹窗 */}
      <LoginModal
        open={showLogin}
        onClose={() => setShowLogin(false)}
        onLogin={() => {
          setShowLogin(false);
          loadContracts(page);
        }}
      />
    </div>
  );
}
