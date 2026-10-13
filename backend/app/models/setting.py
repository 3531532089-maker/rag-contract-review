# 系统设置模型 —— 键值存储（用于 LLM 配置运行时切换）

from datetime import datetime, UTC
from sqlalchemy import Column, String, Text, DateTime

from app.database.session import Base


class Setting(Base):
    """系统设置表（KV）：DB 覆盖优先，缺省回落 .env"""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Setting {self.key}>"
