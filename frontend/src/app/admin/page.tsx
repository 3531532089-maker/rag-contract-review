// 管理后台 —— LLM 运行时配置

"use client";

import { useState, useEffect } from "react";
import { getSettings, updateSettings, testLlm, resetSettings } from "@/lib/api";
import { isLoggedIn, triggerAuthRequired, onAuthChange } from "@/lib/auth";
import type { LlmSettings } from "@/lib/types";

const inputCls =
  "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm " +
  "focus:outline-none focus:ring-2 focus:ring-blue-500";

export default function AdminPage() {
  const [mounted, setMounted] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [settings, setSettings] = useState<LlmSettings | null>(null);
  const [form, setForm] = useState({
    llm_model: "",
    llm_base_url: "",
    llm_temperature: "0.3",
    llm_max_tokens: "2000",
  });
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
    const unsub = onAuthChange(() => setLoggedIn(isLoggedIn()));
    return unsub;
  }, []);

  useEffect(() => {
    if (!loggedIn) return;
    loadSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loggedIn]);

  async function loadSettings() {
    setLoading(true);
    try {
      const s = await getSettings();
      setSettings(s);
      setForm({
        llm_model: s.llm_model,
        llm_base_url: s.llm_base_url,
        llm_temperature: String(s.llm_temperature),
        llm_max_tokens: String(s.llm_max_tokens),
      });
    } catch {
      setMessage({ type: "err", text: "加载设置失败" });
    } finally {
      setLoading(false);
    }
  }

  function updateField(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  const formInput = () => ({
    llm_model: form.llm_model,
    llm_base_url: form.llm_base_url,
    llm_temperature: Number(form.llm_temperature),
    llm_max_tokens: Number(form.llm_max_tokens),
  });

  async function handleSave() {
    setBusy(true);
    setMessage(null);
    try {
      const s = await updateSettings(formInput());
      setSettings(s);
      setMessage({ type: "ok", text: "已保存，立即生效（无需重启）" });
    } catch {
      setMessage({ type: "err", text: "保存失败，请检查输入" });
    } finally {
      setBusy(false);
    }
  }

  async function handleTest() {
    setBusy(true);
    setMessage(null);
    try {
      const r = await testLlm(formInput());
      if (r.ok) {
        setMessage({ type: "ok", text: `连接成功（${r.elapsed_ms}ms）：${r.reply ?? ""}` });
      } else {
        setMessage({ type: "err", text: `连接失败：${r.error ?? "未知错误"}` });
      }
    } catch {
      setMessage({ type: "err", text: "测试请求失败" });
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    if (!confirm("恢复默认配置？（清除后台保存的设置，回到 .env 的值）")) return;
    setBusy(true);
    setMessage(null);
    try {
      const s = await resetSettings();
      setSettings(s);
      setForm({
        llm_model: s.llm_model,
        llm_base_url: s.llm_base_url,
        llm_temperature: String(s.llm_temperature),
        llm_max_tokens: String(s.llm_max_tokens),
      });
      setMessage({ type: "ok", text: "已恢复 .env 默认配置" });
    } catch {
      setMessage({ type: "err", text: "恢复失败" });
    } finally {
      setBusy(false);
    }
  }

  if (!mounted) return null;

  if (!loggedIn) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center">
        <span className="text-5xl block mb-4">🔐</span>
        <p className="text-gray-600 font-medium mb-4">请先登录管理员账号</p>
        <button
          onClick={() => triggerAuthRequired()}
          className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 transition-colors"
        >
          登录
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">⚙️ LLM 配置</h1>
        <p className="text-sm text-gray-500 mt-1">
          修改后保存立即生效，无需重启后端。API Key 仍从后端{" "}
          <code className="text-xs bg-gray-100 px-1 rounded">.env</code> 读取，不在此处填写。
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        {loading ? (
          <div className="text-sm text-gray-400">加载中...</div>
        ) : (
          <>
            {settings && (
              <div className="text-xs text-gray-400 flex gap-4 flex-wrap">
                {Object.entries(settings.sources).map(([k, src]) => (
                  <span key={k}>
                    {k.replace("llm_", "")}:{" "}
                    <span className={src === "db" ? "text-amber-600 font-medium" : "text-gray-400"}>
                      {src === "db" ? "后台覆盖" : ".env 默认"}
                    </span>
                  </span>
                ))}
              </div>
            )}

            <Field label="模型" hint="如 deepseek-v4-pro / gpt-4o">
              <input
                value={form.llm_model}
                onChange={(e) => updateField("llm_model", e.target.value)}
                className={inputCls}
                placeholder="模型名称"
              />
            </Field>

            <Field label="接口地址 (Base URL)">
              <input
                value={form.llm_base_url}
                onChange={(e) => updateField("llm_base_url", e.target.value)}
                className={inputCls}
                placeholder="https://api.deepseek.com/v1"
              />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="温度 (Temperature)">
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={form.llm_temperature}
                  onChange={(e) => updateField("llm_temperature", e.target.value)}
                  className={inputCls}
                />
              </Field>
              <Field label="最大长度 (Max Tokens)">
                <input
                  type="number"
                  min="1"
                  value={form.llm_max_tokens}
                  onChange={(e) => updateField("llm_max_tokens", e.target.value)}
                  className={inputCls}
                />
              </Field>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleSave}
                disabled={busy}
                className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                           hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
              >
                {busy ? "处理中..." : "保存"}
              </button>
              <button
                onClick={handleTest}
                disabled={busy}
                className="px-5 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg
                           hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                测试连接
              </button>
              <button
                onClick={handleReset}
                disabled={busy}
                className="px-5 py-2 text-red-500 text-sm font-medium rounded-lg
                           hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                恢复默认
              </button>
            </div>

            {message && (
              <p className={`text-sm ${message.type === "ok" ? "text-green-600" : "text-red-500"}`}>
                {message.text}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      {hint && <span className="text-xs text-gray-400 ml-2">{hint}</span>}
      <div className="mt-1">{children}</div>
    </label>
  );
}
