// 单条风险卡片 —— 展示风险等级、条款、原因、建议、原文引用

"use client";

import { useState } from "react";
import RiskBadge from "./RiskBadge";
import type { RiskItem } from "@/lib/types";

interface Props {
  risk: RiskItem;
  index: number;
}

export default function RiskCard({ risk, index }: Props) {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className="border rounded-lg p-4 bg-white hover:shadow-sm transition-shadow">
      {/* 头部：序号 + 等级 + 条款名 */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm text-gray-400 font-mono">#{index + 1}</span>
        <RiskBadge level={risk.risk_level} />
        <h4 className="font-semibold text-gray-800">{risk.clause}</h4>
      </div>

      {/* 风险原因 */}
      <div className="mb-2">
        <span className="text-xs text-gray-400">⚠️ 风险原因</span>
        <p className="text-sm text-gray-700 mt-0.5">{risk.reason}</p>
      </div>

      {/* 修改建议 */}
      <div className="mb-2">
        <span className="text-xs text-gray-400">💡 修改建议</span>
        <p className="text-sm text-gray-700 mt-0.5">{risk.suggestion}</p>
      </div>

      {/* 原文引用（可折叠） */}
      {risk.original_text && (
        <div>
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className="text-xs text-blue-500 hover:text-blue-700"
          >
            {showOriginal ? "收起原文 ▲" : "查看原文 ▼"}
          </button>
          {showOriginal && (
            <blockquote className="mt-1 pl-3 border-l-2 border-gray-300 text-xs text-gray-500 italic whitespace-pre-wrap">
              {risk.original_text}
            </blockquote>
          )}
        </div>
      )}
    </div>
  );
}
