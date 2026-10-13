// 会话侧边栏 —— 某合同的会话列表 + 新建/切换/删除

"use client";

import type { ChatSession } from "@/lib/types";

interface Props {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  onDelete: (sessionId: string) => void;
}

export default function SessionSidebar({
  sessions,
  currentSessionId,
  onSelect,
  onNew,
  onDelete,
}: Props) {
  return (
    <div className="flex flex-col h-[500px] border rounded-xl bg-white">
      {/* 顶部：新建按钮 */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onNew}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 transition-colors"
        >
          ＋ 新建会话
        </button>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-400">
            还没有会话，点击上方新建
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {sessions.map((s) => (
              <li
                key={s.id}
                onClick={() => onSelect(s.id)}
                className={`group flex items-center gap-2 px-3 py-2.5 cursor-pointer transition-colors ${
                  s.id === currentSessionId ? "bg-blue-50" : "hover:bg-gray-50"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 truncate">
                    {s.title || "未命名会话"}
                  </p>
                  <p className="text-xs text-gray-400">
                    {s.message_count} 条 ·{" "}
                    {new Date(s.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(s.id);
                  }}
                  className="text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  title="删除会话"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
