// API 调用封装 —— 统一管理后端通信、auth header、401 拦截

import axios, { AxiosError } from "axios";
import { getToken, triggerAuthRequired } from "./auth";
import type {
  UploadResponse,
  ReviewResponse,
  ChatResponse,
  LoginResponse,
  ContractListResponse,
  ContractDetail,
} from "./types";

// axios 实例
const api = axios.create({
  baseURL: "/api", // Next.js rewrites proxy to http://localhost:8000/api
  timeout: 60000,  // 60s default
});

// ===== 请求拦截器：自动注入 token =====
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ===== 响应拦截器：401 → 弹出登录框 =====
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      triggerAuthRequired();
    }
    return Promise.reject(error);
  }
);

// ===== 认证 =====

export async function login(password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login", { password });
  return data;
}

// ===== 文件上传 =====

export async function uploadContract(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post<UploadResponse>("/upload/contract", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,
  });
  return data;
}

// ===== 合同列表 & 详情（分页） =====

export async function listContracts(
  page: number = 1,
  limit: number = 20
): Promise<ContractListResponse> {
  const { data } = await api.get<ContractListResponse>("/upload/contracts", {
    params: { page, limit },
  });
  return data;
}

export async function getContract(id: string): Promise<ContractDetail> {
  const { data } = await api.get<ContractDetail>(`/upload/contracts/${id}`);
  return data;
}

export async function deleteContract(id: string): Promise<void> {
  await api.delete(`/upload/contracts/${id}`);
}

// ===== 合同审查 =====

export async function reviewContract(id: string): Promise<ReviewResponse> {
  const { data } = await api.post<ReviewResponse>(`/review/${id}`, null, {
    timeout: 130000,
  });
  return data;
}

export async function getReview(id: string): Promise<ReviewResponse> {
  const { data } = await api.get<ReviewResponse>(`/review/${id}`);
  return data;
}

// ===== AI 问答 =====

export async function chatWithContract(
  contractId: string,
  question: string
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", {
    contract_id: contractId,
    question,
  });
  return data;
}

// ===== AI 问答（SSE 流式） =====

export interface ChatStreamCallbacks {
  onSources?: (sources: string[]) => void;
  onToken?: (token: string) => void;
  onError?: (message: string) => void;
}

export async function chatWithContractStream(
  contractId: string,
  question: string,
  callbacks: ChatStreamCallbacks
): Promise<void> {
  const token = getToken();

  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ contract_id: contractId, question }),
  });

  if (!res.ok || !res.body) {
    if (res.status === 401) {
      triggerAuthRequired();
    }
    let detail = `请求失败 (${res.status})`;
    try {
      const errData = await res.json();
      if (errData?.detail) detail = errData.detail;
    } catch {
      // 忽略解析错误
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 事件以空行分隔
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;
      try {
        const event = JSON.parse(payload) as {
          type?: string;
          sources?: string[];
          content?: string;
          message?: string;
        };
        if (event.type === "sources") {
          callbacks.onSources?.(event.sources ?? []);
        } else if (event.type === "token") {
          callbacks.onToken?.(event.content ?? "");
        } else if (event.type === "error") {
          callbacks.onError?.(event.message ?? "未知错误");
        }
        // "done" 事件无需处理，循环结束即完成
      } catch {
        // 忽略无法解析的行
      }
    }
  }
}
