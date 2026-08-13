// 风险评分环形图 —— SVG 圆环 + 中间分数 + 颜色渐变

"use client";

interface Props {
  score: number;  // 0-100
  size?: number;  // 默认 120px
}

export default function RiskGauge({ score, size = 120 }: Props) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(score / 100, 1);
  const offset = circumference * (1 - progress);
  const center = size / 2;

  // 颜色：0-40 绿, 41-70 黄, 71-100 红
  let color: string;
  if (score <= 40) color = "#22c55e";
  else if (score <= 70) color = "#f59e0b";
  else color = "#ef4444";

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* 背景圆环 */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth={strokeWidth}
      />
      {/* 进度圆环（从顶部 12 点方向顺时针） */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${center} ${center})`}
        style={{ transition: "stroke-dashoffset 0.8s ease" }}
      />
      {/* 中间分数 */}
      <text
        x={center}
        y={center}
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize={size * 0.28}
        fontWeight="bold"
      >
        {score}
      </text>
      {/* "分" 字 */}
      <text
        x={center}
        y={center + size * 0.18}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#9ca3af"
        fontSize={size * 0.11}
      >
        分
      </text>
    </svg>
  );
}
