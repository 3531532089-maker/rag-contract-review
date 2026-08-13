// 合同卡片 —— 展示列表中的单个合同

"use client";

import type { ContractListItem } from "@/lib/types";

interface Props {
  contract: ContractListItem;
  onView: (id: string) => void;
  onReview: (id: string) => void;
  onDelete: (id: string) => void;
}

function scoreColor(score: number | null): string {
  if (score === null) return "text-gray-400 bg-gray-100";
  if (score >= 71) return "text-red-600 bg-red-50";
  if (score >= 41) return "text-yellow-600 bg-yellow-50";
  return "text-green-600 bg-green-50";
}

export default function ContractCard({ contract, onView, onReview, onDelete }: Props) {
  const date = new Date(contract.created_at).toLocaleDateString("zh-CN");
  const isReviewed = contract.risk_score !== null;

  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white hover:shadow-md transition-shadow min-w-0">
      <div className="flex items-start justify-between">
        {/* 左侧：文件信息 */}
        <div className="flex items-start gap-3 min-w-0">
          <span className="text-2xl mt-0.5 shrink-0">📄</span>
          <div className="min-w-0">
            <h3 className="font-semibold text-gray-800 truncate" title={contract.filename}>
              {contract.filename}
            </h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-gray-400">
              <span>{contract.contract_type}</span>
              <span>{date}</span>
              <span>{contract.char_count.toLocaleString()} 字</span>
            </div>
          </div>
        </div>

        {/* 右侧：风险评分 */}
        <div className="shrink-0 ml-4">
          <div className={`text-center px-3 py-2 rounded-lg ${scoreColor(contract.risk_score)}`}>
            <div className="text-lg font-bold">
              {isReviewed ? contract.risk_score : "--"}
            </div>
            <div className="text-[10px]">分</div>
          </div>
        </div>
      </div>

      {/* 底部：操作按钮 */}
      <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
        <button
          onClick={() => onView(contract.id)}
          className="flex-1 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg
                     hover:bg-blue-100 transition-colors"
        >
          查看详情
        </button>
        <button
          onClick={() => onReview(contract.id)}
          className="flex-1 py-2 text-xs font-medium text-orange-600 bg-orange-50 rounded-lg
                     hover:bg-orange-100 transition-colors"
        >
          {isReviewed ? "重新审查" : "风险审查"}
        </button>
        <button
          onClick={() => onDelete(contract.id)}
          className="py-2 px-3 text-xs font-medium text-red-500 bg-red-50 rounded-lg
                     hover:bg-red-100 transition-colors"
        >
          删除
        </button>
      </div>
    </div>
  );
}
