// 风险等级标签 —— 高/中/低 彩色标签

import { RISK_BADGE_ZH } from "@/lib/types";

interface Props {
  level: "high" | "medium" | "low";
}

const COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-300",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
  low: "bg-green-100 text-green-700 border-green-300",
};

export default function RiskBadge({ level }: Props) {
  return (
    <span
      className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full border ${COLORS[level]}`}
    >
      {RISK_BADGE_ZH[level]}
    </span>
  );
}
