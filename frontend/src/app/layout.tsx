// Next.js 根布局 —— 顶部导航栏 + 登录入口 + 页面主体

"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import "./globals.css";
import LoginModal from "@/components/LoginModal";
import SplashScreen from "@/components/SplashScreen";
import { isLoggedIn, clearToken, onAuthRequired } from "@/lib/auth";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showSplash, setShowSplash] = useState(true);
  const [splashFading, setSplashFading] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  // 仅客户端挂载后才显示 UI（防止 SSR 水合不匹配）
  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
  }, []);

  // 闪屏开场：挂载后 2 秒开始淡出，2.5 秒后移除
  useEffect(() => {
    if (!mounted) return;
    const fadeTimer = setTimeout(() => setSplashFading(true), 2000);
    const removeTimer = setTimeout(() => setShowSplash(false), 2500);
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(removeTimer);
    };
  }, [mounted]);

  // 监听全局"需要登录"事件
  useEffect(() => {
    const unsubscribe = onAuthRequired(() => {
      setLoggedIn(false);
      setShowLogin(true);
    });
    return unsubscribe;
  }, []);

  function handleLogin() {
    setLoggedIn(true);
  }

  function handleLogout() {
    clearToken();
    setLoggedIn(false);
    router.push("/");
  }

  // SSR 阶段返回最小骨架（防止 usePathname 返回 null 导致水合错误）
  const isHome = !mounted || pathname === "/";
  const showBackLink = mounted && pathname !== "/";

  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">
        {showSplash && <SplashScreen fading={splashFading} />}

        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📋</span>
              <a href="/" className="text-xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
                智能合同审查系统
              </a>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full hidden sm:inline">
                AI 驱动
              </span>
            </div>

            <div className="flex items-center gap-3">
              {showBackLink && (
                <a
                  href="/"
                  className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
                >
                  ← 首页
                </a>
              )}

              {mounted && loggedIn && (
                <a
                  href="/admin"
                  className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
                >
                  ⚙️ 管理设置
                </a>
              )}

              {mounted ? (
                loggedIn ? (
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 transition-colors"
                  >
                    <span className="w-2 h-2 bg-green-500 rounded-full" />
                    已登录
                    <span className="text-xs text-gray-400 ml-1">退出</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setShowLogin(true)}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  >
                    🔐 登录
                  </button>
                )
              ) : (
                <span className="text-sm text-gray-400">加载中...</span>
              )}
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-6">
          {children}
        </main>

        <LoginModal
          open={showLogin}
          onClose={() => setShowLogin(false)}
          onLogin={handleLogin}
        />
      </body>
    </html>
  );
}
