// 登录弹窗 —— 居中弹窗，毛玻璃背景，输入密码登录

"use client";

import { useState, useEffect, useRef } from "react";
import { login } from "@/lib/api";
import { setToken } from "@/lib/auth";

interface Props {
  open: boolean;
  onClose: () => void;
  onLogin: () => void;  // 登录成功后回调（刷新数据）
}

export default function LoginModal({ open, onClose, onLogin }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // 打开时自动聚焦密码框
  useEffect(() => {
    if (open) {
      setPassword("");
      setError("");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password.trim()) return;

    setLoading(true);
    setError("");
    try {
      const result = await login(password);
      setToken(result.token);
      onLogin();
      onClose();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "登录失败，请检查密码";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 毛玻璃背景 */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 弹窗 */}
      <div className="relative bg-white rounded-2xl shadow-2xl p-8 w-full max-w-sm mx-4 animate-in">
        <h2 className="text-xl font-bold text-gray-800 mb-2">管理员登录</h2>
        <p className="text-sm text-gray-500 mb-6">
          上传合同、AI 审查等功能需要管理员权限
        </p>

        <form onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="请输入管理员密码"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       transition-shadow"
            disabled={loading}
          />

          {error && (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          )}

          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 text-sm text-gray-600 border border-gray-300 rounded-lg
                         hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2.5 text-sm text-white bg-blue-600 rounded-lg
                         hover:bg-blue-700 disabled:bg-blue-300 transition-colors font-medium"
            >
              {loading ? "登录中..." : "登录"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
