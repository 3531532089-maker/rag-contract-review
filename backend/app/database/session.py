from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

# 创建数据库引擎
# 支持 SQLite（开发）和 PostgreSQL（生产），通过 .env 中的 DATABASE_URL 自动切换
_connect_args = {}
_pool_args = {}

if "sqlite" in DATABASE_URL:
    # SQLite: 允许多线程访问同一文件
    _connect_args["check_same_thread"] = False
else:
    # PostgreSQL: 使用连接池（避免每次请求都建新连接）
    _pool_args = {
        "pool_size": 10,        # 常驻连接数
        "max_overflow": 20,     # 超出后的临时连接数
        "pool_pre_ping": True,  # 每次取出连接前测试是否有效（防止闲置断开）
        "pool_recycle": 3600,   # 每小时回收连接
    }

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
    **_pool_args,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    每次请求自动创建/关闭数据库会话。

    FastAPI 依赖注入：
        @router.get("/xxx")
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
