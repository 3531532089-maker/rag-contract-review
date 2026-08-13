"use client";

// 全局错误边界 —— 捕获渲染错误，避免白屏
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <span className="text-5xl block mb-4">⚠️</span>
        <h2 className="text-lg font-semibold text-gray-800 mb-2">
          页面加载出错
        </h2>
        <p className="text-sm text-gray-500 mb-4 max-w-md">
          {error.message || "发生了意外错误，请稍后重试"}
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 transition-colors"
        >
          重新加载
        </button>
      </div>
    </div>
  );
}
