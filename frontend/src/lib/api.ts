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
