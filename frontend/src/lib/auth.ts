// 认证状态管理
// Token 存在 localStorage，登录过期时通过事件系统弹出登录框

const TOKEN_KEY = "contract_review_token";

// ===== Token 读写 =====

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  notifyAuthChange();
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  notifyAuthChange();
}

export function isLoggedIn(): boolean {
  return getToken() !== null;
}

// ===== 登录过期事件（发布/订阅） =====

type AuthCallback = () => void;
let listeners: AuthCallback[] = [];

export function onAuthRequired(callback: AuthCallback): () => void {
  listeners.push(callback);
  // 返回取消订阅函数
  return () => {
    listeners = listeners.filter((cb) => cb !== callback);
  };
}

export function triggerAuthRequired(): void {
  // 触发前先清除旧 token，避免重复 401
  clearToken();
  listeners.forEach((cb) => cb());
}

// ===== 登录状态变化（登录/退出时通知，供页面刷新登录态） =====

type AuthChangeCallback = () => void;
let authChangeListeners: AuthChangeCallback[] = [];

export function onAuthChange(callback: AuthChangeCallback): () => void {
  authChangeListeners.push(callback);
  return () => {
    authChangeListeners = authChangeListeners.filter((cb) => cb !== callback);
  };
}

function notifyAuthChange(): void {
  authChangeListeners.forEach((cb) => cb());
}
