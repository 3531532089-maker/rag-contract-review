// 闪屏开场页 —— 深色科技风，logo + 系统名 + 进度条/扫描线动画
// 由 RootLayout 控制：挂载后 2 秒开始淡出，2.5 秒后移除

"use client";

interface Props {
  fading: boolean; // 是否正在淡出（父组件控制）
}

export default function SplashScreen({ fading }: Props) {
  return (
    <div
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-slate-950 overflow-hidden transition-opacity duration-500 ${
        fading ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      {/* 背景：光晕 + 网格 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="splash-glow absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[640px] h-[640px] rounded-full bg-blue-600/15 blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
            backgroundSize: "44px 44px",
          }}
        />
      </div>

      {/* 内容 */}
      <div className="relative z-10 flex flex-col items-center px-6">
        <div className="splash-logo text-7xl mb-8 drop-shadow-[0_0_32px_rgba(59,130,246,0.65)]">
          📋
        </div>

        <h1 className="splash-title text-3xl font-bold text-white tracking-wide">
          智能合同审查系统
        </h1>
        <p className="splash-subtitle text-slate-400 mt-3 text-sm tracking-[0.35em]">
          AI 驱动的合同风控平台
        </p>

        {/* 进度条 + 扫描线 */}
        <div className="splash-progress-wrap mt-12 w-72">
          <div className="relative h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="splash-progress-bar h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400" />
            <div className="splash-scanline absolute top-0 h-full w-16 bg-white/50 blur-[2px]" />
          </div>
          <p className="mt-4 text-center text-xs text-slate-500 tracking-[0.3em] animate-pulse">
            正在加载审查引擎...
          </p>
        </div>
      </div>
    </div>
  );
}
