// 自定义 404 页面
export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <span className="text-6xl block mb-4">🔍</span>
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          页面不存在
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          请检查链接是否正确，或返回首页
        </p>
        <a
          href="/"
          className="inline-block px-4 py-2 bg-blue-600 text-white text-sm font-medium
                     rounded-lg hover:bg-blue-700 transition-colors"
        >
          ← 返回首页
        </a>
      </div>
    </div>
  );
}
