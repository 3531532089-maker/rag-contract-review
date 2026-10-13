// 类型定义 —— 确保前后端数据结构一致

// ===== 合同列表项 =====
export interface ContractListItem {
  id: string;
  filename: string;
  contract_type: string;
  risk_score: number | null;
  char_count: number;
  created_at: string;
}

// ===== 合同列表响应（含分页） =====
export interface ContractListResponse {
  total: number;
  page: number;
  limit: number;
  contracts: ContractListItem[];
}

// ===== 合同详情 =====
export interface ContractDetail {
  id: string;
  filename: string;
  contract_type: string;
  risk_score: number | null;
  content: string;
  char_count: number;
  created_at: string;
}

// ===== 上传响应 =====
export interface UploadResponse {
  contract_id: string;
  filename: string;
  message: string;
  content_preview: string;
}

// ===== 风险条目 =====
export interface RiskItem {
  risk_level: "high" | "medium" | "low";
  clause: string;
  reason: string;
  suggestion: string;
  original_text: string;
}

// ===== 审查结果 =====
export interface ReviewResponse {
  contract_id: string;
  contract_type: string;
  risk_score: number;
  summary: string;
  risks: RiskItem[];
}

// ===== 聊天消息（UI 内部使用） =====
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

// ===== 聊天响应 =====
export interface ChatResponse {
  answer: string;
  sources: string[];
}

// ===== 聊天会话（多轮对话） =====
export interface ChatSession {
  id: string;
  contract_id: string;
  title: string | null;
  created_at: string;
  message_count: number;
}

// ===== 会话消息记录（后端返回） =====
export interface ChatMessageRecord {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[] | null;
  created_at: string;
}

// ===== 会话详情 =====
export interface SessionDetail {
  id: string;
  contract_id: string;
  title: string | null;
  created_at: string;
  messages: ChatMessageRecord[];
}

// ===== LLM 运行时设置 =====
export interface LlmSettings {
  llm_model: string;
  llm_base_url: string;
  llm_temperature: number;
  llm_max_tokens: number;
  sources: Record<string, "db" | "env">;
}

// ===== LLM 设置输入（更新 / 测试用，字段均可选） =====
export interface LlmSettingsInput {
  llm_model?: string;
  llm_base_url?: string;
  llm_temperature?: number;
  llm_max_tokens?: number;
}

// ===== LLM 测试连接结果 =====
export interface LlmTestResult {
  ok: boolean;
  elapsed_ms: number;
  reply?: string;
  error?: string;
  model: string;
}

// ===== 登录 =====
export interface LoginResponse {
  token: string;
  token_type: string;
}

// ===== 风险等级颜色映射 =====
export const RISK_COLORS: Record<string, string> = {
  high: "text-red-600 bg-red-50 border-red-200",
  medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
  low: "text-green-600 bg-green-50 border-green-200",
};

export const RISK_BADGE_ZH: Record<string, string> = {
  high: "高风险",
  medium: "中风险",
  low: "低风险",
};

export const RISK_DOT_COLORS: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};
