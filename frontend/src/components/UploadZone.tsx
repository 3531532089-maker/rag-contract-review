// 拖拽上传区域 —— 支持点击选择 + 拖拽释放

"use client";

import { useState, useRef, useCallback } from "react";
import { uploadContract } from "@/lib/api";
import type { UploadResponse } from "@/lib/types";

// 允许的 MIME 类型
const ALLOWED_MIME = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/octet-stream", // 部分浏览器对 .docx 发这个
];

// 最大文件大小（前端预检）
const MAX_SIZE = 20 * 1024 * 1024; // 20MB

interface Props {
  onUploaded: (result: UploadResponse) => void;
}

export default function UploadZone({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = useCallback(
    async (file: File) => {
      // 验证扩展名
      const name = file.name.toLowerCase();
      if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
        setError("只支持 PDF 和 Word(.docx) 文件");
        return;
      }

      // 验证 MIME 类型
      if (file.type && !ALLOWED_MIME.includes(file.type)) {
        setError(`不支持的文件类型: ${file.type}。请上传 PDF 或 Word(.docx) 文件`);
        return;
      }

      // 验证文件大小
      if (file.size > MAX_SIZE) {
        setError(`文件过大（${(file.size / 1024 / 1024).toFixed(1)}MB），最大支持 20MB`);
        return;
      }

      setUploading(true);
      setError("");
      setSuccess("");
      try {
        const result = await uploadContract(file);
        setSuccess(`"${file.name}" 上传成功！${result.message}`);
        onUploaded(result);
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail;
        setError(detail || "上传失败，请检查网络连接");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  // 拖拽事件
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) acceptFile(file);
  };

  // 点击选择
  const handleClick = () => inputRef.current?.click();
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) acceptFile(file);
    e.target.value = "";
  };

  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200
          ${dragging
            ? "border-blue-400 bg-blue-50 scale-[1.01]"
            : "border-gray-300 bg-gray-50 hover:border-blue-300 hover:bg-blue-50/30"
          }
          ${uploading ? "pointer-events-none opacity-60" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={handleFileChange}
        />

        {uploading ? (
          <div>
            <div className="inline-block w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-3" />
            <p className="text-sm text-gray-500">正在解析文件...</p>
          </div>
        ) : (
          <div>
            <span className="text-4xl mb-3 block">📤</span>
            <p className="text-sm text-gray-600 font-medium">
              点击选择文件或拖拽到此处
            </p>
            <p className="text-xs text-gray-400 mt-1">
              支持 PDF、Word(.docx) 格式，最大 20MB
            </p>
          </div>
        )}
      </div>

      {success && (
        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          {success}
        </div>
      )}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
}
