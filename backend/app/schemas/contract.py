# Pydantic 数据模型 —— 定义 API 的输入输出结构
# 与 models/contract.py 的区别：
#   - models/contract.py 定义数据库表结构
#   - schemas/contract.py 定义 API 请求/响应的格式

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ===== 请求模型（客户端发给服务器的数据）=====


class ReviewRequest(BaseModel):
    """请求合同审查的格式"""
    contract_id: str


# ===== 响应模型（服务器返回给客户端的数据）=====


class ContractResponse(BaseModel):
    """合同基本信息响应"""
    id: str
    filename: str
    contract_type: Optional[str] = None
    risk_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 SQLAlchemy 模型自动转换


class UploadResponse(BaseModel):
    """文件上传成功后的响应"""
    contract_id: str
    filename: str
    message: str
    content_preview: str  # 前500字预览


class RiskItem(BaseModel):
    """单条风险详情"""
    risk_level: str         # 风险等级：high / medium / low
    clause: str             # 涉及条款
    reason: str             # 风险原因
    suggestion: str         # 修改建议
    original_text: str      # 合同原文引用


class ReviewResponse(BaseModel):
    """合同审查结果响应"""
    contract_id: str
    contract_type: str
    risk_score: float       # 0-100
    summary: str            # 总体评价
    risks: list[RiskItem]   # 风险列表
