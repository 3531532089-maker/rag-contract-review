# 合同数据模型 —— 数据库表结构

import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Text, DateTime, Float, JSON, Index

from app.database.session import Base


class Contract(Base):
    """合同表"""

    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)   # SHA256 重复检测 + 索引
    contract_type = Column(String(100), nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_analysis = Column(JSON, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    is_deleted = Column(DateTime, nullable=True)  # 软删除时间戳（null=未删除）

    # 复合索引：按时间倒序列表查询
    __table_args__ = (
        Index("idx_contracts_created", "created_at"),
        Index("idx_contracts_hash", "content_hash"),
    )

    def __repr__(self):
        return f"<Contract {self.filename}>"
