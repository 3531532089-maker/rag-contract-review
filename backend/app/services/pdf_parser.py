# PDF 解析服务
# 使用 PyMuPDF (fitz) 提取 PDF 中的文本
# 同时也支持 Word (.docx) 文件

import fitz  # PyMuPDF 的导入名
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> str:
    """
    从 PDF 文件中提取文本。

    参数:
        file_path: PDF 文件的路径

    返回:
        提取出的完整文本（保留段落结构和页码信息）

    异常:
        ValueError: 加密 PDF 或扫描件
    """
    text_parts = []

    doc = fitz.open(file_path)

    # 检测加密 PDF
    if doc.is_encrypted:
        doc.close()
        raise ValueError(
            "该 PDF 文件已加密（设有密码保护）。请先使用 Adobe Acrobat 或在线工具"
            "去除密码保护后重新上传。本系统暂不支持解析加密的 PDF。"
        )

    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"--- 第{page_num}页 ---\n{page_text}")

    doc.close()

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "PDF 文件中未检测到文本内容。可能是扫描件（图片型PDF），"
            "请使用带文字层的 PDF，或先用 OCR 工具将扫描件转为可搜索 PDF。"
        )

    return full_text


def extract_text_from_docx(file_path: str) -> str:
    """
    从 Word (.docx) 文件中提取文本。
    """
    from docx import Document

    doc = Document(file_path)
    text_parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    return "\n\n".join(text_parts)


def parse_contract_file(file_path: str) -> dict:
    """
    自动识别文件类型（PDF 或 Word），提取文本。

    返回:
        {"text": "...", "page_count": N, "file_type": "pdf"}
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        doc = fitz.open(file_path)

        # 检测加密
        if doc.is_encrypted:
            doc.close()
            raise ValueError(
                "该 PDF 文件已加密（设有密码保护）。请先去除密码保护后重新上传。"
            )

        page_count = doc.page_count
        text_parts = []
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"--- 第{page_num}页 ---\n{page_text}")
        doc.close()

        text = "\n\n".join(text_parts)
        if not text.strip():
            raise ValueError(
                "PDF 文件中未检测到文本内容。可能是扫描件（图片型PDF），"
                "请使用带文字层的 PDF。"
            )
        return {"text": text, "page_count": page_count, "file_type": "pdf"}

    elif suffix == ".docx":
        text = extract_text_from_docx(file_path)
        return {"text": text, "page_count": None, "file_type": "word"}

    else:
        raise ValueError(f"不支持的文件格式: {suffix}。请上传 PDF 或 Word(.docx) 文件。")
